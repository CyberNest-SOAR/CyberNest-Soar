import json
from datetime import datetime, timezone
import logging
from pathlib import Path

from app.config.settings import settings
from app.schemas.alert_intelligence import AlertRequest, AlertResponse
from app.client.ollama_client import LLMClient
from app.services.prompt_builder import PromptBuilder

# Setup standard logger
logger = logging.getLogger("alert_intelligence.service")

class LLMService:
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()
        self.prompt_builder = PromptBuilder()

    def map_severity(self, alert_severity: int) -> str:
        """
        Maps a Wazuh numeric severity level to standard text classifications.
        """
        if alert_severity >= 12:
            return "critical"
        elif alert_severity >= 8:
            return "high"
        elif alert_severity >= 4:
            return "medium"
        else:
            return "low"

    def process_alert(self, alert: AlertRequest) -> AlertResponse:
        """
        Routes the alert based on XGBoost confidence thresholds:
        - Confidence >= 0.85 -> Auto actionable
        - Confidence <= 0.15 -> Auto noise
        - 0.15 < Confidence < 0.85 -> Analyzed by local Ollama model
        """
        confidence = alert.noise_confidence
        verdict_source = "XGBoost"

        if confidence >= 0.85:
            response = AlertResponse(
                verdict="actionable",
                confidence=confidence,
                severity=self.map_severity(alert.alert_severity),
                reasoning=f"Automated decision: XGBoost classification confidence ({confidence:.2f}) is high (>= 0.85)."
            )
        elif confidence <= 0.15:
            response = AlertResponse(
                verdict="noise",
                confidence=1.0 - confidence,  # Express confidence in noise classification
                severity=self.map_severity(alert.alert_severity),
                reasoning=f"Automated decision: XGBoost classification confidence ({confidence:.2f}) is low (<= 0.15)."
            )
        else:
            # Route to local Ollama (DeepSeek model)
            verdict_source = "Ollama"
            prompt = self.prompt_builder.build_prompt(alert)
            response = self.llm_client.analyze_alert(prompt, alert_id=alert.alert_id)

        # Log transaction to logs/llm.log
        self._log_request(alert.alert_id, response)

        # Append structured result to output/verdicts.json
        self._save_verdict(alert, response, verdict_source)

        return response

    def _log_request(self, alert_id: str, response: AlertResponse):
        """
        Logs every request to logs/llm.log using the required JSON format.
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "alert_id": alert_id,
            "llm_verdict": response.verdict,
            "confidence": round(response.confidence, 4)
        }
        
        try:
            log_file = settings.LOG_FILE
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to logs/llm.log: {e}")

    def _save_verdict(self, alert: AlertRequest, response: AlertResponse, source: str):
        """
        Saves structured historical inputs and outputs in output/verdicts.json.
        """
        verdict_data = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "alert_id": alert.alert_id,
            "source": source,
            "input": alert.model_dump(),
            "output": response.model_dump()
        }
        
        try:
            verdicts_file = settings.OUTPUT_VERDICTS_FILE
            verdicts = []
            
            # Read existing history if any
            if verdicts_file.exists() and verdicts_file.stat().st_size > 0:
                with open(verdicts_file, "r", encoding="utf-8") as f:
                    try:
                        verdicts = json.load(f)
                    except json.JSONDecodeError:
                        verdicts = []
            
            # Append new verdict
            verdicts.append(verdict_data)
            
            # Write back
            with open(verdicts_file, "w", encoding="utf-8") as f:
                json.dump(verdicts, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update output/verdicts.json: {e}")

import os
import time
import logging
import json
import re
import requests

from app.config.settings import settings
from app.schemas.alert_intelligence import AlertResponse

# Setup standard logger
logger = logging.getLogger("alert_intelligence.client")

class LLMClient:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model_name = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT_SEC
        self.retries = settings.OLLAMA_RETRIES

    def _clean_response_text(self, text: str) -> str:
        """
        Cleans the response text by removing <think>...</think> tags and markdown code blocks.
        """
        if not text:
            return ""
        
        # Remove thinking/thought process blocks (DeepSeek-R1 outputs)
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        
        # Remove markdown code blocks (e.g. ```json ... ```)
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
        
        return cleaned

    def _parse_response_json(self, text: str) -> dict:
        """
        Safely extracts and parses JSON dictionary from cleaned text.
        """
        cleaned = self._clean_response_text(text)
        if not cleaned:
            raise ValueError("Empty response text after cleaning")

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Attempt parsing by finding the first '{' and last '}'
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start:end+1])
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to decode substring JSON: {e}")
            raise ValueError("No valid JSON structure found in response text")

    def analyze_alert(self, prompt: str, alert_id: str = None) -> AlertResponse:
        """
        Sends the prompt to the local Ollama model, enforcing a structured JSON output mapped to AlertResponse.
        Handles retries, timeouts, and raises zero exceptions to the API level (returns fallback response).
        """
        alert_id_str = alert_id if alert_id else "unknown"
        attempts = self.retries + 1
        last_error = "Unknown error"
        endpoint = f"{self.ollama_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        for attempt in range(1, attempts + 1):
            start_time = time.perf_counter()
            try:
                logger.info(
                    f"Sending request to Ollama model {self.model_name} at {endpoint} "
                    f"(Attempt {attempt}/{attempts}) for Alert ID: {alert_id_str}"
                )
                
                response = requests.post(
                    endpoint,
                    json=payload,
                    timeout=self.timeout
                )
                
                # Check HTTP status code
                response.raise_for_status()
                response_json = response.json()
                
                response_text = response_json.get("response")
                if not response_text:
                    raise ValueError("Received empty or missing 'response' field from Ollama")

                # Parse the inner JSON response
                parsed_data = self._parse_response_json(response_text)
                
                # Verify fields required by AlertResponse
                verdict = parsed_data.get("verdict", "unknown")
                confidence = float(parsed_data.get("confidence", 0.0))
                severity = parsed_data.get("severity", "unknown")
                reasoning = parsed_data.get("reasoning", "Parsed from raw response text")
                
                alert_response = AlertResponse(
                    verdict=verdict,
                    confidence=confidence,
                    severity=severity,
                    reasoning=reasoning
                )
                
                response_time = time.perf_counter() - start_time
                logger.info(
                    f"Ollama request succeeded | Model: {self.model_name} | "
                    f"Alert ID: {alert_id_str} | Status: SUCCESS | Response Time: {response_time:.4f}s"
                )
                return alert_response

            except Exception as e:
                response_time = time.perf_counter() - start_time
                last_error = str(e)
                logger.warning(
                    f"Attempt {attempt}/{attempts} failed | Model: {self.model_name} | "
                    f"Alert ID: {alert_id_str} | Status: FAILURE | Response Time: {response_time:.4f}s | "
                    f"Error: {last_error}"
                )
                
                # Sleep/retry with exponential backoff if not the last attempt
                if attempt < attempts:
                    sleep_time = 2 ** attempt
                    logger.info(f"Sleeping for {sleep_time} seconds before retrying...")
                    time.sleep(sleep_time)

        logger.error(
            f"All {attempts} attempts to communicate with Ollama failed for Alert ID: {alert_id_str}. "
            f"Last error: {last_error}"
        )
        return self.get_fallback_response(f"LLM unavailable: {last_error}")

    def get_fallback_response(self, error_message: str) -> AlertResponse:
        """
        Generates the standard fallback AlertResponse requested by the specification.
        """
        return AlertResponse(
            verdict="unknown",
            confidence=0.0,
            severity="unknown",
            reasoning=error_message
        )

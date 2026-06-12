import os

from app.config.settings import settings
from app.schemas.alert_intelligence import AlertRequest

class PromptBuilder:
    @staticmethod
    def build_prompt(alert: AlertRequest) -> str:
        """
        Reads the SOC Analyst prompt template and interpolates alert fields.
        """
        prompt_path = settings.PROMPT_TEMPLATE_FILE
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template file not found at: {prompt_path}")
            
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
            
        # Format the prompt using fields from the AlertRequest
        return template.format(
            alert_id=alert.alert_id,
            alert_severity=alert.alert_severity,
            enrichment_vt_score=alert.enrichment_vt_score,
            enrichment_abuse_score=alert.enrichment_abuse_score,
            asset_criticality=alert.asset_criticality,
            similar_alerts_last_hour=alert.similar_alerts_last_hour,
            maintenance_window=alert.maintenance_window,
            known_admin_activity=alert.known_admin_activity,
            noise_confidence=alert.noise_confidence
        )

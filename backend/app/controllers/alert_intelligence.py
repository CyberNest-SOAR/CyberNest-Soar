"""Controller for the Alert Intelligence Service."""

import logging
from fastapi import APIRouter, status
from app.schemas.alert_intelligence import AlertRequest, AlertResponse
from app.services.alert_intelligence_service import LLMService

log = logging.getLogger(__name__)
router = APIRouter(tags=["Alert Intelligence"])

# Instantiate the service
service = LLMService()

@router.post("/analyze", response_model=AlertResponse, status_code=status.HTTP_200_OK)
def analyze_endpoint(alert: AlertRequest):
    """
    Analyzes normalized and enriched Wazuh alerts:
    - Route to auto-actionable if confidence >= 0.85
    - Route to auto-noise if confidence <= 0.15
    - Delegate to DeepSeek-R1 via Ollama for intermediate confidence values
    """
    try:
        log.info(f"Received alert analysis request for Alert ID: {alert.alert_id}")
        response = service.process_alert(alert)
        return response
    except Exception as e:
        log.error(f"Critical service error while processing Alert ID {alert.alert_id}: {e}", exc_info=True)
        # Guarantees that the endpoint never crashes and always returns the required Pydantic-compliant fallback structure
        return AlertResponse(
            verdict="unknown",
            confidence=0.0,
            severity="unknown",
            reasoning=f"Internal service error: {str(e)}"
        )

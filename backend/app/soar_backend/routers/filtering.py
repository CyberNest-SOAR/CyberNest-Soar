import sys
from pathlib import Path
from fastapi import APIRouter
from schemas.models import FilterRequest, FilterResult, UnifiedAlert
from typing import List

_WORKSPACE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_DIR))

from ai.inference.predict_noise import predict_noise

router = APIRouter(prefix="/alerts", tags=["Team 3: Log Filtering & Noise Reduction"])


def classify_alert_single(alert: UnifiedAlert) -> dict:
    # predict_noise is robust to receive UnifiedAlert or dict
    result = predict_noise(alert)
    label = "important" if result["prediction"] == "Actionable" else "noise"
    return {
        "classification": label,
        "confidence": result["confidence"],
    }


@router.post("/filter", response_model=List[FilterResult])
async def classify_alerts(request: FilterRequest):
    results = []
    for alert in request.alerts:
        result = predict_noise(alert)
        label = "important" if result["prediction"] == "Actionable" else "noise"
        results.append(FilterResult(
            alert_id=alert.event_id,
            classification=label,
            confidence=result["confidence"],
            summary=f"ML classified as {label} ({result['confidence']:.1%})"
        ))
    return results


@router.post("/predict-noise")
async def predict_noise_endpoint(alert: dict):
    """Predict noise for a given raw alert or feature dict."""
    return predict_noise(alert)


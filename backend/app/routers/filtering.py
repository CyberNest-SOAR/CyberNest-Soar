import sys
import importlib.util
from pathlib import Path
from fastapi import APIRouter
from app.schemas.models import FilterRequest, FilterResult, UnifiedAlert
from typing import List
CURRENT_DIR = Path(__file__).resolve().parent


if CURRENT_DIR.parents[1].name == "app":
    # Inside Docker: /app/routers -> parent is /app -> ai is right next to it
    _PREDICT_NOISE_PATH = CURRENT_DIR.parent / "ai" / "inference" / "predict_noise_v2.py"
else:
    # On Local Windows: Go up to the repository root and look down the standard tree
    _WORKSPACE_DIR = CURRENT_DIR.parent.parent.parent
    _PREDICT_NOISE_PATH = _WORKSPACE_DIR / "backend" / "app" / "ai" / "inference" / "predict_noise_v2.py"

spec = importlib.util.spec_from_file_location("predict_noise_module", str(_PREDICT_NOISE_PATH))
predict_noise_module = importlib.util.module_from_spec(spec)
sys.modules["predict_noise_module"] = predict_noise_module
spec.loader.exec_module(predict_noise_module)

predict_noise = predict_noise_module.predict_noise

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


# Internal helper to demonstrate how your raw data is merged for the LLM
def prepare_llm_payload(alert: UnifiedAlert) -> dict:
    """
    Merges the three raw data sources into the structured POST format 
    required for the classification engine.
    """
    # 1. Base Alert (rule_id, severity, etc.)
    rule_id = alert.raw_data.get("rule", {}).get("id", "unknown") if "rule" in alert.raw_data else alert.raw_data.get("rule_id", "unknown")
    severity = alert.severity
    description = alert.description
    
    # 2. Statistics (event_count_5m, unique_ips, etc.)
    # We simulate statistics extraction from raw_data if not explicitly populated
    stats = alert.raw_data.get("stats", {})
    event_count_5m = stats.get("event_count_5m", 1)
    unique_ips = stats.get("unique_ips", 1)
    
    # 3. Context (asset_criticality, ip_reputation)
    asset_criticality = alert.raw_data.get("context", {}).get("asset_criticality", "low")
    ip_reputation = (alert.enrichment_data.virus_total or {}).get("score", 100)
    
    return {
        "rule_id": rule_id,
        "severity": severity,
        "description": description,
        "event_count_5m": event_count_5m,
        "unique_ips": unique_ips,
        "ip_reputation": ip_reputation,
        "asset_criticality": asset_criticality,
        "label": None  # To be filled by the LLM
    }

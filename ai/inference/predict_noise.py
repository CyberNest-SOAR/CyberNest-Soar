"""Inference wrapper for the SOC noise classifier.

Loads a persisted XGBoost classifier trained to distinguish
actionable security alerts from noise.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any

import joblib
import pandas as pd

log = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "noise_classifier.pkl"

FEATURE_NAMES = [
    "alert_severity",
    "enrichment_vt_score",
    "enrichment_abuse_score",
    "similar_alerts_last_hour",
    "historical_false_positive_rate",
    "asset_value",
    "business_hours",
    "mfa_used",
    "signed_binary",
    "suppression_hit",
]

# Load model once at startup
if MODEL_PATH.exists():
    try:
        model = joblib.load(MODEL_PATH)
        log.info("Loaded noise classifier model from %s", MODEL_PATH)
    except Exception as e:
        log.exception("Failed to load noise classifier model from %s: %s", MODEL_PATH, e)
        model = None
else:
    log.warning("Noise classifier model not found at %s", MODEL_PATH)
    model = None


def predict_noise(alert: Any) -> Dict[str, Any]:
    """
    Predict whether an incoming alert is Noise or Actionable.
    
    Accepts:
        - A dictionary of direct feature keys.
        - A raw alert dictionary or Pydantic model (which is converted).
    
    Returns:
        Dict containing:
            "prediction": "Noise" | "Actionable"
            "confidence": float (probability of the predicted class)
    """
    if model is None:
        # If model is not loaded, fail soft or default to Actionable
        log.error("Noise classifier model is not loaded; defaulting alert to Actionable.")
        return {
            "prediction": "Actionable",
            "confidence": 1.0,
        }

    # Convert Pydantic models to dict
    if hasattr(alert, "model_dump"):
        alert_dict = alert.model_dump()
    elif hasattr(alert, "dict"):
        alert_dict = alert.dict()
    elif isinstance(alert, dict):
        alert_dict = alert
    else:
        alert_dict = {}

    # Extract features with robust fallbacks and safe defaults
    features = {}

    # 1. alert_severity
    features["alert_severity"] = alert_dict.get("alert_severity")
    if features["alert_severity"] is None:
        features["alert_severity"] = alert_dict.get("severity", 0)

    # 2. enrichment_vt_score
    features["enrichment_vt_score"] = alert_dict.get("enrichment_vt_score")
    if features["enrichment_vt_score"] is None:
        features["enrichment_vt_score"] = (
            (alert_dict.get("enrichment_data") or {}).get("virus_total", {}).get("score", 0)
        )

    # 3. enrichment_abuse_score
    features["enrichment_abuse_score"] = alert_dict.get("enrichment_abuse_score")
    if features["enrichment_abuse_score"] is None:
        features["enrichment_abuse_score"] = (
            (alert_dict.get("enrichment_data") or {}).get("abuse_ipdb", {}).get("score", 0)
        )

    # 4. similar_alerts_last_hour
    features["similar_alerts_last_hour"] = alert_dict.get("similar_alerts_last_hour")
    if features["similar_alerts_last_hour"] is None:
        features["similar_alerts_last_hour"] = alert_dict.get("event_count_5m", 0)

    # 5. historical_false_positive_rate
    features["historical_false_positive_rate"] = alert_dict.get("historical_false_positive_rate")
    if features["historical_false_positive_rate"] is None:
        features["historical_false_positive_rate"] = 0.0

    # 6. asset_value
    features["asset_value"] = alert_dict.get("asset_value")
    if features["asset_value"] is None:
        risk_score = (alert_dict.get("enrichment_data") or {}).get("risk_score", 0)
        features["asset_value"] = 1 if risk_score > 50 else 0

    # Helper function to convert values to binary int safely
    def to_binary_int(val: Any) -> int:
        if val is None:
            return 0
        if isinstance(val, str):
            return 1 if val.lower() in ("true", "1", "yes") else 0
        return 1 if bool(val) else 0

    # 7. business_hours
    features["business_hours"] = to_binary_int(alert_dict.get("business_hours", 0))

    # 8. mfa_used
    features["mfa_used"] = alert_dict.get("mfa_used")
    if features["mfa_used"] is None:
        features["mfa_used"] = (alert_dict.get("raw_data") or {}).get("mfa_used", 0)
    features["mfa_used"] = to_binary_int(features["mfa_used"])

    # 9. signed_binary
    features["signed_binary"] = alert_dict.get("signed_binary")
    if features["signed_binary"] is None:
        features["signed_binary"] = (alert_dict.get("raw_data") or {}).get("signed_binary", 0)
    features["signed_binary"] = to_binary_int(features["signed_binary"])

    # 10. suppression_hit
    features["suppression_hit"] = alert_dict.get("suppression_hit")
    if features["suppression_hit"] is None:
        features["suppression_hit"] = (alert_dict.get("raw_data") or {}).get("suppression_hit", 0)
    features["suppression_hit"] = to_binary_int(features["suppression_hit"])

    # Build pandas DataFrame for inference
    row = {f: features[f] for f in FEATURE_NAMES}
    df = pd.DataFrame([row])

    # Predict probability
    try:
        proba = model.predict_proba(df)[0]
        # proba[1] is probability of class Actionable, proba[0] is Noise.
        # Threshold is 0.50. If proba[1] >= 0.50, then predict "Actionable", else "Noise"
        pred = 1 if proba[1] >= 0.50 else 0
        confidence = float(proba[pred])
    except Exception as e:
        log.error("Model prediction failed: %s. Defaulting to Actionable.", e)
        return {
            "prediction": "Actionable",
            "confidence": 1.0,
        }

    return {
        "prediction": "Actionable" if pred == 1 else "Noise",
        "confidence": round(confidence, 4),
    }


if __name__ == "__main__":
    test_alert = {
        "alert_severity": 15,
        "enrichment_vt_score": 90,
        "enrichment_abuse_score": 80,
        "similar_alerts_last_hour": 120,
        "historical_false_positive_rate": 0.01,
        "asset_value": 90,
        "business_hours": 1,
        "mfa_used": 0,
        "signed_binary": 1,
        "suppression_hit": 0,
    }
    print("Testing with mock alert:")
    print(predict_noise(test_alert))

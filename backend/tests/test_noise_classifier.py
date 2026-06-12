import sys
from pathlib import Path

_WORKSPACE_DIR = Path(__file__).resolve().parent.parent.parent
if str(_WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_DIR))

from backend.app.ai.inference.predict_noise_v2 import predict_noise


def test_noise_classifier_actionable():
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
    result = predict_noise(test_alert)
    assert result["prediction"] == "Actionable"
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0


def test_noise_classifier_noise():
    test_alert = {
        "alert_severity": 1,
        "enrichment_vt_score": 0,
        "enrichment_abuse_score": 0,
        "similar_alerts_last_hour": 1,
        "historical_false_positive_rate": 0.95,
        "asset_value": 0,
        "business_hours": 0,
        "mfa_used": 1,
        "signed_binary": 1,
        "suppression_hit": 1,
    }
    result = predict_noise(test_alert)
    assert result["prediction"] == "Noise"
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0


def test_noise_classifier_defaults():
    # Test safe defaulting for empty alerts
    result = predict_noise({})
    assert result["prediction"] in ("Actionable", "Noise")
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0

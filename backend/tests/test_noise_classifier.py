import sys
from pathlib import Path

_WORKSPACE_DIR = Path(__file__).resolve().parent.parent.parent
if str(_WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_DIR))

from backend.app.ai.inference.predict_noise_v2 import predict_noise
import backend.app.ai.inference.predict_noise_v2 as predict_noise_v2
from unittest.mock import MagicMock

# Mock the model behavior for testing purposes
mock_model = MagicMock()
def mock_predict_proba(df):
    severity = df["alert_severity"].iloc[0] if "alert_severity" in df.columns else 1
    # Higher severity / vt score leads to actionable
    if severity > 5:
        return [[0.1, 0.9]]
    else:
        return [[0.9, 0.1]]

mock_model.predict_proba = mock_predict_proba
predict_noise_v2.model = mock_model
predict_noise_v2.features = [
    "enrichment_vt_score",
    "enrichment_abuse_score",
    "alert_severity",
    "asset_value",
    "bytes_sent",
    "bytes_received",
    "duration",
    "dst_port",
    "similar_alerts_last_hour",
    "repeated_behavior_score",
    "business_hours",
    "weekend_activity",
    "maintenance_window",
    "patch_window",
    "known_admin_activity",
    "vulnerability_scan",
    "scheduled_backup",
    "mfa_used",
    "signed_binary",
    "historically_seen",
    "recurring_alert"
]
predict_noise_v2.threshold = 0.5



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

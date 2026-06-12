"""Basic smoke tests for the phishing detector."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.ai.inference.phishing_model import PhishingDetector


def _build_detector() -> PhishingDetector:
    detector = PhishingDetector(
        model_path=Path("/tmp/nonexistent_model.joblib"),
        vectorizer_path=Path("/tmp/nonexistent_vectorizer.joblib"),
    )
    
    # Mock SklearnDetector to simulate a ready model
    detector.sklearn_detector.is_ready = MagicMock(return_value=True)
    
    def mock_analyse(subject: str, body: str):
        combined = f"{subject} {body}".lower()
        is_suspicious = "urgent" in combined or "prize" in combined
        label = "suspicious" if is_suspicious else "safe"
        return {
            "engine": "ml",
            "probability": 0.9 if is_suspicious else 0.1,
            "spelling_score": 0.0,
            "keyword_score": 0.8 if is_suspicious else 0.0,
            "composite_score": 0.9 if is_suspicious else 0.1,
            "model_label": label,
            "enrichment": {},
            "feedback_question": "Feedback?",
        }
        
    detector.sklearn_detector.analyse = MagicMock(side_effect=mock_analyse)
    return detector


def test_suspicious_email_flagged():
    detector = _build_detector()
    result = detector.analyse("Urgent: Verify your account", "Click here to claim your prize")

    assert result["model_label"] == "suspicious"
    assert result["composite_score"] >= 0


def test_calm_email_marked_safe():
    detector = _build_detector()
    result = detector.analyse("Weekly meeting", "Looking forward to our sync tomorrow.")

    assert result["model_label"] == "safe"

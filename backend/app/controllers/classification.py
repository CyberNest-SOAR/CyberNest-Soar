"""AI classification endpoints for phishing detection."""

from __future__ import annotations

import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query

from ..models.email_models import EmailAnalysis, EmailPayload, EmailRecord, FeedbackPayload
from ..services.email_service import EmailService
from ..ai.phishing_model import get_detector, PhishingDetector

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["classification"])

ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "phishing_model.joblib"
VECTORIZER_PATH = ARTIFACTS_DIR / "tfidf_vectorizer.joblib"

# Attempt to create a shared detector but do NOT raise during import-time failures.
# Import-time exceptions can prevent the FastAPI app from starting; instead keep
# `detector_instance` as `None` and let request-time dependency handling raise
# a clear HTTP error when a request tries to use the detector.
try:
    detector_instance = get_detector(
        model_path=str(MODEL_PATH),
        vectorizer_path=str(VECTORIZER_PATH),
    )

    if detector_instance.is_ml_ready():
        log.info(
            "Phishing ML detector loaded successfully",
        )
    else:
        log.warning(
            "Phishing ML detector artifacts not ready — falling back to heuristic at runtime",
        )

except Exception as e:
    log.critical(f"Failed to initialize the phishing ML model at import time: {e}")
    detector_instance = None


def get_detector_dependency() -> PhishingDetector:
    if detector_instance is None:
        log.error("Detector instance is not available for requests; ML unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Phishing Detector is not initialized or ML artifacts are missing.",
        )
    return detector_instance


def get_email_service(request: Request) -> EmailService:
    """Dependency to get the email service from app state."""
    service: EmailService = request.app.state.email_service
    return service

@router.get("/classifications", response_model=list[EmailRecord])
def list_emails(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: EmailService = Depends(get_email_service),
) -> list[EmailRecord]:
    return service.list_emails(limit=limit, offset=offset)


@router.get("/classify/{gmail_id}", response_model=EmailAnalysis, status_code=status.HTTP_200_OK)
def classify_email_by_id(
    gmail_id: str,
    service: EmailService = Depends(get_email_service),
) -> EmailAnalysis:
    log.info(f"Classifying email with Gmail ID: {gmail_id}...")
    """
    Classify an email by its Gmail ID.
    
    Re-analyzes the specified email using the phishing detection model
    and returns the classification results. The email must exist in the
    database (either from a previous sync or manual submission).
    """

    try:
        analysis = service.classify_email_by_id(gmail_id)
        return analysis
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

@router.post(
    "/classify-payload", 
    response_model=EmailAnalysis,
    summary="Classify a new, direct email payload"
)
def classify_direct_payload(
    request: EmailPayload,
    detector: PhishingDetector = Depends(get_detector_dependency)
):
    log.info(f"Received direct classification request for sender: {request.sender}...")
    result = detector.analyse(request.subject, request.body)
    log.info(f"Analysis result: {result['model_label']} (Score: {result['composite_score']})")
    return result


@router.post("/classify/{gmail_id}/feedback", status_code=status.HTTP_200_OK)
def submit_feedback(
    gmail_id: str,
    payload: FeedbackPayload,
    service: EmailService = Depends(get_email_service),
):
    """Capture user feedback: True if model classification was correct, False if wrong."""

    try:
        service.submit_feedback(gmail_id=gmail_id, is_correct=payload.is_correct)
        return {
            "status": "ok", 
            "gmail_id": gmail_id, 
            "is_correct": payload.is_correct,
            "message": "Feedback captured successfully"
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:  # pragma: no cover - safety net
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    
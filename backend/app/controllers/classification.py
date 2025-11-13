"""AI classification endpoints for phishing detection."""

from __future__ import annotations

import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query

from backend.app.models.email_models import EmailAnalysis, EmailPayload, EmailRecord
from backend.app.services.email_service import EmailService
from backend.app.ai.phishing_model import get_detector, PhishingDetector

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["classification"])

# =======================================================================
# AI MODEL LOADING
# =======================================================================

ARTIFACTS_DIR = Path("artifacts")
MODEL_PATH = ARTIFACTS_DIR / "phishing_model.joblib"
VECTORIZER_PATH = ARTIFACTS_DIR / "tfidf_vectorizer.joblib"

try:
    detector_instance = get_detector(
        model_path=str(MODEL_PATH),
        vectorizer_path=str(VECTORIZER_PATH)
    )
    log.info(f"Phishing detector loaded successfully from {ARTIFACTS_DIR.resolve()}")
    if not detector_instance.is_ml_ready():
        log.warning("ML model is NOT ready. Falling back to Heuristics.")
except Exception as e:
    log.error(f"Failed to load the phishing model: {e}")
    detector_instance = None

def get_detector_dependency() -> PhishingDetector:
    if detector_instance is None:
        log.error("Detector instance is not available!")
        raise RuntimeError("AI Phishing Detector is not initialized.")
    return detector_instance

# =======================================================================
# EXISTING ENDPOINTS
# =======================================================================

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

# =======================================================================
# NEW ENDPOINT (For AI Task)
# =======================================================================

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
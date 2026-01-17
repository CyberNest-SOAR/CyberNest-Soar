"""FastAPI routes for the SOAR phishing detection API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..models.email_models import (
    EmailCreateResponse,
    EmailPayload,
    EmailRecord,
    EmailSyncResponse,
    FeedbackPayload,
)
from ..services.email_service import EmailService


router = APIRouter(prefix="/api/emails", tags=["emails"])



def get_email_service(request: Request) -> EmailService:
    service: EmailService = request.app.state.email_service
    return service


@router.post("/emails/sync", response_model=EmailSyncResponse)
def sync_gmail(
    max_results: int | None = Query(None, ge=1, le=500),
    service: EmailService = Depends(get_email_service),
) -> EmailSyncResponse:
    """Pull the latest emails from Gmail and analyse each message."""

    return service.sync_with_gmail(max_results=max_results)

@router.post("/emails", response_model=EmailCreateResponse, status_code=status.HTTP_201_CREATED)
def submit_email(
    payload: EmailPayload,
    service: EmailService = Depends(get_email_service),
) -> EmailCreateResponse:
    """Accept an email payload, analyse it, and persist the result."""

    return service.create_manual_email(payload)


@router.get("/emails", response_model=list[EmailRecord])
def list_emails(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: EmailService = Depends(get_email_service),
) -> list[EmailRecord]:
    return service.list_emails(limit=limit, offset=offset)


@router.get("/emails/{gmail_id}", response_model=EmailRecord)
def get_email(
    gmail_id: str,
    service: EmailService = Depends(get_email_service),
) -> EmailRecord:
    record = service.get_email(gmail_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    return record


@router.post("/emails/{gmail_id}/feedback", status_code=status.HTTP_200_OK)
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
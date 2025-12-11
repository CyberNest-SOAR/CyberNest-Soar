"""Business logic around email ingestion and analysis.

This service coordinates Gmail access, phishing analysis, and persistence.
It logs important lifecycle events and analysis results to help operators
understand what the backend is doing during syncs or manual submissions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from uuid import uuid4
import logging

from ..ai.phishing_model import get_detector
from ..services.enrichment_service import enrichment_features
from ..client.gmail_api import (
    get_email_message_details,
    get_email_messages,
    init_gmail_service,
)
from ..config.settings import Settings
from ..models.email_models import (
    EmailAnalysis,
    EmailCreateResponse,
    EmailPayload,
    EmailRecord,
    EmailSyncResponse,
)
from ..repository.gmail_db import EmailRepository
from ..repository.feedback_repo import save_feedback

log = logging.getLogger(__name__)


class EmailService:
    """Coordinate Gmail access, phishing analysis, and persistence."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.repository = EmailRepository(settings.database_url)
        self.detector = get_detector(
            str(settings.model_artifact_path),
            str(settings.vectorizer_artifact_path),
        )
        log.info("EmailService initialized; model=%s vectorizer=%s",
                 settings.model_artifact_path, settings.vectorizer_artifact_path)
        self.repository.init_schema()

    def _analyse(self, subject: str | None, body: str | None) -> EmailAnalysis:
        subject = subject or ""
        body = body or ""
        try:
            analysis_payload = self.detector.analyse(subject, body)
            log.debug("Analysis payload: %s", analysis_payload)
            return EmailAnalysis(**analysis_payload)
        except Exception as e:
            log.exception("Analysis failed for subject=%s: %s", subject, e)
            raise

    def create_manual_email(self, payload: EmailPayload) -> EmailCreateResponse:
        gmail_id = f"manual-{uuid4().hex}"
        analysis = self._analyse(payload.subject, payload.body)

        log.info("Creating manual email record %s (sender=%s) with label=%s",
                 gmail_id, payload.sender, analysis.model_dump().get("model_label"))

        record_id = self.repository.upsert_email(
            gmail_id=gmail_id,
            subject=payload.subject,
            sender=payload.sender,
            recipients=payload.recipients,
            snippet=payload.body[:140],
            body=payload.body,
            has_attachments=bool(payload.attachments),
            date=datetime.now(timezone.utc),
            is_starred=False,
            labels=["MANUAL"],
            analysis=analysis.model_dump(exclude_none=True),
        )

        return EmailCreateResponse(
            record_id=record_id,
            gmail_id=gmail_id,
            analysis=analysis,
        )

    def list_emails(self, limit: int = 50, offset: int = 0) -> List[EmailRecord]:
        records = self.repository.list_emails(limit=limit, offset=offset)
        return [EmailRecord(**record) for record in records]

    def get_email(self, gmail_id: str) -> EmailRecord | None:
        record = self.repository.get_email(gmail_id)
        return EmailRecord(**record) if record else None

    def sync_with_gmail(self, max_results: int | None = None) -> EmailSyncResponse:
        client_file = self.settings.google_client_secret_file
        service = init_gmail_service(
            client_file,
            token_dir=self.settings.token_directory,
        )

        target = max_results or self.settings.gmail_max_results
        messages = get_email_messages(
            service,
            max_results=target,
            folder_name=self.settings.gmail_sync_folder,
        )

        analysed = 0

        log.info("Starting Gmail sync (target=%s) for folder=%s", target, self.settings.gmail_sync_folder)

        for message in messages:
            details = get_email_message_details(service, message["id"])
            if not details:
                continue

            try:
                analysis = self._analyse(details.get("subject"), details.get("body"))
            except Exception:
                # Continue processing other messages even if analysis fails for one
                log.exception("Skipping message %s due to analysis failure", message["id"])
                continue

            self.repository.upsert_email(
                gmail_id=details["gmail_id"],
                subject=details.get("subject"),
                sender=details.get("sender"),
                recipients=details.get("recipients", []),
                snippet=details.get("snippet"),
                body=details.get("body"),
                has_attachments=details.get("has_attachments", False),
                date=details.get("parsed_date"),
                is_starred=details.get("star", False),
                labels=details.get("labels", []),
                analysis=analysis.model_dump(exclude_none=True),
            )

            analysed += 1
            if analysed % 50 == 0 and analysed > 0:
                log.info("Processed %d messages so far", analysed)

        return EmailSyncResponse(
            synced=len(messages),
            analysed=analysed,
            folder=self.settings.gmail_sync_folder,
        )

    def get_most_recent_email(self) -> EmailRecord | None:
        """Fetch the most recently received email from Gmail."""
        client_file = self.settings.google_client_secret_file
        service = init_gmail_service(
            client_file,
            token_dir=self.settings.token_directory,
        )

        messages = get_email_messages(
            service,
            max_results=1,
            folder_name=self.settings.gmail_sync_folder,
        )

        if not messages:
            return None

        details = get_email_message_details(service, messages[0]["id"])
        if not details:
            return None

        # Check if email already exists in database
        existing = self.repository.get_email(details["gmail_id"])
        if existing:
            return EmailRecord(**existing)

        # If not in database, create a record
        analysis = self._analyse(details.get("subject"), details.get("body"))

        record_id = self.repository.upsert_email(
            gmail_id=details["gmail_id"],
            subject=details.get("subject"),
            sender=details.get("sender"),
            recipients=details.get("recipients", []),
            snippet=details.get("snippet"),
            body=details.get("body"),
            has_attachments=details.get("has_attachments", False),
            date=details.get("parsed_date"),
            is_starred=details.get("star", False),
            labels=details.get("labels", []),
            analysis=analysis.model_dump(exclude_none=True),
        )

        # Fetch the newly created record
        record = self.repository.get_email(details["gmail_id"])
        return EmailRecord(**record) if record else None

    def classify_email_by_id(self, gmail_id: str) -> EmailAnalysis:
        """Classify an email by its Gmail ID, re-analyzing if needed."""
        record = self.repository.get_email(gmail_id)
        if not record:
            raise ValueError(f"Email with ID {gmail_id} not found")

        # Re-analyze the email
        subject = record.get("subject") or ""
        body = record.get("body") or ""
        analysis = self._analyse(subject, body)
        log.info("Re-classified email %s -> %s", gmail_id, analysis.model_dump().get("model_label"))

        # Ensure recipients is a list
        recipients = record.get("recipients", [])
        if isinstance(recipients, str):
            recipients = [r.strip() for r in recipients.split(",") if r.strip()]

        # Update the record with new analysis
        self.repository.upsert_email(
            gmail_id=record["gmail_id"],
            subject=record.get("subject"),
            sender=record.get("sender"),
            recipients=recipients,
            snippet=record.get("snippet"),
            body=record.get("body"),
            has_attachments=record.get("has_attachments", False),
            date=record.get("date"),
            is_starred=record.get("is_starred", False),
            labels=record.get("labels", []),
            analysis=analysis.model_dump(exclude_none=True),
        )

        return analysis

    def submit_feedback(self, gmail_id: str, user_label: str) -> None:
        """Capture user feedback for an analysed email and persist enrichment."""
        record = self.repository.get_email(gmail_id)
        if not record:
            raise ValueError(f"Email with ID {gmail_id} not found")

        # Prefer stored enrichment; recompute if missing
        analysis_data = record.get("analysis") or {}
        enrichment = analysis_data.get("enrichment")
        if not enrichment:
            subject = record.get("subject") or ""
            body = record.get("body") or ""
            enrichment = enrichment_features(subject, body)

        save_feedback(
            case_id=gmail_id,
            subject=record.get("subject", ""),
            body=record.get("body", ""),
            user_label=user_label,
            enrichment=enrichment,
        )

        log.info("Captured feedback for gmail_id=%s label=%s", gmail_id, user_label)

    def close(self) -> None:
        self.repository.close()



import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/phishing", tags=["Phishing Emails"])

PHISHING_DB_PATH = Path(__file__).resolve().parent.parent / "phishing_db.json"

def _load_db():
    if PHISHING_DB_PATH.exists():
        with open(PHISHING_DB_PATH) as f:
            return json.load(f)
    return []

def _save_db(data):
    PHISHING_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PHISHING_DB_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)

@router.get("/emails")
async def list_phishing_emails(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filter by status: safe, suspicious, phishing"),
):
    db = _load_db()
    if status:
        db = [e for e in db if e.get("classification", "").lower() == status.lower()]
    total = len(db)
    page = db[offset:offset + limit]
    return {"total": total, "offset": offset, "limit": limit, "emails": page}

@router.get("/emails/{email_id}")
async def get_phishing_email(email_id: str):
    db = _load_db()
    for email in db:
        if email.get("id") == email_id:
            return email
    raise HTTPException(status_code=404, detail="Email not found")

@router.post("/emails")
async def submit_phishing_email(
    sender: str,
    subject: str,
    body: str,
    recipient: Optional[str] = None,
):
    db = _load_db()
    import hashlib, uuid
    email_id = str(uuid.uuid4())
    entry = {
        "id": email_id,
        "sender": sender,
        "subject": subject,
        "body_preview": body[:500],
        "recipient": recipient,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "classification": "pending",
        "analysis": {},
    }
    db.append(entry)
    _save_db(db)
    return {"message": "Email submitted", "email_id": email_id}

@router.get("/stats")
async def phishing_stats():
    db = _load_db()
    total = len(db)
    classified = {"safe": 0, "suspicious": 0, "phishing": 0, "pending": 0}
    for email in db:
        cls = email.get("classification", "pending").lower()
        if cls in classified:
            classified[cls] += 1
        else:
            classified["pending"] += 1
    return {
        "total_emails": total,
        "classified": classified,
        "latest_scan": datetime.now(timezone.utc).isoformat(),
    }

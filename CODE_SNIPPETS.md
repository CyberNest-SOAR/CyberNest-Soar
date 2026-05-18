# CyberNest-SOAR Code Snippets

Essential code snippets from the codebase demonstrating key project ideas.

---

## 1. FastAPI Application Initialization

**File**: [backend/main.py](backend/main.py)

Application entrypoint with lifecycle management and router registration:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.email_service import EmailService

@asynccontextmanager
async def lifespan(app: FastAPI):
    email_service = EmailService(settings)
    app.state.settings = settings
    app.state.email_service = email_service
    try:
        yield
    finally:
        email_service.close()

app = FastAPI(
    title="SOAR Phishing Detection API",
    version="1.0.0",
    description="Essential endpoints for ingesting, analysing, and retrieving email data.",
    lifespan=lifespan,
)
```

**Key Idea**: FastAPI lifespan manager initializes the email service once and keeps it available throughout app lifecycle.

---

## 2. Pydantic Data Models for Request/Response Validation

**File**: [backend/app/models/email_models.py](backend/app/models/email_models.py)

Type-safe request and response structures:

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any

class EmailPayload(BaseModel):
    sender: EmailStr
    recipients: List[EmailStr] = Field(default_factory=list)
    subject: str = Field(..., max_length=512)
    body: str = Field(..., min_length=1)
    attachments: List[str] = Field(default_factory=list)

class EmailAnalysis(BaseModel):
    engine: str = Field(default="heuristic")
    probability: Optional[float] = None
    composite_score: float
    model_label: str
    case_id: Optional[str] = None
    feedback_question: Optional[str] = Field(
        default="Is this classification correct? Please provide feedback."
    )
```

**Key Idea**: Pydantic ensures all incoming requests and outgoing responses conform to strict schemas.

---

## 3. Configuration Management with Environment Variables

**File**: [backend/app/config/settings.py](backend/app/config/settings.py)

Centralized configuration loaded from `.env` file:

```python
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/soar_db",
        description="PostgreSQL connection URL",
    )
    model_artifact_path: Path = Field(
        default=_default_artifacts / "phishing_model.joblib",
        description="Location of phishing ML model artifact",
    )
    vectorizer_artifact_path: Path = Field(
        default=_default_artifacts / "tfidf_vectorizer.joblib",
        description="Location of persisted TF-IDF vectorizer",
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
```

**Key Idea**: All configuration is externalized and type-checked at startup.

---

## 4. FastAPI Route Handlers with Dependency Injection

**File**: [backend/app/controllers/emails.py](backend/app/controllers/emails.py)

REST endpoints using FastAPI's dependency injection pattern:

```python
from fastapi import APIRouter, Depends, Query, Request
from app.services.email_service import EmailService

router = APIRouter(prefix="/api", tags=["emails"])

def get_email_service(request: Request) -> EmailService:
    return request.app.state.email_service

@router.post("/emails", response_model=EmailCreateResponse, status_code=201)
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
```

**Key Idea**: Dependency injection ensures service is available across routes with automatic validation of query parameters.

---

## 5. Business Logic Layer - Email Service Orchestration

**File**: [backend/app/services/email_service.py](backend/app/services/email_service.py)

Service layer that coordinates multiple operations:

```python
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

    def _analyse(self, subject: str | None, body: str | None) -> EmailAnalysis:
        subject = subject or ""
        body = body or ""
        try:
            analysis_payload = self.detector.analyse(subject, body)
            return EmailAnalysis(**analysis_payload)
        except Exception as e:
            log.exception("Analysis failed for subject=%s: %s", subject, e)
            raise

    def create_manual_email(self, payload: EmailPayload) -> EmailCreateResponse:
        gmail_id = f"manual-{uuid4().hex}"
        analysis = self._analyse(payload.subject, payload.body)
        analysis.case_id = gmail_id

        log.info("Creating manual email record %s (sender=%s) with label=%s",
                 gmail_id, payload.sender, analysis.model_label)

        record_id = self.repository.upsert_email(
            gmail_id=gmail_id,
            subject=payload.subject,
            sender=payload.sender,
            # ... other fields
        )
```

**Key Idea**: Service layer decouples API layer from database and ML model, orchestrating complex workflows.

---

## 6. ML Model Loading and Inference

**File**: [backend/app/ai/phishing_model.py](backend/app/ai/phishing_model.py)

Machine learning detector using RandomForest with TF-IDF vectorization:

```python
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

class SklearnDetector:
    """RandomForest-based phishing classifier persisted to disk."""

    def __init__(self, model_path: Path, vectorizer_path: Path, threshold: float = 0.5):
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.threshold = threshold
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        log.debug("Loading artifacts, model_path=%s, vectorizer_path=%s",
                  self.model_path, self.vectorizer_path)
        
        if self.model_path.exists() and self.vectorizer_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                log.info("Loaded sklearn artifacts from disk")
            except Exception:
                log.exception("Failed to load sklearn artifacts")
                self.model = None
                self.vectorizer = None

    def analyse(self, subject: str, body: str) -> Dict[str, float | str]:
        if not self.is_ready():
            raise RuntimeError("Sklearn model is not ready; train the detector first.")

        combined_text = f"{subject} {body}".strip()
        X_tfidf = self.vectorizer.transform([combined_text])
        
        proba_array = self.model.predict_proba(X_tfidf)[0]
        proba = float(proba_array[1]) if len(proba_array) == 2 else 1.0
        label = "suspicious" if proba >= self.threshold else "safe"
        
        return {"probability": proba, "model_label": label}
```

**Key Idea**: Serialized ML artifacts (model + vectorizer) are loaded once and reused for all predictions.

---

## 7. Email Enrichment - Feature Extraction

**File**: [backend/app/services/enrichment_service.py](backend/app/services/enrichment_service.py)

Extract heuristic features from email content for phishing detection:

```python
import re
from urllib.parse import urlparse

URL_RE = re.compile(r'https?://[^\s)"]+', re.IGNORECASE)
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly"}
SUSPICIOUS_WORDS = {"verify", "update", "urgent", "password", "confirm", "expire"}

def enrichment_features(subject: str, body: str) -> Dict:
    txt = f"{subject or ''}\n{body or ''}"
    txt_lower = txt.lower()

    urls = extract_urls(txt)
    domains = extract_domains(txt)
    
    return {
        "subject_len": len(subject or ""),
        "text_len": len(txt),
        "num_urls": len(urls),
        "has_shortener": any(d in SHORTENERS for d in domains),
        "num_exclamations": txt.count("!"),
        "num_suspicious_words": sum(1 for w in SUSPICIOUS_WORDS if w in txt_lower),
        "html_ratio": calculate_html_ratio(body),
    }
```

**Key Idea**: Extract numerical features from email text that ML model uses alongside TF-IDF vectors.

---

## 8. Database Access Layer with PostgreSQL

**File**: [backend/app/repository/gmail_db.py](backend/app/repository/gmail_db.py)

Thin wrapper around PostgreSQL using psycopg:

```python
import psycopg
from contextlib import contextmanager

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    gmail_id TEXT UNIQUE NOT NULL,
    subject TEXT,
    sender TEXT,
    recipients TEXT,
    body TEXT,
    analysis JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

class EmailRepository:
    """Thin wrapper around psycopg for storing analysed emails."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._conn = None

    def connect(self) -> psycopg.extensions.connection:
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(self.database_url)
        return self._conn

    @contextmanager
    def cursor(self):
        conn = self.connect()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    def upsert_email(self, gmail_id: str, subject: str, analysis: dict) -> int:
        with self.cursor() as cur:
            cur.execute("""
                INSERT INTO emails (gmail_id, subject, analysis)
                VALUES (%s, %s, %s)
                ON CONFLICT (gmail_id) DO UPDATE
                SET analysis = EXCLUDED.analysis
                RETURNING id;
            """, (gmail_id, subject, psycopg.types.json.Json(analysis)))
            return cur.fetchone()[0]
```

**Key Idea**: Context manager pattern ensures proper database connection and transaction handling.

---

## 9. Gmail OAuth Integration

**File**: [backend/app/client/gmail_api.py](backend/app/client/gmail_api.py)

Google OAuth authentication and Gmail API access:

```python
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def create_service(
    client_secret_file,
    api_name,
    api_version,
    scopes,
    token_dir="token_files",
):
    creds = None
    token_file = f"token_{api_name}_{api_version}.json"

    # Load cached credentials
    if os.path.exists(os.path.join(token_dir, token_file)):
        creds = Credentials.from_authorized_user_file(
            os.path.join(token_dir, token_file), scopes
        )

    # If no valid creds, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_file, scopes
            )
            creds = flow.run_local_server(port=0)

    # Save and build service
    with open(os.path.join(token_dir, token_file), "w") as token:
        token.write(creds.to_json())

    service = build(api_name, api_version, credentials=creds)
    return service
```

**Key Idea**: Handles OAuth flow with token caching to avoid repeated authentication.

---

## 10. ML Model Training with Enrichment Features

**File**: [backend/app/ai/phishing_model.py](backend/app/ai/phishing_model.py)

Combining TF-IDF with enrichment vectors for improved classification:

```python
import numpy as np
import scipy.sparse as sp
from sklearn.ensemble import RandomForestClassifier

def _enrichment_vector(subject: str, body: str) -> np.ndarray:
    """Convert enrichment features to fixed-order numerical vector."""
    feats = enrichment_features(subject, body)
    return np.array([
        feats["subject_len"],           # 0
        feats["text_len"],              # 1
        feats["num_urls"],              # 2
        1.0 if feats["has_shortener"] else 0.0,  # 3
        feats["num_exclamations"],      # 4
        feats["num_upper_words"],       # 5
        feats["num_suspicious_words"],  # 6
        feats["html_ratio"],            # 7
    ], dtype=np.float32)

def train_detector(subjects, bodies, labels):
    """Train RandomForest with combined TF-IDF + enrichment features."""
    
    # TF-IDF features
    vectorizer = TfidfVectorizer(max_features=1000)
    X_tfidf = vectorizer.fit_transform(bodies)
    
    # Enrichment features
    X_enrichment = _enrichment_vectors_batch(subjects, bodies)
    
    # Combine features
    X_combined = sp.hstack([X_tfidf, X_enrichment], format="csr")
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_combined, labels)
    
    return model, vectorizer
```

**Key Idea**: Hybrid approach combines text vectorization with domain-specific heuristic features.

---

## Summary of Key Ideas

| Concept | Files | Purpose |
|---|---|---|
| **FastAPI Setup** | main.py | Application initialization with lifecycle management |
| **Type Safety** | email_models.py | Request/response validation using Pydantic |
| **Config Management** | settings.py | Externalized configuration from environment |
| **REST Endpoints** | controllers/emails.py | Route handlers with dependency injection |
| **Business Logic** | services/email_service.py | Service layer orchestrating workflows |
| **ML Inference** | ai/phishing_model.py | RandomForest model loading and prediction |
| **Feature Engineering** | services/enrichment_service.py | Extract heuristic features from emails |
| **Database Access** | repository/gmail_db.py | PostgreSQL persistence with psycopg |
| **OAuth Integration** | client/gmail_api.py | Gmail API authentication and access |
| **Hybrid ML** | ai/phishing_model.py | Combine TF-IDF + enrichment vectors |

---

## Architecture Flow

```
Client Request
    ↓
[FastAPI Route Handler] (controllers/emails.py)
    ↓ (Validates with Pydantic)
[EmailService] (services/email_service.py)
    ├→ [Enrichment Service] (services/enrichment_service.py)
    ├→ [ML Detector] (ai/phishing_model.py)
    └→ [EmailRepository] (repository/gmail_db.py)
         ↓
    PostgreSQL Database
```

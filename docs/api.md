# CyberNest SOAR — API Reference

Base URL: `http://localhost:8000`  
Auto-generated docs: [`/docs`](http://localhost:8000/docs) (Swagger) · [`/redoc`](http://localhost:8000/redoc) (ReDoc)

---

## Email Endpoints (`/api`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/emails/sync` | Pull latest emails from Gmail and analyse each. Optional `?max_results=1-500`. |
| POST | `/api/emails` | Submit an email payload manually, analyse it, persist result. Returns 201. |
| GET | `/api/emails` | List emails (basic, no analysis). Supports `?limit=1-200` (default 20) and `?offset=0`. |
| GET | `/api/emails/{gmail_id}` | Get a single email by Gmail ID (basic). Returns 404 if not found. |

### POST `/api/emails` — Example

```json
{
  "sender": "attacker@phish.com",
  "recipients": ["victim@corp.com"],
  "subject": "Urgent: Verify your account",
  "body": "Click here to secure your account: http://evil.com/login",
  "attachments": []
}
```

### Response

```json
{
  "record_id": 1,
  "gmail_id": "manual-<uuid>",
  "analysis": {
    "spelling_score": 0.31,
    "keyword_score": 0.08,
    "composite_score": 0.196,
    "model_label": "suspicious"
  }
}
```

---

## AI / Classification Endpoints (`/api/ai`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/ai/classifications` | List emails with full analysis data. Supports `?limit=1-200` and `?offset=0`. |
| GET | `/api/ai/classify/{gmail_id}` | Re-analyse a specific email by Gmail ID. Returns 404 if not found. |
| POST | `/api/ai/classify-payload` | Classify a direct email payload without persisting. Returns 503 if ML model unavailable. |
| POST | `/api/ai/classify/{gmail_id}/feedback` | Submit feedback on a classification. Body: `{"is_correct": true/false}`. |

---

## Enrichment & External APIs

The backend enriches alerts via these external services (configured in backend env):

| Service | Purpose |
|---------|---------|
| VirusTotal | File/URL reputation |
| AbuseIPDB | IP reputation |
| MISP | Threat intelligence sharing |
| EPSS | Exploit prediction scoring |
| NVD | CVE details |
| CISA KEV | Known exploited vulnerabilities |
| URLhaus | Malicious URL database |
| AlienVault OTX | Open threat exchange |

---

## Models

### EmailRecord

```
sender, recipients, subject, body, attachments (list),
spelling_score, keyword_score, composite_score, model_label,
gmail_id, record_id, created_at
```

### EmailAnalysis

```
spelling_score (float)
keyword_score (float)
composite_score (float)
model_label (str): "benign" | "suspicious" | "malicious"
```

### Feedback

```json
{
  "is_correct": true
}
```

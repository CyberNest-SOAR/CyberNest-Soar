# API Reference

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

### POST `/api/emails` — Example Request

```json
{
  "sender": "attacker@phish.com",
  "recipients": ["victim@corp.com"],
  "subject": "Urgent: Verify your account",
  "body": "Click here to secure your account: http://evil.com/login",
  "attachments": []
}
```

### POST `/api/emails` — Example Response

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

## Model Schemas

### EmailRecord

```
sender          string    Email sender address
recipients      []string  List of recipient addresses
subject         string    Email subject line
body            string    Email body content
attachments     []string  List of attachment filenames
spelling_score   float    Spelling anomaly score (0–1)
keyword_score    float    Suspicious keyword score (0–1)
composite_score  float    Combined risk score (0–1)
model_label     string    "benign" | "suspicious" | "malicious"
gmail_id        string    Gmail message ID (or manual-<uuid>)
record_id       int       Database record ID
created_at      datetime  Timestamp of creation
```

### EmailAnalysis

```
spelling_score   float    0–1, higher = more anomalies
keyword_score    float    0–1, higher = more suspicious keywords
composite_score  float    0–1, combined from spelling + keyword + model
model_label      string   "benign" | "suspicious" | "malicious"
```

### Feedback

```json
{
  "is_correct": true
}
```

---

## External Enrichment Services

The backend enriches alerts via these external APIs (configured via environment variables):

| Service | Purpose | Config Variable |
|---------|---------|-----------------|
| VirusTotal | File/URL reputation | `VT_API_KEY` |
| AbuseIPDB | IP reputation | `ABUSEIPDB_API_KEY` |
| MISP | Threat intelligence sharing | `MISP_URL` + `MISP_API_KEY` |
| EPSS | Exploit prediction scoring | (public API, no key required) |
| NVD | CVE details | `NVD_API_KEY` (optional) |
| CISA KEV | Known exploited vulnerabilities | (public feed) |
| URLhaus | Malicious URL database | (public API) |
| AlienVault OTX | Open threat exchange | `OTX_API_KEY` |

---

## Error Handling

All endpoints return standard HTTP status codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (validation error) |
| 404 | Resource not found |
| 503 | Service unavailable (e.g., ML model not loaded) |

Error responses follow this format:

```json
{
  "detail": "Error description message"
}
```

---

## Rate Limiting

Rate limiting is configured at the API Gateway level (Kong/NGINX). Default limits:

| Tier | Requests/min |
|------|-------------|
| Standard | 60 |
| Authenticated | 300 |

---

## Authentication

API authentication is implemented via JWT tokens. Include the token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Obtain a token from the `/auth/login` endpoint (available when authentication is enabled).

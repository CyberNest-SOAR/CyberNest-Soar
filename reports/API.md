# API Reference

Base URL: `http://localhost:8000`

Auto-generated docs: [`/docs`](http://localhost:8000/docs) (Swagger) · [`/redoc`](http://localhost:8000/redoc) (ReDoc)

---

## System & Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root status |
| GET | `/health` | Health check |
| GET | `/api/v1/system/health` | Detailed system health check |
| GET | `/api/v1/system/audit-log` | View recent audit log entries |
| GET | `/api/v1/system/audit-log/export` | Export audit log as text |
| GET | `/api/v1/system/end-point-health` | Check external service health (OpenSearch, TheHive, MISP, etc.) |
| GET | `/metrics` | Prometheus metrics |

---

## Authentication (`/api/auth`, `/api/v1/users`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Login with username/password, returns JWT |
| POST | `/api/v1/users/login` | Login (alternative endpoint) |
| POST | `/api/v1/users/logout` | Logout current user |
| POST | `/api/v1/users/refresh` | Refresh JWT token |
| GET | `/api/v1/users/me` | Get current authenticated user |
| GET | `/api/v1/users/` | List all users |
| GET | `/api/v1/users/{user_id}` | Get user by ID |
| POST | `/api/v1/users/` | Create new user |
| PUT | `/api/v1/users/{user_id}` | Update user |
| DELETE | `/api/v1/users/{user_id}` | Delete user |
| GET | `/api/v1/users/{user_id}/sessions` | Get sessions for a user |
| GET | `/api/v1/users/sessions` | List all active sessions |
| DELETE | `/api/v1/users/sessions/{session_id}` | Revoke a session |
| GET | `/api/v1/users/audit/sessions` | List audit session history |
| GET | `/api/v1/users/roles/list` | List available roles |
| GET | `/api/v1/users/audit/log` | Get audit log |
| POST | `/api/v1/users/{user_id}/mfa/toggle` | Toggle MFA for user |
| POST | `/api/v1/users/{user_id}/reset-password` | Admin-initiated password reset |
| GET | `/api/v1/users/{user_id}/permissions` | Check user permissions |

---

## Settings (`/api/v1/settings`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/settings` | Get all platform settings |
| PUT | `/api/v1/settings` | Update settings |
| GET | `/api/v1/settings/security` | Get security toggles |
| PUT | `/api/v1/settings/security` | Update security toggles |
| GET | `/api/v1/settings/rbac` | Get RBAC configuration |
| PUT | `/api/v1/settings/rbac` | Update RBAC configuration |
| GET | `/api/v1/settings/auth` | Get auth configuration |
| PUT | `/api/v1/settings/auth` | Update auth configuration |

---

## Alerts (`/api/v1/alerts`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/alerts/` | Fetch alerts from OpenSearch (Wazuh index) with pagination |
| POST | `/api/v1/alerts/batch/process` | Run full downstream pipeline on a batch of alerts |
| POST | `/api/v1/alerts/batch/enrich` | Enrich alert batch with threat intelligence |
| GET | `/api/v1/alerts/training-format` | Get alerts formatted for ML training |

### Log Filtering & Noise Reduction

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/alerts/filter` | Classify alerts as noise or important (ML-based) |
| POST | `/api/v1/alerts/predict-noise` | Predict noise probability for a raw alert dict |

---

## Risk Scoring (`/api/v1/risk-score`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/risk-score/` | Calculate risk score (0–100) for a single alert |
| POST | `/api/v1/risk-score/batch` | Batch risk scoring for multiple alerts |

Evaluates CVSS severity, EPSS exploit probability, asset criticality, and historical patterns.

---

## Patch Recommendation (`/api/v1/patch`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/patch/` | Get patch recommendations for a detected vulnerability |
| POST | `/api/v1/patch/batch` | Batch patch recommendations |

Returns priority-ordered patches based on exploit timelines and asset exposure.

---

## Playbooks (`/api/v1/playbooks`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/playbooks/decision` | Unified playbook decision engine — determines response action |
| POST | `/api/v1/playbooks/create-case` | Create a TheHive case from alert data |
| POST | `/api/v1/playbooks/from-alert` | Create case directly from a `UnifiedAlert` payload |

---

## Threat Intelligence (`/api/v1/threat-intel`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/threat-intel/lookup` | IOC lookup (VirusTotal + MISP) from an alert |
| POST | `/api/v1/threat-intel/batch-lookup` | Batch IOC lookup for multiple alerts |
| POST | `/api/v1/threat-intel/lookup-ioc` | Single IOC lookup with per-source detail |
| POST | `/api/v1/threat-intel/misp-sync` | Sync recent threat hits with MISP |

---

## Alert Intelligence

| Method | Path | Description |
|--------|------|-------------|
| POST | `/analyze` | Analyze an alert via DeepSeek-R1 LLM |

---

## RAG (Knowledge Base) (`/api/v2/rag`, `/api/v1/rag`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v2/rag/knowledge-base` | Add an entry to the knowledge base |
| POST | `/api/v2/rag/search` | Semantic search across knowledge base |
| GET | `/api/v2/rag/knowledge-base` | List all knowledge base entries |
| DELETE | `/api/v2/rag/knowledge-base/{case_id}` | Delete a KB entry |
| GET | `/api/v2/rag/stats` | Knowledge base statistics |
| POST | `/api/v2/rag/ingest-feedback` | Batch-ingest analyst feedback into KB |
| POST | `/api/v1/rag/query` | Semantic RAG query using Qdrant + Ollama |
| GET | `/api/v1/rag/health` | RAG system health check |

---

## SOC Chat (`/api/soc-chat`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/soc-chat/messages` | Send a chat message |
| GET | `/api/soc-chat/messages` | List chat messages |
| GET | `/api/soc-chat/mentions` | Get mentions for the current user |
| PATCH | `/api/soc-chat/mentions/{mention_id}/read` | Mark a mention as read |

---

## Email / Phishing (`/api`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/emails/sync` | Pull latest Gmail messages and analyse each |
| POST | `/api/emails` | Submit a manual email payload for analysis |
| GET | `/api/emails` | List emails (basic info, no analysis) |
| GET | `/api/emails/{gmail_id}` | Get a single email by Gmail ID |

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

## AI Classification (`/api/ai`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/ai/classifications` | List classified emails with analysis data |
| GET | `/api/ai/classify/{gmail_id}` | Re-analyse an email by Gmail ID |
| POST | `/api/ai/classify-payload` | Classify a direct payload without persisting |
| POST | `/api/ai/classify/{gmail_id}/feedback` | Submit feedback on a classification |

---

## LLM Classification (`/api/v2/llm`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v2/llm/classify` | Classify an alert using LLM reasoning |
| POST | `/api/v2/llm/preview-rag` | Preview RAG context for an alert |

---

## Model Training (`/api/v2/training`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v2/training/retrain-xgboost` | Retrain XGBoost model on latest feedback |
| POST | `/api/v2/training/retrain-randomforest` | Retrain RandomForest model |
| GET | `/api/v2/training/metrics` | Get model performance metrics |
| GET | `/api/v2/training/drift` | Check model drift status |
| POST | `/api/v2/training/auto-retrain` | Auto-retrain if drift detected |

---

## SSVC Prioritization (`/api/v1/ssvc`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/ssvc/evaluate` | Evaluate SSVC decision for a vulnerability |
| POST | `/api/v1/ssvc/evaluate-alert` | Evaluate SSVC from an alert payload |

---

## Clustering (`/api/v1/clustering`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/clustering/add` | Add alert and check cluster membership |
| GET | `/api/v1/clustering/clusters` | Get current cluster map |
| POST | `/api/v1/clustering/find` | Find matching cluster for an alert |

---

## Deduplication (`/api/v1/dedup`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/dedup/check` | Check if an alert is a duplicate |
| POST | `/api/v1/dedup/clear` | Clear the dedup cache |

---

## Feedback (`/api/v2/feedback`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v2/feedback` | Submit analyst feedback |
| GET | `/api/v2/feedback` | List feedback entries |
| GET | `/api/v2/feedback/stats` | Feedback statistics |
| GET | `/api/v2/feedback/export-training` | Export feedback in training format |
| DELETE | `/api/v2/feedback/{feedback_id}` | Delete a feedback entry |

---

## Cortex Analyzer Engine (`/api/v1/cortex`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/cortex/health` | Cortex service health check |
| GET | `/api/v1/cortex/analyzers` | List available analyzers |
| GET | `/api/v1/cortex/analyzers/{analyzer_id}` | Get analyzer details |
| POST | `/api/v1/cortex/analyzers/{analyzer_id}/run` | Run an analyzer |
| GET | `/api/v1/cortex/jobs/{job_id}` | Get job report |
| GET | `/api/v1/cortex/responders` | List available responders |
| POST | `/api/v1/cortex/responders/{responder_id}/run` | Run a responder |

---

## Osquery Fleet Management (`/api/v1/osquery`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/osquery/health` | Osquery fleet health check |
| GET | `/api/v1/osquery/nodes` | List enrolled fleet nodes |
| GET | `/api/v1/osquery/nodes/{node_id}` | Get node details |
| POST | `/api/v1/osquery/query` | Run a raw SQL query on a node |
| POST | `/api/v1/osquery/query/quick-snapshot` | Run predefined quick-snapshot queries |
| GET | `/api/v1/osquery/tables` | List available osquery tables |
| GET | `/api/v1/osquery/tables/{table_name}` | Get table schema |

---

## UI Dashboard (`/api/v1/ui`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/ui/command-center` | SOC Command Center metrics |
| GET | `/api/v1/ui/alerts-table` | Paginated alerts table |
| GET | `/api/v1/ui/investigation/{event_id}` | Investigation detail |
| GET | `/api/v1/ui/incident-response` | Incident response overview |
| GET | `/api/v1/ui/threat-intel-center` | Threat Intelligence Center |
| GET | `/api/v1/ui/asset-intelligence` | Asset & Endpoint Intelligence |
| GET | `/api/v1/ui/ai-operations` | AI Operations Center |
| GET | `/api/v1/ui/it-hygiene` | IT Hygiene & Exposure |
| GET | `/api/v1/ui/playbooks-automation` | Playbooks & Automation |
| GET | `/api/v1/ui/reporting-audit` | Reporting & Audit |
| GET | `/api/v1/ui/admin-health` | Administration & System Health |
| POST | `/api/v1/ui/admin-health/providers` | Add a threat intel provider |
| POST | `/api/v1/ui/admin-health/check-connection` | Check a provider connection |
| GET | `/api/v1/ui/patch-management` | Patch Management with CVEs |
| GET | `/api/v1/ui/dashboard` | All dashboard pages combined |

---

## Graph & Visualization (`/api/v1/graph`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/graph/pipeline/attack-type-distribution` | Attack types from dataset pipeline |
| GET | `/api/v1/graph/pipeline/severity-distribution` | Severity distribution |
| GET | `/api/v1/graph/pipeline/mitre-tactics` | MITRE ATT&CK tactics breakdown |
| GET | `/api/v1/graph/pipeline/analyst-verdicts` | Analyst verdict distribution |
| GET | `/api/v1/graph/pipeline/timeline` | Event timeline over time |
| GET | `/api/v1/graph/alerts/severity-distribution` | Live alert severity distribution |
| GET | `/api/v1/graph/alerts/timeline` | Live alert timeline |
| GET | `/api/v1/graph/alerts/top-rules` | Top Wazuh rules by volume |
| GET | `/api/v1/graph/alerts/source-breakdown` | Alert source breakdown |

---

## Operations (`/api/v1/operations`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/operations/execute` | Execute a response action |
| POST | `/api/v1/operations/approval/request` | Request approval for an action |
| POST | `/api/v1/operations/approval/{approval_id}/approve` | Approve a pending action |
| POST | `/api/v1/operations/approval/{approval_id}/reject` | Reject a pending action |
| GET | `/api/v1/operations/approval/pending` | Get pending approvals |
| GET | `/api/v1/operations/approval/history` | Get approval history |
| POST | `/api/v1/operations/feedback` | Record analyst feedback on an execution |
| GET | `/api/v1/operations/feedback` | List operations feedback |
| GET | `/api/v1/operations/feedback/stats` | Feedback statistics |
| POST | `/api/v1/operations/feedback/clear` | Clear all feedback |
| GET | `/api/v1/operations/history` | Execution history |

---

## External Enrichment Services

The backend enriches alerts via these external APIs:

| Service | Purpose | Config Variable |
|---------|---------|-----------------|
| VirusTotal | File/URL reputation | `VT_API_KEY` |
| AbuseIPDB | IP reputation | `ABUSEIPDB_API_KEY` |
| MISP | Threat intelligence sharing | `MISP_URL` + `MISP_API_KEY` |
| EPSS | Exploit prediction scoring | (public API) |
| NVD | CVE details | `NVD_API_KEY` (optional) |
| CISA KEV | Known exploited vulnerabilities | (public feed) |
| URLhaus | Malicious URL database | (public API) |
| AlienVault OTX | Open threat exchange | `OTX_API_KEY` |

---

## Error Handling

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | Deleted |
| 400 | Bad request (validation error) |
| 401 | Unauthorized |
| 403 | Forbidden (RBAC) |
| 404 | Resource not found |
| 503 | Service unavailable |

```json
{
  "detail": "Error description message"
}
```

---

## Authentication

JWT-based authentication. Include token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Obtain a token from `POST /api/auth/login` or `POST /api/v1/users/login`. RBAC roles control access to specific endpoints.

---

## Rate Limiting

Configured at the API Gateway level (Kong/NGINX):

| Tier | Requests/min |
|------|-------------|
| Standard | 60 |
| Authenticated | 300 |

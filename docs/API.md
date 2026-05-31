# CyberNest SOAR — API Reference

This project exposes **32 REST endpoints** across **4 FastAPI applications**:
[SOAR Backend](#1-soar-backend-unified-api), [Phishing Detection](#2-phishing-detection-api),
[SOC Dataset Pipeline](#3-soc-dataset-pipeline), and [Simulation Engine](#4-simulation-engine).

---

# 1. SOAR Backend Unified API

**Base URL:** `http://<host>:<port>/api/v1`

Root health checks at `/` and `/health` (no `/api/v1` prefix).

---

## Alerts — Team 0: Core Data

### `GET /api/v1/alerts/`

Fetch Wazuh alerts from OpenSearch with optional enrichment.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 100 | Number of alerts to fetch (≥1) |
| `from` (offset) | int | 0 | Number of alerts to skip |
| `severity` | int | — | Filter by Wazuh rule level (1–15) |
| `enrich` | bool | false | Enrich via VT, AbuseIPDB, MISP in parallel |
| `vuln` | bool | — | `true` = only alerts with CVEs, `false` = only without |

Response: `List[UnifiedAlert]` — backend schema (11 core fields + nested `EnrichmentData`).

```json
{
  "event_id": "wazuh-abc123",
  "source": "wazuh",
  "timestamp": "2026-05-22T10:30:00Z",
  "description": "SSH Brute Force detected",
  "severity": 10,
  "host_context": { "hostname": "web-01", "ip_address": "10.0.1.50" },
  "raw_data": { "...": "..." },
  "enrichment_data": {
    "tags": ["vuln:CVE-2026-1234", "misp_hit"],
    "virus_total": { "score": 75, "malicious": 6 },
    "abuse_ipdb": { "score": 85, "total_reports": 42 },
    "misp": { "matches": ["uuid-..."], "count": 2 },
    "epss": { "score": 0.87 },
    "nvd": { "cvss": 9.8, "severity": "CRITICAL" },
    "cisa_kev": { "cve": "CVE-2026-1234", ... }
  }
}
```

---

### `GET /api/v1/alerts/training-format`

Fetch alerts in the **dataset_pipeline UnifiedAlert schema** (111 flat fields)
so AI models see the exact same schema during inference as training data.
Enrichment is flattened to scalars (`enrichment_vt_score`, `enrichment_abuse_score`, …).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 100 | Number of alerts |
| `from` (offset) | int | 0 | Pagination offset |
| `enrich` | bool | false | Enrich + flatten into training scalars |

Response: `List[dict]` — 111-field UnifiedAlert.

```json
{
  "event_id": "wazuh-abc123",
  "dataset_source": "wazuh",
  "src_ip": "203.0.113.5",
  "dst_ip": "10.0.1.50",
  "src_port": 57321,
  "dst_port": 22,
  "protocol": "TCP",
  "alert_signature": "SSH Brute Force",
  "alert_severity": 10,
  "attack_type": "brute_force",
  "enrichment_vt_score": 75,
  "enrichment_abuse_score": 85,
  "enrichment_misp_matches": ["uuid-..."],
  "enrichment_epss_score": 0.87,
  "enrichment_cvss_score": 9.8,
  "asset_criticality": "medium",
  "host_role": "unknown",
  "analyst_verdict": null,
  "...": "..."
}
```

---

### `POST /api/v1/alerts/batch/process`

Run the full downstream pipeline on a batch of alerts (enrich + patch + risk + LLM
classification).

| Parameter | Type | Description |
|-----------|------|-------------|
| Body | `List[UnifiedAlert]` | Alerts array (as returned by `GET /alerts/`) |

Response: `List[dict]` — per-alert combined result.

---

### `POST /api/v1/alerts/batch/enrich`

Enrich a batch with threat intel only (VT, AbuseIPDB, MISP).

| Parameter | Type | Description |
|-----------|------|-------------|
| Body | `List[UnifiedAlert]` | Alerts array |

Response: `List[UnifiedAlert]` — enriched in place.

---

### `POST /api/v1/alerts/filter`

LLM-assisted classification of alerts as noise vs. important.

| Parameter | Type | Description |
|-----------|------|-------------|
| Body | `FilterRequest` | `{ alerts: List[UnifiedAlert] }` |

Response: `List[FilterResult]` — `{ alert_id, classification, confidence, summary }`.

---

## Threat Intel — Team 5: Intel

### `POST /api/v1/threat-intel/lookup`

Lookup IOC from a UnifiedAlert in VirusTotal and MISP.

| Parameter | Type |
|-----------|------|
| Body | `UnifiedAlert` |

Response: `IntelResponse` — `{ ioc, malicious, reputation, sources }`.

---

### `POST /api/v1/threat-intel/batch-lookup`

Enrich a batch of alerts with threat intel.

| Parameter | Type |
|-----------|------|
| Body | `List[UnifiedAlert]` |

Response: `List[IntelResponse]`.

---

### `POST /api/v1/threat-intel/misp-sync`

Sync recent OpenSearch hits with MISP explicitly.

Response: `MispSyncResponse` — `{ status, synced_events, events }`.

---

## Patch Recommendations — Team 2: Patch

### `POST /api/v1/patch/`

Get patch recommendations for a single alert.

| Parameter | Type |
|-----------|------|
| Body | `UnifiedAlert` |

Response: `PatchResponse` — `{ host, recommendations: [{ cve, cvss, epss, priority, action }] }`.

---

### `POST /api/v1/patch/batch`

Get patch recommendations for a batch of alerts.

| Parameter | Type |
|-----------|------|
| Body | `List[UnifiedAlert]` |

Response: `List[PatchResponse]`.

---

## Risk Scoring — Team 1: Risk

### `POST /api/v1/risk-score/`

Calculate risk score for an alert.

| Parameter | Type |
|-----------|------|
| Body | `RiskScoreRequest` |

Response: `RiskScoreResponse` — `{ event_id, risk_score, priority, confidence, features }`.

---

### `POST /api/v1/risk-score/batch`

Score a batch of alerts.

| Parameter | Type |
|-----------|------|
| Body | `List[UnifiedAlert]` |

Response: `List[RiskScoreResponse]`.

---

## Playbooks — Team 4: Playbooks

### `POST /api/v1/playbooks/decision`

Combines tag-based logic with risk-score thresholds for playbook decisions.

| Parameter | Type |
|-----------|------|
| Body | `PlaybookDecisionRequest` |

Response: `PlaybookDecisionResponse` — `{ action, confidence, automation_level, reason }`.

---

## Health

### `GET /`

Root health check.

```json
{ "status": "SOAR API is online", "version": "v1" }
```

### `GET /health`

Deep health check: verifies OpenSearch cluster and MISP connectivity.

```json
{ "status": "healthy", "opensearch": "connected", "misp": "connected" }
```

---

# 2. Phishing Detection API

**Base URL:** `http://<host>:<port>/api`

---

### `POST /api/emails/sync`

Pull latest emails from Gmail and analyse each message.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_results` | int | — | 1–500 |

Response: `EmailSyncResponse`.

---

### `POST /api/emails`

Accept an email payload, analyse it, and persist the result.

| Parameter | Type |
|-----------|------|
| Body | `EmailPayload` |

Response: `EmailCreateResponse` (201).

---

### `GET /api/emails`

List all analysed emails.

| Parameter | Type | Default |
|-----------|------|---------|
| `limit` | int | 20 (max 200) |
| `offset` | int | 0 |

Response: `list[EmailRecordBasic]`.

---

### `GET /api/emails/{gmail_id}`

Get a single email record by its Gmail ID.

| Parameter | Type |
|-----------|------|
| Path: `gmail_id` | str |

Response: `EmailRecordBasic`.

---

### `GET /api/ai/classifications`

List all email records with full classification data.

| Parameter | Type | Default |
|-----------|------|---------|
| `limit` | int | 20 (max 200) |
| `offset` | int | 0 |

Response: `list[EmailRecord]`.

---

### `GET /api/ai/classify/{gmail_id}`

Re-classify an email by Gmail ID using the ML model.

| Parameter | Type |
|-----------|------|
| Path: `gmail_id` | str |

Response: `EmailAnalysis`.

---

### `POST /api/ai/classify-payload`

Classify a raw email payload (subject + body) without persisting.

| Parameter | Type |
|-----------|------|
| Body | `EmailPayload` |

Response: `EmailAnalysis`.

---

### `POST /api/ai/classify/{gmail_id}/feedback`

Submit user feedback on whether the model classification was correct.

| Parameter | Type |
|-----------|------|
| Path: `gmail_id` | str |
| Body | `FeedbackPayload` |

Response: `{ status, gmail_id, is_correct }`.

---

# 3. SOC Dataset Pipeline

**Base URL:** `http://<host>:8003/pipeline`
**Port:** 8003

---

### `POST /pipeline/run`

Run the SOC dataset pipeline: download → parse → enrich → augment → attack
chains → SOC reasoning → export.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_events` | int | 50000 | Target alert count |
| `download_only` | bool | false | Only download datasets |
| `export_only` | bool | false | Re-export from existing NDJSON |
| `reasoning_only` | bool | false | Apply SOC reasoning to existing NDJSON + re-export |

Response:
```json
{
  "status": "complete",
  "stats": {
    "download": { "cicids2017": 5, "unsw_nb15": 2, ... },
    "parse": 221362,
    "enrich": 221362,
    "augment": 259412,
    "chains": 259412,
    "reasoning": 259412,
    "export": { "ndjson": "...", "csv": "...", "llm_analyst_notes": "...", ... },
    "elapsed_seconds": 142.3,
    "final_alert_count": 259412
  }
}
```

---

### `GET /pipeline/status`

Show current pipeline execution status and stats from the last run.

Response: `{ status: "complete"|"idle", stats: {...} }`.

---

### `GET /pipeline/export/{format}`

List export files in a given format.

| Parameter | Type | Description |
|-----------|------|-------------|
| Path: `format` | str | `ndjson`, `csv`, `json` |

Response: `{ files: [...], latest: "..." }`.

---

# 4. Simulation Engine

**Base URL:** `http://<host>:8002/simulate`
**Port:** 8002

---

### `GET|POST /simulate/generate`

Generate simulated security events with configurable attack distribution.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `total` | int | — | Number of events |
| `campaign_id` | str | auto | Campaign identifier |
| `format` | str | json | Output format |
| `export_opensearch` | bool | false | Index to OpenSearch |
| `export_thehive` | bool | false | Create TheHive case |
| `write_files` | bool | false | Write to sensor log files |
| Body (POST) | `Dict` | — | Override attack distribution weights |

Supports 8 attack generators: `benign_traffic`, `malware`, `brute_force`,
`phishing`, `ddos`, `lateral_movement`, `privilege_escalation`, `noise_alerts`.

5 telemetry formatters: Wazuh, Suricata, Zeek, Velociraptor, osquery.

Response:
```json
{
  "status": "generated",
  "campaign_id": "cmp-abc123",
  "total_events": 500,
  "distribution": { "malware": 50, "brute_force": 40, ... },
  "files_written": { "suricata": 3, "zeek": 3, ... },
  "opensearch_indexed": 500,
  "thehive_case_id": 42
}
```

---

### `GET|POST /simulate/inject`

Generate events and inject them into Wazuh-monitored sensor log files.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `total` | int | 50 | Number of events |
| `campaign_id` | str | auto | Campaign identifier |
| `target` | str | all | `suricata`, `zeek`, `velociraptor`, `arkime`, or `all` |
| `format` | str | json | Output format |

---

### `POST /simulate/campaign`

Run a time-based multi-wave attack campaign with escalating intensity.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `total` | int | 5000 | Total events across all waves |
| `waves` | int | 5 | Number of attack waves |
| `interval_seconds` | int | 60 | Delay between waves |
| `format` | str | json | Output format |

---

### `GET /simulate/status`

Show current simulation configuration and generator state.

Response:
```json
{
  "campaign_id": "cmp-abc123",
  "distribution": { "malware": 0.10, "benign": 0.45, ... },
  "total_events_generated": 15000,
  "opensearch_connected": true,
  "thehive_connected": true
}
```

---

### `POST /simulate/config`

Update attack distribution and simulation config at runtime.

| Parameter | Type |
|-----------|------|
| Body | `Dict[str, Any]` |

Example body:
```json
{
  "distribution": { "malware": 0.15, "phishing": 0.10, "benign": 0.40 },
  "opensearch_host": "opensearch:9200"
}
```

---

### `GET /simulate/dataset/{format}`

Download a generated dataset file in the requested format.

| Parameter | Type | Default |
|-----------|------|---------|
| Path: `format` | str | — |
| `total` | int | 1000 |

Response: `JSONResponse` with inline Content-Disposition for download.

# CyberNest SOAR — API Reference

This project exposes **32+ REST endpoints** across **4 FastAPI applications**:
[SOAR Backend](#1-soar-backend-unified-api), [Phishing Detection](#2-phishing-detection-api),
[SOC Dataset Pipeline](#3-soc-dataset-pipeline), and [Simulation Engine](#4-simulation-engine).

---

# Pipeline Architecture

```
SENSOR LAYER                     SOAR BACKEND                    EXTERNAL INTEL
┌──────────┐                    ┌──────────────────┐            ┌────────────┐
│  Wazuh   │─── OpenSearch ────▶│  GET /alerts/    │───────────▶│ VirusTotal │
│ Suricata │                    │  (enrich=true)   │            │ AbuseIPDB  │
│   Zeek   │                    │                  │            │    MISP    │
│Velocirapt│                    │  asyncio.gather() │            │  NVD/EPSS  │
└──────────┘                    └────────┬─────────┘            │  CISA KEV  │
                                         │                      └────────────┘
                                         ▼
                              ┌──────────────────────┐
                              │  /alerts/filter       │  LLM classification
                              │  /risk-score/         │  Composite 0-100
                              │  /patch/              │  CVE recommendations
                              │  /playbooks/decision  │  Auto action decision
                              │  /threat-intel/lookup │  IOC enrichment
                              └──────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  TheHive → Cortex     │
                              │  Case mgmt + response │
                              └──────────────────────┘
```

**Enrichment** runs inline via `asyncio.gather()` with per-service 5s timeout,
`return_exceptions=True`, and private-IP short-circuit. CVE extraction via regex
from alert description feeds NVD/EPSS substage.

---

# 1. SOAR Backend Unified API

**Base URL:** `http://<host>:<port>/api/v1`

Root health checks at `/` and `/health` (no `/api/v1` prefix).

| Team | Domain | Responsibility |
|------|--------|---------------|
| 0 | Core Data & Alerts | Alert retrieval, stats, batch processing |
| 1 | Risk Scoring Engine | Multi-factor 0-100 composite score |
| 2 | Patch Recommendation Engine | CVE-based patch advice |
| 3 | Log Filtering & Noise Reduction | LLM-assisted noise vs important |
| 4 | Intelligent Playbooks | Automated action recommendation |
| 5 | Threat Intelligence & Enrichment | IOC lookup, MISP sync |

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

Response: `List[UnifiedAlert]` — backend schema (11 core fields + nested `EnrichmentData`).
If CVE regex matches description, NVD (CVSS) and EPSS are fetched and embedded.

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
    "cisa_kev": { "cve": "CVE-2026-1234" }
  }
}
```

**Private IP handling:** External lookups skipped for RFC1918 addresses;
defaults `vt_score=0`, `abuse_score=100` to avoid quota waste.

---

### `GET /api/v1/alerts/stats`

Aggregated alert statistics.

```json
{
  "by_severity": { "low": 40, "medium": 30, "high": 30 },
  "top_rules": [{ "rule_id": "5710", "count": 25 }]
}
```

---

### `GET /api/v1/alerts/training-format`

Fetch alerts in the **dataset_pipeline UnifiedAlert schema** (111 flat fields)
so AI models see the exact same schema during inference as training data.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 100 | Number of alerts |
| `from` (offset) | int | 0 | Pagination offset |
| `enrich` | bool | false | Enrich + flatten into training scalars |

Response: `List[dict]` — 111-field UnifiedAlert.

---

### `POST /api/v1/alerts/batch/process`

Run the full downstream pipeline on a batch of alerts (enrich + patch + risk + LLM).

| Parameter | Type | Description |
|-----------|------|-------------|
| Body | `List[UnifiedAlert]` | Alerts array |

Response: `List[dict]` — per-alert combined result.

---

### `POST /api/v1/alerts/batch/enrich`

Enrich a batch with threat intel only (VT, AbuseIPDB, MISP).

| Parameter | Type |
|-----------|------|
| Body | `List[UnifiedAlert]` |

Response: `List[UnifiedAlert]` — enriched in place.

---

### `POST /api/v1/alerts/filter`

LLM-assisted classification of alerts as noise vs. important (Team 3).

| Parameter | Type | Description |
|-----------|------|-------------|
| Body | `FilterRequest` | `{ alerts: List[UnifiedAlert] }` |

Response: `List[FilterResult]` — `{ alert_id, classification, confidence, summary }`.

**Decision heuristics:**
| Feature | Low Value | High Value |
|---------|-----------|------------|
| `event_count_5m` | Targeted attack | Scanner noise |
| `unique_ips` | Single source | Mass scanning |
| `vt_score` | Benign | Malicious |
| `asset_criticality` | Low value | High value target |

---

### `GET /api/v1/alerts/clusters`

Grouped alert clusters by type (Team 3).

```json
{ "clusters": [{ "type": "brute_force", "count": 50 }] }
```

---

## Risk Scoring — Team 1: Risk

### `POST /api/v1/risk-score/`

Calculate risk score for a single alert.

**Formula:**
```
RiskScore = min((Severity × 10) + (CVSS × 5) + (EPSS × 50)
                + (AbuseScore × 0.5) + (VTScore × 0.5), 100)
```

| Component | Range | Max Contribution |
|-----------|-------|------------------|
| Base (severity × 10) | 10–150 | 100 (clamped) |
| CVSS (× 5) | 0–49 | ~49 |
| EPSS (× 50) | 0–50 | ~50 |
| AbuseIPDB (× 0.5) | 0–50 | ~50 |
| VirusTotal (× 0.5) | 0–50 | ~50 |

**Priority mapping:**
| Score | Priority |
|-------|----------|
| > 70 | CRITICAL |
| > 30 | HIGH |
| ≤ 30 | MEDIUM / LOW |

Confidence is currently fixed at 0.85 across all scores.

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

### `GET /api/v1/patch/recommendations`

Query recommendations by host.

| Parameter | Type |
|-----------|------|
| Query: `host` | str |

Response: `{ host, recommendations: [...] }`.

---

### `POST /api/v1/patch/analyze`

Deep analysis of host patch status.

| Parameter | Type |
|-----------|------|
| Body | `{ host: str }` |

Response: Detailed patch posture for the host.

---

## Playbooks — Team 4: Playbooks

### `POST /api/v1/playbooks/decision`

Combines tag-based logic with risk-score thresholds for playbook decisions.

| Parameter | Type |
|-----------|------|
| Body | `PlaybookDecisionRequest` |

Response: `PlaybookDecisionResponse` — `{ action, confidence, automation_level, reason }`.

| Condition | Action | Automation |
|-----------|--------|------------|
| risk >= 90 | QUARANTINE_HOST | AUTO |
| Tag: phishing | CREATE_TICKET | SEMI |
| risk >= 70 + tag | BLOCK_IP | AUTO |
| Low risk | MONITOR | SEMI |

---

### `POST /api/v1/playbooks/execute`

Execute a specific playbook action.

| Parameter | Type |
|-----------|------|
| Body | `{ action: str, target: str }` |

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

Sync recent OpenSearch hits with MISP explicitly. Syncs last 50 alerts hourly.

Response: `MispSyncResponse` — `{ status, synced_events, events }`.

---

### `GET /api/v1/threat-intel`

Query IOC enrichment directly.

| Parameter | Type |
|-----------|------|
| Query: `ioc` | str |

Response: `{ ioc, malicious, reputation }`.

---

## Metrics & Hygiene

### `GET /api/v1/metrics/hygiene`

Security hygiene score across the estate.

```json
{ "score": 78, "breakdown": { "patch": 80, "auth": 70 } }
```

---

## Cases & Auth

### `POST /api/v1/cases`

Create a TheHive case from enriched alert data.

### `POST /api/v1/auth`

Authentication endpoint — returns JWT for subsequent requests.

**Auth header:** `Authorization: Bearer <JWT>`

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

Enterprise-grade SOC training dataset generator. Pipeline stages:

```
Download → Parse → Enrich → Augment → Attack Chains → SOC Reasoning → Export
                                                                           ↓
                              NDJSON / CSV / OpenSearch Bulk / TheHive / LLM Datasets
```

| Stage | Description |
|-------|-------------|
| **Download** | Fetches CICIDS2017, CSE-CIC-IDS2018, CTU-13, UNSW-NB15, LANL Auth, CERT Insider Threat + synthetic fallback |
| **Parse** | Normalizes all formats into 111-field `UnifiedAlert` schema |
| **Enrich** | GeoIP (country, ASN), MITRE ATT&CK mapping, simulated VT/AbuseIPDB/EPSS/CVSS/MISP scores |
| **Augment** | Simulated analyst verdicts (with 15% unassigned), noise injection (8-15% duplicates, 15% FP, 5% fatigue), alert clustering, playbook outcomes |
| **Attack Chains** | Multi-stage correlation (phishing→exfil, web exploit→ransomware, brute force→compromise) |
| **SOC Reasoning** | 7-step transformation: operational context, environmental context, asset/business context, identity/process context, temporal correlation, historical memory, SOC noise |
| **Export** | NDJSON, CSV, OpenSearch bulk, TheHive cases, direct OpenSearch index, 3 LLM training datasets |

---

### `POST /pipeline/run`

Run the full pipeline or a sub-stage.

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
    "download": { "cicids2017": 5, "unsw_nb15": 2 },
    "parse": 221362,
    "enrich": 221362,
    "augment": 259412,
    "chains": 259412,
    "reasoning": 259412,
    "export": {
      "ndjson": "data/outputs/soc_dataset_20260522_103000.ndjson",
      "csv": "data/outputs/soc_dataset_20260522_103000.csv",
      "opensearch_bulk": "data/outputs/soc_dataset_20260522_103000_bulk.ndjson",
      "thehive": ["case-1", "case-2"],
      "llm_analyst_notes": "data/outputs/llm_datasets/analyst_notes_20260522_103000.json",
      "llm_suppression_reasons": "data/outputs/llm_datasets/suppression_reasons_20260522_103000.json",
      "llm_escalation_decisions": "data/outputs/llm_datasets/escalation_decisions_20260522_103000.json",
      "opensearch_index": { "index": "soc-dataset-4.x", "documents": 259412 }
    },
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

## UnifiedAlert Schema (111 fields)

The canonical schema used by the dataset pipeline and the `/alerts/training-format` endpoint:

```
event_id, timestamp, dataset_source, event_type
src_ip, src_port, dst_ip, dst_port, protocol
src_hostname, dst_hostname, src_user, dst_user
process_name, command_line, file_name, file_hash, registry_key, service_name, image_path
alert_signature, alert_severity, alert_category, alert_action
bytes_sent, bytes_received, duration, packets
attack_type, mitre_technique_id, mitre_technique_name, mitre_tactic
confidence, true_positive, noise
ioc_ip, ioc_domain, ioc_url, ioc_hash
http_method, http_uri, http_user_agent, http_referrer, http_status
dns_query, dns_answer, dns_type
tls_sni, tls_version, ja3_hash
geoip_src_country, geoip_src_asn, geoip_dst_country, geoip_dst_asn
enrichment_vt_score, enrichment_abuse_score, enrichment_misp_matches
enrichment_epss_score, enrichment_cvss_score
analyst_verdict, analyst_assigned, analyst_notes
suppression_hit, escalation_level, playbook_outcome
cluster_id, campaign_id, attack_chain_stage

## SOC Reasoning fields (steps 1-8):

closure_reason, escalation_reason, suppression_reason
playbook_action, playbook_success, recommended_action, risk_adjusted_priority
maintenance_window, patch_window, known_admin_activity, vulnerability_scan
scheduled_backup, business_hours, weekend_activity, environment_context
asset_criticality, host_role, department, business_unit, owner_team, compliance_scope, asset_value
user_role, mfa_used, authentication_method, parent_process, process_hash, integrity_level, signed_binary
timeline_position, previous_alert_id, next_alert_id, session_id
repeated_behavior_score, similar_alerts_last_hour, attack_burst_id, alert_storm_id
historically_seen, historical_false_positive_rate, recurring_alert, prior_case_count

raw_log, extra_fields
```

---

## LLM Training Datasets

The pipeline produces 3 specialized LLM-ready datasets:

| Dataset | Content | Use Case |
|---------|---------|----------|
| `analyst_notes.json` | Alert + analyst reasoning chain | Fine-tune reasoning models |
| `suppression_reasons.json` | Alert + why it was suppressed | Train suppression classifiers |
| `escalation_decisions.json` | Alert + escalation outcome | Train escalation policy models |

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

**Attack generators (8):** `benign_traffic`, `malware`, `brute_force`,
`phishing`, `ddos`, `lateral_movement`, `privilege_escalation`, `noise_alerts`.

**Telemetry formatters (5):** Wazuh, Suricata, Zeek, Velociraptor, osquery.

Response:
```json
{
  "status": "generated",
  "campaign_id": "cmp-abc123",
  "total_events": 500,
  "distribution": { "malware": 50, "brute_force": 40 },
  "files_written": { "suricata": 3, "zeek": 3 },
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

---

### `GET /simulate/status`

Show current simulation configuration and generator state.

```json
{
  "campaign_id": "cmp-abc123",
  "distribution": { "malware": 0.10, "benign": 0.45 },
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

---

# External Integrations

| Service | Purpose | Rate Limit | Auth |
|---------|---------|------------|------|
| VirusTotal | IP/file reputation | 4 req/min | `VT_API_KEY` |
| AbuseIPDB | IP abuse confidence | Varies | `ABUSEIPDB_KEY` |
| MISP | Internal IOC matching | Instance-dep. | `MISP_KEY` |
| NVD | CVE details / CVSS scores | 6 req/sec | None |
| EPSS | Exploit probability | None | None |
| OpenSearch | Alert storage / query | N/A | Basic auth |
| TheHive | Case management | N/A | API key |
| Cortex | Automated response | N/A | Triggered by TheHive |
| CISA KEV | Known exploited vulns | N/A | Embedded in response |

---

# Environment Variables

| Variable | Description | Required | Sensitivity |
|----------|-------------|----------|-------------|
| `OS_HOST` | OpenSearch host URL | ✅ | MEDIUM |
| `OS_PORT` | OpenSearch port | ✅ | LOW |
| `OS_USER` | OpenSearch username | ✅ | HIGH |
| `OS_PASS` | OpenSearch password | ✅ | HIGH |
| `VT_API_KEY` | VirusTotal API key | ✅ | CRITICAL |
| `MISP_URL` | MISP instance URL | ✅ | MEDIUM |
| `MISP_KEY` | MISP API key | ✅ | CRITICAL |
| `ABUSEIPDB_KEY` | AbuseIPDB API key | Optional | HIGH |
| `OPENSEARCH_HOST` | Dataset pipeline OpenSearch host | Optional | MEDIUM |
| `OPENSEARCH_INDEX` | Dataset pipeline index name | Optional | LOW |
| `THEHIVE_URL` | TheHive instance URL | Optional | MEDIUM |
| `THEHIVE_API_KEY` | TheHive API key | Optional | HIGH |
| `MAX_DOWNLOAD_SIZE_MB` | Dataset download limit | Optional | LOW |
| `TOTAL_EVENTS_TARGET` | Pipeline target event count | Optional | LOW |

---

# Deployment

All services run on a shared Docker network `soc_net`. Service inventory:

| Group | Services | Purpose |
|-------|----------|---------|
| Backend | API, PostgreSQL, pgAdmin | Core logic, relational storage |
| SIEM/EDR | Wazuh Manager, Indexer, Dashboard, Agent | Host detection and alert indexing |
| Network Sensors | Suricata, Zeek | IDS and protocol metadata |
| Endpoint | Velociraptor | Deep inspection and live response |
| SOAR | TheHive, Cortex, Cassandra, ES, MinIO | Case mgmt, analysis, response |
| Threat Intel | MISP, MISP Modules, MySQL, Redis | IOC database and enrichment |

**Infrastructure maturity:** Docker Compose (current) → Kubernetes + Helm (planned).
Manual provisioning — Terraform/Ansible placeholders exist.

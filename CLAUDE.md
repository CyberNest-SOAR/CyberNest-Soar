# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CyberNestSoar is an AI-enhanced SOAR platform. It ingests security telemetry (Wazuh alerts, Zeek logs, Suricata alerts, Gmail phishing targets), enriches it via external threat intel APIs (VirusTotal, AbuseIPDB, MISP, NVD, EPSS), scores risk, and drives automated playbook decisions (isolate host, block IP, create case).

## Two Backend Services

There are **two separate FastAPI apps** in this repo:

### 1. Phishing Detection API (`backend/main.py`)
- **Purpose**: Ingest emails from Gmail or manual submission, classify as phishing/safe via ML
- **ML**: sklearn RandomForest + TF-IDF with enrichment features
- **Endpoints**: `POST /api/emails/sync`, `POST /api/emails`, `GET /api/emails`, `GET/POST /api/ai/classify/*`, `POST /api/ai/classify/{id}/feedback`
- **Key files**: `backend/app/ai/phishing_model.py`, `backend/app/services/email_service.py`, `backend/app/controllers/`
- **DB**: PostgreSQL (via `gmail_db.py`)

### 2. Unified Backend API (`backend/main.py`)
- **Purpose**: Expose phishing ingestion, email analysis, SOAR workflows, and RAG semantic query endpoints from a single backend.
- **Endpoints**: `POST /api/emails`, `GET /api/emails`, `GET /api/v1/alerts`, `POST /api/v1/risk-score/`, `POST /api/v1/playbooks/decision`, `POST /api/v1/threat-intel/lookup`, `/api/v1/rag/*`, etc.
- **Key files**: `backend/main.py`, `backend/app/services/vector_manager.py`, `backend/app/services/rag_service.py`, `backend/app/services/collector.py`, `backend/app/routers/*`
- **DB**: PostgreSQL (email/storage), OpenSearch (Wazuh alerts), Redis cache

## Architecture & Patterns

### Fail-Soft Parallel Enrichment
All external API calls (VT, AbuseIPDB, MISP, NVD, EPSS) use `asyncio.wait_for(timeout=5.0)` + `asyncio.gather(return_exceptions=True)`. One slow/offline upstream never blocks the pipeline. See `backend/app/soar_backend/services/intel.py`, `services/enrichment.py`.

### Data Flow
```
Sensors (Wazuh/Suricata/Zeek) → OpenSearch → Collector → Normalizer → Enrichment → Risk Score → Playbook Decision
Gmail API → EmailService → PhishingDetector → PostgreSQL → Feedback Loop
```

### CVE Extraction
`intel.py` scans alert descriptions for `CVE-\d{4}-\d{4,}` patterns, fetches EPSS and CVSS scores concurrently, stores max values on the alert.

## Key Docker Deployments

| File | What it runs |
|------|-------------|
| `docker-compose.root.yml` | Root orchestrator: all services (API, Wazuh, Suricata, Zeek, Velociraptor, TheHive, Cortex, MISP) |
| `docker-compose.yml` | Standalone MISP stack (MariaDB, Redis, ES, MISP app + worker) |
| `sensors/ndr/suricata/suricata1/` | Suricata IDS/IPS sensor |
| `sensors/ndr/zeek/` | Zeek network monitoring sensor |
| `sensors/edr/velociraptor/` | Velociraptor EDR sensor |
| `siem/wazuh/single-node/` | Wazuh SIEM (manager, indexer, dashboard) |

## Running the Project

```bash
# Start everything (root orchestrator)
docker compose -f docker-compose.root.yml up -d

# Start MISP standalone
docker compose up -d

# Run backend dev (unified API)
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Run tests
cd backend && python -m pytest tests/
```

## Environment Variables

Key vars (see `backend/app/config/settings.py` and `backend/app/soar_backend/core/config.py`):
- `OS_HOST`, `OS_AUTH` — OpenSearch connection
- `VT_API_KEY`, `ABUSE_KEY` — Threat intel API keys
- `MISP_URL`, `MISP_KEY` — MISP connection
- `WAZUH_URL`, `WAZUH_USER`, `WAZUH_PASS` — Wazuh API
- `DATABASE_URL` — PostgreSQL connection
- `JWT_SECRET` — API security

## Project Structure

```
backend/
  main.py                          # Phishing Detection API entrypoint
  Dockerfile
  app/
    ai/phishing_model.py           # sklearn RandomForest + TF-IDF detector
    client/gmail_api.py            # Google Gmail API wrapper
    config/settings.py             # Phishing API config
    config/logging_config.py
    controllers/emails.py          # Email CRUD endpoints
    controllers/classification.py  # AI classification & feedback endpoints
    models/email_models.py         # Pydantic schemas for email API
    repository/gmail_db.py         # PostgreSQL email persistence
    repository/feedback_repo.py    # Feedback CSV persistence
    services/email_service.py      # Email ingestion & analysis orchestration
    services/enrichment_service.py # Enrichment feature extraction (URLs, domains, etc.)
    soar_backend/
      main.py                      # SOAR Unified API entrypoint
      core/config.py               # SOAR backend config
      core/security.py
      routers/alerts.py            # Team 0: Wazuh alert fetching & enrichment
      routers/risk.py              # Team 1: Risk scoring
      routers/patch.py             # Team 2: Patch recommendations
      routers/filtering.py         # Team 3: Alert filtering/noise reduction
      routers/playbooks.py         # Team 4: Automated playbook decisions
      routers/intel.py             # Team 5: Threat intel lookups
      schemas/models.py            # UnifiedAlert + all Pydantic schemas
      services/collector.py        # OpenSearch/Wazuh/Velociraptor data ingestion
      services/enrichment.py       # VT, AbuseIPDB, MISP, NVD, EPSS lookups
      services/intel.py            # Intel enrichment orchestrator + CVE extraction
      services/risk.py             # Risk score calculation
      services/playbooks.py        # Playbook decision engine
      services/normalizer.py       # Wazuh hit → UnifiedAlert
      services/filtering.py
      services/patch.py
      utils/
sensors/
  ndr/suricata/                    # Suricata IDS with custom rules
  ndr/zeek/                        # Zeek with custom scripts (brute_force, ddos, phishing)
  edr/velociraptor/                # Velociraptor EDR
  edr/arkime/                      # Arkime (formerly Moloch)
siem/
  wazuh/single-node/               # Wazuh SIEM single-node deployment
  wazuh/multi-node/                # Wazuh SIEM multi-node deployment
services/
  orchestrator/thehive/            # TheHive, Cortex, MISP orchestration
playbooks/                         # Response playbook stage directories
```

## Testing

```bash
cd backend && python -m pytest tests/ -v
```

Tests use heuristic-only analysis (no ML artifacts required). See `backend/tests/test_detector.py`.
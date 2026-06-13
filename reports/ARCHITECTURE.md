# Architecture

## System Overview

CyberNestSOAR is a containerized security orchestration platform that ingests telemetry from multiple EDR and NDR sensors, processes it through a Wazuh-based SIEM pipeline, enriches it with threat intelligence, and surfaces actionable insights via a React dashboard and TheHive case management.

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            SENSORS                                      │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Suricata │ │  Zeek    │ │Velociraptor│ │  Arkime  │ │ osquery  │   │
│  │  (NDR)   │ │  (NDR)   │ │   (EDR)    │ │  (NDR)   │ │  (EDR)   │   │
│  └────┬─────┘ └────┬─────┘ └─────┬──────┘ └────┬─────┘ └────┬─────┘   │
│       │            │             │             │            │         │
│       ▼            ▼             ▼             ▼            ▼         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   INGESTION LAYER                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │
│  │  │ Wazuh Agent  │  │   Filebeat   │  │ Python Forwarders   │  │   │
│  │  │ (file mon.)  │  │ (direct)     │  │ (HTTP API)          │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │   │
│  └─────────┼──────────────────┼──────────────────────┼─────────────┘   │
└────────────┼──────────────────┼──────────────────────┼─────────────────┘
             │                  │                      │
             ▼                  ▼                      ▼
     ┌───────────────────────────────────────────────────────┐
     │                  PROCESSING LAYER                      │
     │  ┌─────────────────────────────────────────────────┐   │
     │  │               Wazuh Manager                     │   │
     │  │  ┌──────────┐ ┌──────────┐ ┌────────────────┐  │   │
     │  │  │ Remoted  │ │Analysisd │ │  Decoder/Rules │  │   │
     │  │  │ (1514/514│ │  (alert  │ │  Matching      │  │   │
     │  │  │   UDP)   │ │generation│ │  Engine        │  │   │
     │  │  └──────────┘ └──────────┘ └────────────────┘  │   │
     │  └─────────────────────────────────────────────────┘   │
     │                                                        │
     │  ┌─────────────────────────────────────────────────┐   │
     │  │           Backend API (FastAPI)                 │   │
     │  │  ┌──────────┐ ┌──────────┐ ┌────────────────┐  │   │
     │  │  │  Email   │ │  AI/ML  │ │  Enrichment    │  │   │
     │  │  │ Endpoints│ │ Endpoints│ │  Service       │  │   │
     │  │  └──────────┘ └──────────┘ └────────────────┘  │   │
     │  └─────────────────────────────────────────────────┘   │
     └───────────────────────────────────────────────────────┘
                          │
                          ▼
     ┌───────────────────────────────────────────────────────┐
     │                   STORAGE LAYER                        │
     │  ┌────────────────┐  ┌────────────────┐               │
     │  │    Wazuh       │  │   PostgreSQL   │               │
     │  │ Indexer/OpenSea│  │   (Backend)    │               │
     │  │   rch          │  │                │               │
     │  └────────┬───────┘  └────────────────┘               │
     └───────────┼───────────────────────────────────────────┘
                 │
                 ▼
     ┌───────────────────────────────────────────────────────┐
     │                  PRESENTATION LAYER                    │
     │  ┌────────────────┐  ┌────────────────┐               │
     │  │ Wazuh Dashboard│  │  React Frontend│               │
     │  │ (OpenSearch    │  │  (SOC UI)      │               │
     │  │  Dashboards)   │  │                │               │
     │  └────────────────┘  └────────────────┘               │
     │                                                        │
     │  ┌────────────────┐  ┌────────────────┐               │
     │  │    TheHive     │  │     MISP       │               │
     │  │ (Case Mgmt)    │  │ (Threat Intel) │               │
     │  └────────────────┘  └────────────────┘               │
     └───────────────────────────────────────────────────────┘
```

---

## Pipeline Details

### Ingestion Methods

| Method | Sensors | Transport | Destination |
|--------|---------|-----------|-------------|
| Wazuh Agent | Suricata, Zeek, Velociraptor, Arkime | TCP 1514 / UDP 514 | Wazuh Manager → analysisd → Indexer |
| Filebeat (direct) | Suricata eve.json, Zeek *.log | HTTPS 9200 | Wazuh Indexer (filebeat-* indices) |
| Python Forwarder | Suricata, Zeek, Arkime | HTTP API | Wazuh Indexer (cybernest-*-events indices) |

### Decoder Pipeline (Wazuh Analysisd)

```
Raw Log → Predecoding → Decoder Matching → Rule Matching → Alert Output
                │               │                  │              │
           Detect format   Match by prematch    Apply rules    Write to
           (JSON, syslog,  string (e.g.         (level ≥ 3     alerts.json
            command)       "^{"timestamp":")     generates      → Filebeat
                                                    alert)      → Indexer
```

### Custom Decoders

| File | Decoder | Prematch |
|------|---------|----------|
| `0475-suricata_decoders.xml` | suricata-eve | `^{"timestamp":` |
| `0476-velociraptor_decoders.xml` | velociraptor-json | `"log_type":"velociraptor"` |
| `0476-velociraptor_decoders.xml` | arkime-json | `"log_type":"arkime"` |
| `local_decoder.xml` | zeek-json | `^{"ts":` |
| `local_decoder.xml` | catch-all-json | `^{` |

### Custom Rules

| File | Rule IDs | Purpose |
|------|----------|---------|
| `0865-zeek_rules.xml` | 866001-866006 | Zeek network IDS |
| `0866-suricata_rules.xml` | 866101-866107 | Suricata alert/event types |
| `0867-velociraptor_rules.xml` | 100021-100033 | Velociraptor/Arkime severity |
| `local_rules.xml` | 100000-100044 | Custom rules (CVE, malware, severity) |

---

## Index Destinations

| Pipeline | Index Pattern | Source |
|----------|--------------|--------|
| Wazuh Agent → Manager | `wazuh-alerts-*` | All sensors via analysisd |
| Filebeat direct | `filebeat-*` | Suricata/Zeek raw JSON |
| Python forwarder | `cybernest-suricata-events` | Suricata via custom forwarder |
| Python forwarder | `cybernest-zeek-events` | Zeek via custom forwarder |
| Python forwarder | `cybernest-arkime-events` | Arkime via custom forwarder |

---

## AI/ML Pipeline

```
Raw Log / Email
      │
      ▼
┌─────────────────┐
│  ML Classifier  │  XGBoost / LightGBM / scikit-learn
│  (fast path)    │  → composite_score, model_label
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
High Conf.   Ambiguous
    │         │
    ▼         ▼
┌────────┐  ┌────────┐
│Auto    │  │  LLM   │  Ollama / Qdrant RAG
│Action  │  │Reasoner│  → contextual analysis
└────────┘  └───┬────┘
                │
                ▼
         ┌────────────┐
         │  Analyst   │
         │  Review    │
         └────────────┘
```

### Risk Scoring

The AI risk scoring engine produces a 0–100 score using:
- **CVSS** — base severity of identified CVEs
- **EPSS** — exploit probability scoring
- **SSVC** — stakeholder-specific vulnerability categorization
- **Asset Criticality** — business value of affected assets
- **Historical Context** — past incident patterns and outcomes

---

## Container Architecture

The system is fully containerized using Docker Compose with a layered extend pattern:

```
docker-compose.root.yml (full stack)
  ├── backend/infra/docker-compose.yml (API, PostgreSQL, pgAdmin)
  ├── siem/wazuh/single-node/docker-compose.yml (Manager, Indexer, Dashboard)
  ├── sensors/ndr/suricata/... (Suricata NDR)
  ├── sensors/ndr/zeek/... (Zeek NDR)
  ├── sensors/edr/velociraptor/... (Velociraptor EDR)
  └── services/orchestrator/thehive/docker-compose.yml (TheHive, Cortex, MISP)

docker-compose.yml (core stack, excludes sensors)
  ├── backend/infra/docker-compose.yml
  ├── siem/wazuh/single-node/docker-compose.yml
  └── services/orchestrator/thehive/docker-compose.yml
```

All services share the `soc_net` bridge network for inter-service communication.

---

## Port Mapping

| Service | Internal Port | External Port |
|---------|--------------|---------------|
| Wazuh Dashboard | 5601 | 8443 (root) / 443 (core) |
| Wazuh Indexer | 9200 | - |
| Wazuh Manager API | 55000 | - |
| Wazuh Agent | 1514 TCP / 514 UDP | - |
| Backend API | 8000 | 8000 |
| PostgreSQL | 5432 | - |
| pgAdmin | 5050 | 5050 |
| TheHive | 9000 | 9000 |
| Cortex | 9001 | - |
| MISP | 80/443 | 8080 |
| Cassandra | 9042 | - |
| OpenSearch (TheHive) | 9201 | - |
| MinIO | 9000/9001 | - |

---

## Credential Matrix

| Username | Password | Service |
|----------|----------|---------|
| `admin` | `SecretPassword` | Wazuh Indexer, Filebeat |
| `wazuh-wui` | `MyS3cr37P450r.*-` | Wazuh Dashboard → Manager API |
| `kibanaserver` | `kibanaserver` | OpenSearch Dashboards internal |
| `admin@thehive.local` | (configured in env) | TheHive |
| `admin@misp.local` | (configured in env) | MISP |

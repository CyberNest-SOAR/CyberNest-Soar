# CyberNestSoar — AI-Enhanced SOAR (Security Orchestration, Automation and Response)

<p align="center">
    <picture>
        <img width="200"" alt="CyberNestSOARlogo" src="https://github.com/user-attachments/assets/36cc11a3-9de5-495a-82e8-8047fa00488f" />
    </picture>
</p>


<p align="center">
  <a href="https://www.docker.com/">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</a>
<a href="https://thehive-project.org/">
  <img src="https://img.shields.io/badge/TheHive-FF9900?style=for-the-badge&logo=hive&logoColor=white" alt="TheHive">
</a>
<a href="https://www.elastic.co/what-is/cortex">
  <img src="https://img.shields.io/badge/Cortex-005571?style=for-the-badge&logo=cortex&logoColor=white" alt="Cortex">
</a>
<a href="https://wazuh.com/">
  <img src="https://img.shields.io/badge/Wazuh-00A9E0?style=for-the-badge&logo=wazuh&logoColor=white" alt="Wazuh">
</a>
<a href="https://zeek.org/">
  <img src="https://img.shields.io/badge/Zeek-0D5C63?style=for-the-badge&logo=zeek&logoColor=white" alt="Zeek">
</a>
<a href="https://www.velocidex.com/velociraptor/">
  <img src="https://img.shields.io/badge/Velociraptor-4B0082?style=for-the-badge&logo=velociraptor&logoColor=white" alt="Velociraptor">
</a>
<a href="https://suricata-ids.org/">
  <img src="https://img.shields.io/badge/Suricata-EF3B2D?style=for-the-badge&logo=suricata&logoColor=white" alt="Suricata">
</a>
<a href="https://attack.mitre.org/">
  <img src="https://img.shields.io/badge/MITRE_ATT%26CK-FF6600?style=for-the-badge" alt="MITRE ATT&CK">
</a>
<a href="https://fastapi.tiangolo.com/">  
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
</a>
</p>

<p align="center">
#  <strong>Security Orchestration Is A Symphony</strong> #
</p>


---

## Overview

CyberNestSoar is a next-generation, open-source SOAR (Security Orchestration, Automation and Response) platform that unifies multi-domain security signals into a centralized, event-driven orchestration engine. It integrates industry-leading tools across SIEM, EDR, NDR, threat intelligence, case management, and AI-powered analytics to eliminate tool fragmentation and alert fatigue in modern SOC operations.

The platform replaces rigid, static alerts with a dynamic ML-based risk scoring engine (XGBoost/LightGBM fused with CVSS, EPSS, and SSVC frameworks), applies dual-layer AI and LLM filtering to suppress false positives, and triggers autonomous containment for high-confidence threats while routing ambiguous cases for analyst review.

---

## Project Roadmap

### Milestone 1 — Core SOAR Integration (Completed)
| Capability | Tools |
|---|---|
| SIEM & Correlation | Wazuh, OpenSearch |
| Network Visibility | Zeek (metadata), Suricata (IDS/IPS), Arkime (packet capture) |
| Endpoint Monitoring & DFIR | Velociraptor, osquery |
| Incident Response & Case Management | TheHive, Cortex |
| Threat Intelligence Enrichment | CVSS, EPSS, SSVC, MISP, VirusTotal, URLhaus, AbuseIPDB, AlienVault OTX |
| Modular Microservices Architecture | Python & Node.js microservices, FastAPI, Docker |
| Standardized Data Exchange | STIX, OpenC2, OCA, JSON, CEF, LEEF |
| CI/CD Pipeline | Automated deployment, rule updates, and testing |

### Milestone 2 — AI Decision Support & Risk Scoring (In Progress)
ML models that replace static severity thresholds with dynamic risk scores based on asset criticality, threat intelligence, vulnerability context, and historical incidents.

### Milestone 3 — AI-Driven Patch Recommendation Engine (In Progress)
Intelligent vulnerability prioritization combining CVE data, host context, exploit likelihood, and business impact to recommend remediation actions.

### Milestone 4 — LLM-Based Log Filtration & Alert Optimization (In Progress)
Reducing alert fatigue by combining ML classification with LLM-powered reasoning, clustering, and alert summarization.

### Milestone 5 — Intelligent Automation Playbooks (Planned)
Transforming static response workflows into adaptive automation that adjusts actions based on risk score, confidence level, and analyst feedback.

---

## The SOC Lifecycle Loop

CyberNestSoar executes the complete defensive cycle, from initial ingest to post-incident learning:

| Phase | Description |
|---|---|
| **Detection** | Aggregates telemetry across distributed environments — EDR, NDR, and email. |
| **Enrichment** | Injects threat intelligence (CVSS, EPSS, MISP, VirusTotal) via automated API hooks. |
| **Triage** | AI-driven priority scoring (0–100) using XGBoost/LightGBM to eliminate noise. |
| **Response** | Immediate execution of automated IR playbooks — host isolation, connection drops, case creation. |
| **Learning** | Feedback loops that refine models based on analyst overrides and mitigated threats. |

---

## AI Integration

### AI Risk Scoring Engine
XGBoost/LightGBM classifier evaluating severity, exploit probability, asset value, and historical outcomes (score 0–100).

### Predictive Patch Recommendation
Tracks host inventories against exploit vectors to estimate time-to-exploit and enforce patching windows.

### Dual-Layer Log Filtering
ML pipeline drops verified background noise; LLM reasoning handles ambiguous anomalies with contextual summaries.

### Adaptive Autonomy Strategy
High-confidence threats trigger autonomous containment; borderline exceptions route to analyst validation loops.

---

## Infrastructure

CyberNestSoar is fully containerized with Docker, enabling deployment on-premises, in the cloud, or in hybrid environments with no vendor lock-in.

```bash
# Full deployment (all services including sensors)
docker compose -f docker-compose.root.yml up --detach

# Or minimal stack (core SIEM + SOAR only)
docker compose up --detach
```

### Deployed Services
| Service | Status |
|---|---|
| Wazuh Manager | SIEM correlation engine |
| Wazuh Indexer | OpenSearch analytics & storage |
| Backend API | FastAPI orchestration layer |
| TheHive | Incident case management |
| Cortex | Observable analysis & enrichment |
| MISP | Threat intelligence sharing |
| Suricata | Network IDS/IPS |
| Zeek | Network metadata extraction |
| Velociraptor | Endpoint DFIR |

---

## Tech Stack

| Component | Technologies | Purpose |
|---|---|---|
| Endpoint (EDR) | osquery, Velociraptor, Wazuh Agent | SQL-based auditing, DFIR artifact collection, endpoint telemetry |
| Network (NDR) | Zeek, Suricata, Arkime | Metadata extraction, signature IDS/IPS, packet session capture |
| SIEM Core | Wazuh Server, OpenSearch | Alert correlation, analytics, storage, indexing |
| Threat Intelligence | CVSS, EPSS, SSVC, MISP, VirusTotal, URLhaus, AbuseIPDB, AlienVault OTX | Exploit tracking, dynamic prioritization, IOC enrichment |
| Data Exchange Formats | STIX, OpenC2, OCA, JSON, CEF, LEEF | Standardized interoperability between security tools |
| Orchestration | Python & Node.js Microservices, FastAPI | Event-driven webhooks, playbook routing, REST API |
| Case Management | TheHive, Cortex | Incident lifecycle, collaborative workflows, observable scanning |
| AI Engine | Python (XGBoost, LightGBM, LLMs, scikit-learn) | Risk scoring, predictive response, log classification |
| Frontend | React, shadcn, Tailwind | Real-time SOC dashboard & visualization |
| Database | PostgreSQL, Redis, OpenSearch | Persistent storage, caching, analytics |
| Infrastructure | Docker, Docker Compose, Kong, NGINX | Vendor-agnostic containerization, API gateway |

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/CyberNest-SOAR/CyberNest-Soar.git
cd CyberNest-Soar

# Full deployment (all services including sensors)
docker compose -f docker-compose.root.yml up --detach

# Or minimal stack (core SIEM + SOAR only)
docker compose up --detach
```

### Access Points

| Service | URL | Credentials |
|---|---|---|
| Wazuh Dashboard | `https://localhost:8443` | `admin` / `SecretPassword` |
| Backend API | `http://localhost:8000` | — |
| API Docs (Swagger) | `http://localhost:8000/docs` | — |
| TheHive | `http://localhost:9000` | Configured in `.env` |
| MISP | `http://localhost:8080` | Configured in `.env` |

---

## Team

| Name | Role | Focus Area |
|---|---|---|
| Paula | SOAR Architect | Architecture, backend API, enrichment layer, pipeline integration |
| Momen | AI Team Lead / RAG Engineer | RAG system, vector search, Docker infrastructure, AI model integration |
| Ahmed | EDR & NDR Engineer | Arkime, Velociraptor, Filebeat, sensor deployment |
| Nayra | ML Engineer | ML model training, enrichment service, patch engine |
| Hanaa | NDR Engineer | Zeek, Suricata, Wazuh integration |
| Pavlly | AI/ML Engineer | Noise classifier, alert filtering, AI phishing model |
| Steven | Backend Developer | Phishing API, risk scoring, classification endpoints |
| Habiba | Frontend Developer | SOAR dashboard, reporting, API integration |
| Amir | Integration Engineer | Integration testing, Wazuh setup, cross-component testing |

---

## Documentation

| Document | Description |
|---|---|
| [Architecture](reports/ARCHITECTURE.md) | Full system architecture, pipeline mapping, data flow, port mapping |
| [Deployment](reports/DEPLOYMENT.md) | Prerequisites, installation, configuration, running, troubleshooting |
| [API Reference](reports/API.md) | Complete API reference — 140+ endpoints across 25 categories |

---

## License

See the [LICENSE](LICENSE) file for full terms. Non-commercial use (educational, academic, personal) is free and permitted. For commercial use, sponsoring, testing, or development collaboration, please contact the team.

> **Email:** cybernestsoar@gmail.com
> **Status:** Active development. Monitoring all incoming telemetry for anomalous signatures.

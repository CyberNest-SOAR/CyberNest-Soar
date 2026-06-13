# CyberNestSoar — AI-Enhanced SOAR Platform

<p align="center">
    <picture>
        <img width="200" alt="CyberNestSOARlogo" src="https://github.com/user-attachments/assets/36cc11a3-9de5-495a-82e8-8047fa00488f" />
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
  <strong>Security Orchestration Is A Symphony</strong>
</p>
<p align="center">
  <a href="README.md">📘 README</a> •
  <a href="reports/ARCHITECTURE.md">🏗️ ARCHITECTURE</a> •
  <a href="reports/DEPLOYMENT.md">🚀 DEPLOYMENT</a> •
  <a href="reports/API.md">⚡ API</a>
</p>

---

## Overview

CyberNestSOAR is a next-generation autonomous security operations platform that eliminates tool fragmentation and alert fatigue by unifying multi-domain security signals across endpoints, networks, and ingestion pipelines into a centralized, event-driven orchestration engine.

Built on a powerful open-source XDR-style framework, the platform replaces rigid legacy alerts with a dynamic machine learning risk-scoring engine (XGBoost / LightGBM) fused with CVSS, EPSS, and SSVC frameworks. A dual-layer AI and LLM filtering system suppresses false positives while routing high-confidence threats to autonomous containment actions.

### Key Capabilities

- **Multi-vector Detection:** EDR (osquery, Velociraptor, Wazuh Agent) + NDR (Zeek, Suricata, Arkime) signal aggregation
- **AI Risk Scoring:** XGBoost/LightGBM classifier evaluating vulnerability severity, exploit probability, asset value, and historical outcomes (score 0–100)
- **Dual-Layer Log Filtering:** ML pipeline drops verified noise; LLM handles ambiguous anomalies
- **Adaptive Autonomy:** High-confidence threats trigger autonomous containment; borderline cases route to analyst review
- **Case Management:** TheHive + Cortex integration for incident lifecycle tracking and observable scanning
- **Threat Intelligence:** CVSS, EPSS, SSVC, MISP, VirusTotal, AbuseIPDB, URLhaus, AlienVault OTX enrichment

---

## Quick Start

```bash
# Clone the repository (source code available on the source-code branch)
git clone https://github.com/CyberNest-SOAR/CyberNest-Soar.git

# Full deployment (all services)
docker compose -f docker-compose.root.yml up --detach

# Or minimal stack (core only)
docker compose up --detach
```

After startup:
- **Wazuh Dashboard:** `https://localhost:8443` (or port 443 on root compose)
- **Backend API:** `http://localhost:8000`
- **API Docs:** `http://localhost:8000/docs` (Swagger) / `http://localhost:8000/redoc` (ReDoc)
- **TheHive:** `http://localhost:9000`
- **MISP:** `http://localhost:8080`

> **Note:** The `source-code` branch contains the full source code, including the FastAPI backend, React frontend, sensor configurations, and pipeline scripts. See [reports/DEPLOYMENT.md](reports/DEPLOYMENT.md) for detailed setup instructions.

---

## Architecture Overview

```
SENSORS → COLLECTION → PROCESSING → STORAGE → UI/API
  │          │             │           │         │
  ├─ Suricata ─┤           │           │         │
  ├─ Zeek     ─┤           │           │         │
  ├─ Velociraptor ─── Wazuh Agent ─ Wazuh Manager ─ Indexer ─ Dashboard
  ├─ Arkime   ─┤     │                 (OpenSearch)
  ├─ osquery  ─┘     ├─ Filebeat ───────┘
  │                  └─ Python Forwarders (direct API)
  └─ Phishing Feed ───→ Backend API ──→ PostgreSQL
```

Three ingestion methods feed into Wazuh Indexer (OpenSearch):
1. **Wazuh Agent** — file monitoring, analysisd decoder/rules pipeline
2. **Filebeat** — direct log shipping
3. **Python Forwarders** — HTTP API-based event forwarding

See [reports/ARCHITECTURE.md](reports/ARCHITECTURE.md) for the complete architecture breakdown.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **EDR** | osquery, Velociraptor, Wazuh Agent |
| **NDR** | Zeek, Suricata, Arkime |
| **SIEM** | Wazuh Server, OpenSearch (Wazuh Indexer) |
| **Threat Intel** | CVSS, EPSS, SSVC, MISP, VirusTotal, AbuseIPDB, URLhaus, AlienVault OTX |
| **Orchestration** | Python microservices, FastAPI |
| **Case Management** | TheHive, Cortex |
| **AI/ML** | XGBoost, LightGBM, LLMs, scikit-learn |
| **Frontend** | React, shadcn, Tailwind CSS |
| **Database** | PostgreSQL, OpenSearch |
| **Infrastructure** | Docker, Docker Compose, Kong/NGINX |

---

## Documentation

| Document | Description |
|----------|-------------|
| [reports/ARCHITECTURE.md](reports/ARCHITECTURE.md) | Full system architecture, pipeline mapping, data flow |
| [reports/DEPLOYMENT.md](reports/DEPLOYMENT.md) | Prerequisites, installation, configuration, running |
| [reports/API.md](reports/API.md) | API endpoint reference, authentication, examples |

---

## Project Status

CyberNestSoar is currently under active development as part of the SOAR Project 1 at SUT. This public branch contains documentation and project overview. The full source code is maintained on the `source-code` branch.

### Team

| Name | Role |
|------|------|
| [Paula Maged](https://github.com/PM-CyberSec) | SOAR Architect & Team Lead |
| [Momen Saif](https://github.com/Momen959) | AI Team Lead / RAG Engineer |
| [Ahmed Ehab](https://github.com/ahmedtalaat1817) | EDR & NDR Engineer |
| [Nayra Ahmed](https://github.com/nayra-ahmedaraby) | ML Engineer |
| [Hanaa Ramadan](https://github.com/Hanaa159) | NDR Engineer |
| [Pavlly Sameh](https://github.com/Pevllo) | AI/ML Engineer |
| [Steven Wael](https://github.com/Steven-06) | Backend Developer |
| [Habiba Karam](https://github.com/HabibaKarm) | Frontend Developer |
| [Amir Khaled](https://github.com/amirkhaled23) | Integration Engineer |

---

## License

This project is for **educational purposes** as part of the SOAR Project 1 at SUT.
Feel free to use or adapt it for learning or non-commercial purposes.

---

### Security Notice

CyberNestSoar is currently under development. Monitoring all incoming telemetry for anomalous signatures in real-time. For security concerns, please open a GitHub issue.

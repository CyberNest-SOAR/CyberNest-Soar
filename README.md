# CyberNestSoar — AI-enhansed SOAR (Security Automation and Response)

<p align="center">
    <picture>
        <img width="803" height="572" alt="image" src="https://github.com/user-attachments/assets/8fd502a7-10b6-44a5-b5d4-be1360c351e8" />
    </picture>
</p>

<p align="center">
#  <strong>Security Orchestration Is A Simphony</strong> #
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

# 🛸 [ SYSTEM_MANIFEST: CyberNestSoar ]
```text

                 / \                CyberNestSOAR is a next-generation, autonomous security
                /   \               operations layer designed to eliminate the tool
               /  ^  \              fragmentation and alert fatigue paralyzing modern SOC
              /  / \  \             teams by seamlessly unifying multi-domain security
             /  /   \  \            signals across endpoints, networks, and ingestion
            /  /-/ \-\  \           pipelines into a centralized, event-driven orchestration
           /  /-/   \-\  \          engine. Built on a powerful open-source XDR-style
          /  /-/-- --\-\  \         framework, the platform introduces intelligent triaging
         /  /-/--\ /--\-\  \        that replaces rigid legacy alerts with a dynamic machine
        /__/      .      \__\       learning risk-scoring engine utilizing XGBoost and
                                    LightGBM models fused with the CVSS, EPSS, and SSVC
            CyberNestSOAR           frameworks. Furthermore, it leverages adaptive
      -------------------------     automation through a dual-layer AI and LLM filtering
       [ AI ENHANCED DEFENSE ]      system to suppress false positives, allowing
                                    high-confidence threats to trigger autonomous
                                    containment actions like rapid host isolation while
                                    seamlessly routing ambiguous data for analyst review.
                                    By orchestrating proven, high-performance industry tools
                                    like Wazuh, Zeek, Suricata, and TheHive, CyberNestSOAR
                                    delivers enterprise-grade, scalable defense pipelines
                                    with zero vendor lock-in. Ultimately, by replacing
                                    manual triage with intelligent execution loops, the
                                    platform drastically optimizes MTTD and MTTR, making
                                    enterprise-tier, self-executing security operations
                                    fully accessible to SMEs, MSSPs, and distributed modern
                                    enterprises.

        ## [ ⌬ ] MODULE_INVENTORY: TECH_STACK
        ## [ ⚡ ] TACTICAL_ORCHESTRATION
        ## [ 🧠 ] NEURAL_CORE_LOGIC
```

---

## ⚡ [ THE_SOC_LIFECYCLE_LOOP ]

CyberNestSoar executes the complete defensive cycle, from initial ingest to post-incident learning:

    DETECTION: Aggregates telemetry across distributed environments — EDR, NDR, and email.

    ENRICHMENT: Injects threat intelligence (CVSS, EPSS, MISP, VirusTotal) via automated API hooks.

    TRIAGE: AI-driven priority scoring (0–100) using XGBoost/LightGBM to eliminate "Log Headache".

    RESPONSE: Immediate execution of automated IR playbooks — host isolation, connection drops, case creation.

    LEARNING: Feedback loops that refine models based on analyst overrides and mitigated threats.



## 🧠 [ COGNITIVE_LAYERS (AI_INTEGRATION) ]

The system leverages advanced neural logic to act as a Force Multiplier for security teams:

    [ ⟁ ] AI RISK SCORING ENGINE: XGBoost/LightGBM classifier evaluating severity, exploit probability, asset value, and historical outcomes (score 0–100).

    [ ⌬ ] PREDICTIVE PATCH RECOMMENDATION: Tracks host inventories against exploit vectors to estimate time-to-exploit and enforce patching windows.

    [ ⚙ ] DUAL-LAYER LOG FILTERING: ML pipeline drops verified background noise; LLM reasoning handles ambiguous anomalies with contextual summaries.

    [ ⚡ ] ADAPTIVE AUTONOMY STRATEGY: High-confidence threats trigger autonomous containment; borderline exceptions route to analyst validation loops.



## ⬢ [ INFRASTRUCTURE_NODES ]

Because CyberNestSoar is Docker-based, it is not tethered to a single vendor. It can be deployed on-prem, in the cloud, or in hybrid environments with zero hardware friction.

    root@cybernest:~$ docker compose -f docker-compose.root.yml up --detach
    [+] Running 16/16
     ⠿ Container Wazuh_Manager      Healthy
     ⠿ Container Wazuh_Indexer      Healthy
     ⠿ Container Backend_API        Running
     ⠿ Container TheHive_CaseMgmt   Running
     ⠿ Container Cortex_Analyzers   Running
     ⠿ Container MISP_Intel         Running
     ⠿ Container Suricata_NDR       Running
     ⠿ Container Zeek_NDR           Running
     ⠿ Container Velociraptor_EDR   Running



## ⌬ [ MODULE_INVENTORY: TECH_STACK ]

| Component         | Technology                                        |         PROTOCOL / UTILITY                     |
| ----------------- | ------------------------------------------------- | ---------------------------------------------- |
| Endpoint (EDR)    | osquery / Velociraptor / Wazuh Agent              | SQL-based auditing, DFIR artifact collection, endpoint telemetry |
| Network (NDR)     | Zeek / Suricata / Arkime                          | Metadata extraction, signature IDS/IPS, packet session capture |
| SIEM Core         | Wazuh Server / OpenSearch                         | Alert correlation, analytics, storage, indexing |
| Threat Intel      | CVSS / EPSS / SSVC / MISP / VirusTotal / URLhaus / AbuseIPDB / AlienVault OTX | Exploit tracking, dynamic prioritization, IOC enrichment |
| Orchestration     | Python & Node.js Microservices / FastAPI          | Event-driven webhooks, playbook routing, REST API |
| Case Management   | TheHive / Cortex                                  | Incident lifecycle, collaborative workflows, observable scanning |
| AI Neural Engine  | Python (XGBoost / LightGBM / LLMs / scikit-learn) | Risk scoring, predictive response, log classification |
| Frontend          | React / shadcn / Tailwind                         | Real-time SOC dashboard & visualization |
| Database          | PostgreSQL / Redis / OpenSearch                   | Persistent storage, caching, analytics |
| Infrastructure    | Docker / Docker Compose / Kong / NGINX            | Vendor-agnostic containerization, API gateway |



## 🥷 [OPERATIONAL_STRIKE_TEAM]

| Name   | Tactical Title           | Tools & Modules                          | Tactical Responsibilities                      | Operational Description                                      |
|--------|--------------------------|------------------------------------------|------------------------------------------------|-------------------------------------------------------------|
| Paula  | SOAR Architect           | Wazuh, Suricata, Filebeat, TheHive, FastAPI, Docker, React | Architecture Design, Backend API, Enrichment Layer, Decoder/Rule Engineering, Pipeline Integration | Full SOAR pipeline integration (Wazuh/Suricata/Zeek/Velociraptor/Arkime); UI dashboard data pipeline |
| Momen  | AI Team Lead / RAG Engineer | Qdrant, Ollama, Docker, Python, LLMs, React | RAG System, Vector Search, Docker Infrastructure, AI Model Integration | RAG chatting system: semantic router, Qdrant + Ollama vector search, OpenSearch execution layer |
| Ahmed  | EDR & NDR Engineer       | Arkime, Velociraptor, Docker, Python, Filebeat | Sensor Deployment, Docker Config, API Integration | Arkime deployment & OpenSearch setup; Velociraptor EDR sensor templates; Filebeat integration |
| Nayra  | ML Engineer              | Scikit-learn, XGBoost, HistGradientBoosting, Python, Matplotlib | ML Model Training, Enrichment Service, Patch Engine | Phishing email model; patch engine models; ML pipeline visualization; enrichment service |
| Hanaa  | NDR Engineer             | Zeek, Suricata, Wazuh, Docker            | Sensor Configuration, Log Pipeline, Wazuh Integration | Suricata classified logs; Zeek configuration; Wazuh single-node integration |
| Pavlly | AI/ML Engineer           | Python, XGBoost, LLMs, Scikit-learn      | Noise Classifier, Alert Filtering, AI Phishing Model | ML noise classifier V2; AI phishing model; alert filtering router & tests |
| Steven | Backend Developer        | Python, XGBoost, FastAPI                 | Phishing Email API, Classification, Backend Endpoints | Phishing email API; risk scoring model; feedback & classification endpoints |
| Habiba | Frontend Developer       | React, shadcn, Tailwind                  | SOAR Dashboard, API Integration, UI Components | Initial SOAR dashboard; Reporting & Audit page; API endpoints |
| Amir   | Integration Engineer     | Wazuh, Python, Docker                    | Integration Testing, Wazuh Setup, Alert Injection | Integration Stack folder; Wazuh files setup; cross-component testing |



## Quick Start

```bash
# Clone the repository
git clone https://github.com/CyberNest-SOAR/CyberNest-Soar.git

# Full deployment (all services including sensors)
docker compose -f docker-compose.root.yml up --detach

# Or minimal stack (core SIEM + SOAR only)
docker compose up --detach
```

**Access Points:**

| Service | URL | Credentials |
|---------|-----|-------------|
| Wazuh Dashboard | `https://localhost:8443` | `admin` / `SecretPassword` |
| Backend API | `http://localhost:8000` | — |
| API Docs | `http://localhost:8000/docs` | Swagger UI |
| TheHive | `http://localhost:9000` | Configured in .env |
| MISP | `http://localhost:8080` | Configured in .env |



## Documentation

| Document | Description |
|----------|-------------|
| [reports/ARCHITECTURE.md](reports/ARCHITECTURE.md) | Full system architecture, pipeline mapping, data flow, port mapping |
| [reports/DEPLOYMENT.md](reports/DEPLOYMENT.md) | Prerequisites, installation, configuration, running, troubleshooting |
| [reports/API.md](reports/API.md) | Complete API reference — 140+ endpoints across 25 categories |



## 📟 License

This project is for **educational purposes** as part of the SOAR Project 1 at SUT.
Feel free to use or adapt it for learning or non-commercial purposes.



### [ SECURITY_NOTICE ] CyberNestSoar is currently under developement. Soon! Monitoring all incoming telemetry for anomalous signatures.

# CyberNestSoar — AI-Enhanced SOAR Platform

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
<p align="center">
  <a href="README.md">📘 README</a> •
  <a href="docs/pipelines.md">📡 PIPELINES</a> •
  <a href="docs/api.md">⚡ API</a> •
  <a href="docs/team_members_and_milestones.md">👥 TEAM</a> •
  <a href="docs/security.md">🔒 SECURITY</a>
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

CyberNestSoar transforms data from initial ingestion to post-incident reinforcement across five fully operational pipelines:

* **DETECTION (EDR & NDR):** Aggregates continuous multi-vector signals spanning endpoint system changes, deep packet inspections, and live phishing telemetry hooks.
* **ENRICHMENT & CONTEXT:** Ingests live vulnerability matrices and external intelligence feeds to reconstruct comprehensive threat scenarios automatically.
* **TRIAGE & CLASSIFICATION:** Replaces legacy "Log Headaches" with an advanced machine learning classification layer to isolate high-risk actions instantly.
* **RESPONSE EXECUTION:** Fires API-driven playbooks to isolate assets, drop malicious connections, and spin up cases programmatically without human delays.
* **FEEDBACK LEARNING:** Implements a direct loop to capture operational overrides, dynamically re-tuning machine learning models against local false positives.

---

## 🧠 [ COGNITIVE_LAYERS (AI_INTEGRATION) ]

The system moves beyond static if/else scripts, using layered neural logic to supercharge detection accuracy and incident response velocity:

* **[ ⟁ ] AI RISK SCORING ENGINE:** A supervised XGBoost and LightGBM classifier evaluating vulnerability severity, exploit probability, asset value, and historical outcomes to generate an objective risk score (0–100) that determines response priorities.
* **[ ⌬ ] PREDICTIVE PATCH RECOMMENDATION:** Tracks host inventories and incoming asset telemetry against active exploit vectors to estimate exact time-to-exploit metrics, enforcing precise, accelerated patching windows.
* **[ ⚙ ] DUAL-LAYER LOG FILTERING:** Uses a hyper-fast machine learning pipeline to drop verified background noise, calling upon higher-context LLM reasoning only when handling ambiguous or highly complex anomalies to provide clean structural summaries.
* **[ ⚡ ] ADAPTIVE AUTONOMY STRATEGY:** Grants full orchestrational logic based on threshold confidence. High-confidence critical events prompt real-time autonomous containments while borderline exceptions flag analysts via custom validation loops.

---

## ⬢ [ INFRASTRUCTURE_NODES ]

Because CyberNestSoar relies entirely on a containerized architecture, deployment bypasses dedicated hardware constraints. Scale seamlessly across cloud or internal networks with native microservices orchestration:

```bash
root@cybernest:~$ docker-compose up --detach
[+] Running 8/8
 ⠿ Container Wazuh_Manager      Healthy
 ⠿ Container AI_Decision_Engine Running
 ⠿ Container TheHive_CaseMgmt   Running
 ⠿ Container CyberNest_Core     Active
```

---

## ⌬ [ MODULE_INVENTORY: TECH_STACK ]

| Component | Technology | PROTOCOL / UTILITY |
| :--- | :--- | :--- |
| **Endpoint (EDR)** | osquery / Velociraptor / Wazuh Agent | Continuous SQL-based auditing, live DFIR artifact collection, and endpoint telemetry. |
| **Network (NDR)** | Zeek / Suricata / Arkime | Unstructured metadata extraction, signature-based IDS/IPS, and full packet session capture. |
| **SIEM Core** | Wazuh Server / OpenSearch | Real-time alert correlation engine paired with high-performance analytics, storage, and indexing. |
| **Threat Intel** | CVSS / EPSS / SSVC / MISP / VirusTotal / URLhaus / AbuseIPDB / AlienVault OTX | Exploit probability tracking, dynamic prioritization models, and automated IOC/reputation API enrichment. |
| **Orchestration Core** | Custom Python & Node.js Microservices | Event-driven webhook processing, playbook routing, and multi-service REST API control planes. |
| **Case Management** | TheHive / Cortex | Incident ticket lifecycle tracking, collaborative workflow spaces, and unified observable scanning. |
| **AI Neural Engine** | Python (XGBoost / LightGBM / LLMs) | Dynamic risk calculation, predictive response matrices, and high-context log classification. |
| **Monitoring** | Prometheus / Grafana | Centralized system telemetry monitoring, pipeline latency tracking, and operational dashboards. |
| **API Gateway** | Kong / NGINX | Centralized token validation (JWT), RBAC policy mapping, and ingress rate limiting. |

---

## 🥷 [OPERATIONAL_STRIKE_TEAM]


| Name | Tactical Title | Tools & Modules | Tactical Responsibilities | Recent Key Contributions |
| :--- | :--- | :--- | :--- | :--- |
| [**Paula Maged**](https://github.com/PM-CyberSec) | SOAR Architect & Cybersecurity Team Lead | `Wazuh`, `Suricata`, `Filebeat`, `TheHive`, `FastAPI`, `Docker`, `React`, `soar_backend API`, `enrichment layer` | Architecture Design, soar_backend API Development, Enrichment Layer Engineering, Decoder/Rule Engineering, Data Pipeline Orchestration, SOAR Pipeline Integration | Full SOAR pipeline integration (Wazuh/Suricata/Zeek/Velociraptor/Arkime); SOAR backend API & enrichment layer (VT, AbuseIPDB, MISP, EPSS, NVD, CISA KEV, URLhaus, AlienVault OTX); UI dashboard data pipeline & SOC reasoning bridge; API.md & SECURITY.md documentation; 144 total commits |
| [**Momen Saif**](https://github.com/Momen959) | AI Team Lead / RAG Engineer | `Qdrant`, `Ollama`, `Docker`, `Python`, `LLMs`, `React` | RAG System Architecture, Vector Search, Docker Infrastructure, AI Model Integration | RAG chatting system: semantic router, Qdrant + Ollama vector search, OpenSearch execution layer, indexer; Windows start_all.bat; caching system; AI model completion; Docker builds; 61 commits |
| [**Ahmed Ehab**](https://github.com/ahmedtalaat1817) | EDR & NDR Engineer | `Arkime`, `Velociraptor`, `Docker`, `Python`, `Filebeat` | Sensor Deployment, Docker Config, API Integration, Arkime/Velociraptor Pipeline | Arkime sensor deployment & OpenSearch setup; Velociraptor EDR sensor templates; Filebeat integration with Velociraptor logging; Docker compose fixes; 34 commits |
| [**Nayra Ahmed**](https://github.com/nayra-ahmedaraby) | ML Engineer | `Scikit-learn`, `XGBoost`, `HistGradientBoosting`, `Python`, `Matplotlib` | ML Model Training, Enrichment Service, Patch Engine, Visualization | Phishing email model enhancements & API connection (Wk 1-4); patch engine models & backend integration; ML pipeline visualization with cluster interpretations; enrichment service; performance metrics & graphs; 25 commits |
| [**Hanaa Ramadan**](https://github.com/Hanaa159) | NDR Engineer | `Zeek`, `Suricata`, `Wazuh`, `Docker` | Sensor Configuration, Log Pipeline, Wazuh Integration, Zeek Scripting | Suricata with classified logs; Zeek configuration updates; Wazuh single-node integration; dependency management; 19 commits |
| [**Pavlly Sameh**](https://github.com/Pevllo) | AI/ML Engineer | `Python`, `XGBoost`, `LLMs`, `Scikit-learn` | Noise Classifier, Alert Filtering, AI Phishing Model, Log Filtration | ML noise classifier V2 integration; AI phishing model updates; alert filtering router & tests; python path shadowing fix; 10 commits |
| [**Steven Wael**](https://github.com/Steven-06) | Backend Developer / Phishing API | `Python`, `XGBoost`, `FastAPI` | Phishing Email API, Classification, Backend Endpoints | Phishing email API (Wk 1-4, mostly completed); risk scoring model v1; backend endpoints (feedback, classification); response model updates; structural fixes; 10 commits |
| [**Habiba Karam**](https://github.com/HabibaKarm) | Frontend Developer | `React`, `shadcn`, `Tailwind` | SOAR Dashboard, API Integration, UI Components | Initial SOAR dashboard implementation; Reporting & Audit page enhancements; API endpoints; clean frontend setup; 9 commits |
| [**Amir Khaled**](https://github.com/amirkhaled23) | Integration Engineer | `Wazuh`, `Python`, `Docker` | Integration Testing, Validation Scripts, Wazuh Setup, Alert Injection | Integration Stack folder; Wazuh files setup; file uploads; cross-component testing; 6 commits |

---

## 📟 License

This project is for **educational purposes** as part of the SOAR Project 1 at SUT.  
Feel free to use or adapt it for learning or non-commercial purposes.

### [ SECURITY_NOTICE ] CyberNestSoar is currently under development. Monitoring all incoming telemetry for anomalous signatures in real-time. Soon!

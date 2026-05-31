# CyberNest-SOAR Codebase Report

## Project Overview
**CyberNest-SOAR** is a Security Orchestration, Automation, and Response (SOAR) system focused on phishing email detection. It combines a FastAPI backend, PostgreSQL database, AI/ML models, and security monitoring tools to automatically detect, analyze, and respond to phishing threats.

---

## 📁 Root Level Directories & Files

### Root Configuration Files
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Docker Compose configuration for containerized deployment |
| `.env.example` | Template for environment variables |
| `README.md` | Project documentation and setup guide |
| `LICENSE` | Project licensing information |

---

## 🔧 `/backend` - FastAPI Application Core
**Purpose**: Main application logic, API endpoints, AI model integration, and database operations.

### Backend Root Files
| File | Purpose |
|------|---------|
| `main.py` | Application entrypoint; initializes FastAPI app with routers and lifecycle management |
| `openAuth.py` | OAuth authentication logic for Google/Gmail integration |
| `requirements.txt` | Python dependencies (FastAPI, Pydantic, scikit-learn, joblib, Google APIs, etc.) |
| `Dockerfile` | Container image definition for backend service |

### Backend Subdirectories

#### `/backend/app` - Application Package
Core application modules organized by responsibility.

##### `/backend/app/ai` - Machine Learning & Phishing Detection
**Purpose**: Implements phishing detection using machine learning models.

| File | Purpose |
|------|---------|
| `phishing_model.py` | `SklearnDetector` class using RandomForest classifier; loads pre-trained model and TF-IDF vectorizer from disk artifacts |
| `train_model.py` | Model training script; trains RandomForest classifier on phishing email datasets |

##### `/backend/app/api` - API Layer
**Purpose**: Placeholder for additional API utilities (currently contains `.gitkeep`).

##### `/backend/app/client` - External Service Clients
**Purpose**: Integrations with external services.

| File | Purpose |
|------|---------|
| `gmail_api.py` | Gmail API client; handles Gmail authentication, email fetching, and synchronization |

##### `/backend/app/config` - Configuration Management
**Purpose**: Application configuration and logging setup.

| File | Purpose |
|------|---------|
| `settings.py` | Pydantic settings class; loads config from `.env` including database URL, model paths, Gmail settings, artifact locations |
| `logging_config.py` | Logging configuration; sets up structured logging across the application |

##### `/backend/app/controllers` - API Route Handlers
**Purpose**: FastAPI route handlers that define REST endpoints.

| File | Purpose |
|------|---------|
| `emails.py` | Email endpoints: `POST /api/emails/sync` (sync Gmail), `POST /api/emails` (submit email), `GET /api/emails` (list emails) |
| `classification.py` | Classification endpoints; handles phishing classification results and feedback |

##### `/backend/app/core` - Core Utilities
**Purpose**: Placeholder for core domain logic (currently empty with `.gitkeep`).

##### `/backend/app/models` - Pydantic Data Models
**Purpose**: Request/response data models and database schemas.

| File | Purpose |
|------|---------|
| `email_models.py` | Pydantic models: `EmailPayload`, `EmailAnalysis`, `EmailRecord`, `EmailCreateResponse`, `FeedbackPayload` for request/response validation |

##### `/backend/app/repository` - Data Access Layer
**Purpose**: Database operations and persistence.

| File | Purpose |
|------|---------|
| `gmail_db.py` | Database queries for email data (CRUD operations on email table) |
| `feedback_repo.py` | Database operations for user feedback on classifications |

##### `/backend/app/services` - Business Logic Layer
**Purpose**: Service layer orchestrating multiple operations.

| File | Purpose |
|------|---------|
| `email_service.py` | Main service: email validation, classification, Gmail sync, database persistence |
| `enrichment_service.py` | Email enrichment; extracts features from email content for analysis |

#### `/backend/artifacts` - ML Model Artifacts
**Purpose**: Persisted machine learning models.

| File | Purpose |
|------|---------|
| `phishing_model.joblib` | Serialized scikit-learn RandomForest classifier model |
| `tfidf_vectorizer.joblib` | Persisted TF-IDF vectorizer for text feature extraction |

#### `/backend/data` - Training & Feedback Data
**Purpose**: Datasets for model training and user feedback.

| File | Purpose |
|------|---------|
| `data.csv` | Training dataset for phishing detection model |
| `_training_buffer.csv` | Temporary buffer for training data |
| `feedback.csv` | Collected user feedback on classification accuracy |

#### `/backend/infra` - Infrastructure Configuration
**Purpose**: Container orchestration for backend.

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Docker Compose for backend services |

#### `/backend/logs` - Application Logs
**Purpose**: Runtime application logs and debugging information.

#### `/backend/tests` - Unit Tests
**Purpose**: Test suite for backend functionality.

| File | Purpose |
|------|---------|
| `test_detector.py` | Tests for phishing detection model accuracy |

---

## 📊 `/data` - Project-Level Data Management
**Purpose**: Centralized data storage for datasets and feedback.

| Subdirectory | Purpose |
|---|---|
| `/data/datasets` | Large datasets and data sources |
| `/data/feedback` | Centralized feedback collection |

---

## 📋 `/infra` - Infrastructure as Code
**Purpose**: Deployment and infrastructure configuration.

| Subdirectory | Purpose |
|---|---|
| `/infra/ansible` | Ansible playbooks for automated infrastructure provisioning |
| `/infra/ci-cd` | CI/CD pipeline configurations (GitHub Actions, GitLab CI, etc.) |
| `/infra/k8s` | Kubernetes manifests for container orchestration |
| `/infra/monitoring` | Monitoring stack configuration (Prometheus, Grafana, etc.) |
| `/infra/terraform` | Terraform IaC for cloud infrastructure |

---

## 📖 `/docs` - Documentation
**Purpose**: Project documentation and diagrams.

| Subdirectory | Purpose |
|---|---|
| `/docs/diagrams` | Architecture diagrams and visual documentation |

---

## 🎬 `/playbooks` - Automation Playbooks
**Purpose**: Ansible playbooks for SOAR response workflows.

| Subdirectory | Purpose |
|---|---|
| `/playbooks/detection_to_enrichment` | Playbook: Route detected phishing emails to enrichment service |
| `/playbooks/enrichment_to_remediation` | Playbook: Escalate enriched threats to remediation actions |
| `/playbooks/phishing_response` | Playbook: Complete phishing response workflow (detection → remediation) |

---

## 📡 `/sensors` - Security Monitoring Sensors
**Purpose**: Endpoint and network detection & response (EDR/NDR) tools.

### `/sensors/edr` - Endpoint Detection & Response
**Purpose**: Host-level threat detection.

|         Subdirectory        |                          Purpose                          |
|-----------------------------|-----------------------------------------------------------|
| `/sensors/edr/arkime`       | Arkime packet capture and analysis tool                   |
| `/sensors/edr/osquery`      | OSQuery endpoint monitoring and querying                  |
| `/sensors/edr/velociraptor` | Velociraptor digital forensics and incident response tool |

### `/sensors/ndr` - Network Detection & Response
**Purpose**: Network-level threat detection.

|      Subdirectory       |                       Purpose                       |
|-------------------------|-----------------------------------------------------|
| `/sensors/ndr/arkime`   | Arkime for full-packet network capture              |
| `/sensors/ndr/zeek`     | Zeek network monitoring and IDS (protocol analysis) |
| `/sensors/ndr/suricata` | Suricata IDS/IPS engine for traffic inspection      |

#### `/sensors/ndr/suricata/suricata-setup` - Suricata Configuration
**Purpose**: Suricata IDS deployment and configuration.

| File | Purpose |
|------|---------|
| `Dockerfile` | Container image for Suricata |
| `docker-compose.yml` | Suricata service orchestration |
| `setup.sh` | Initialization script for Suricata |
| `suricata.yaml` | Suricata configuration (rules engine, output, protocol detection) |

##### `/sensors/ndr/suricata/suricata-setup/suricata/rules` - Detection Rules
**Purpose**: IDS/IPS detection and classification rules.

| File | Purpose |
|------|---------|
| `suricata.rules` | Suricata detection rules (malware, C&C, exploit signatures) |
| `local.rules` | Custom local detection rules for organization-specific threats |
| `classification.config` | Rule severity and classification configuration |
| `test.pcap` | Test packet capture for rule validation |

##### `/sensors/ndr/suricata/suricata-setup/filebeat` - Log Shipping
**Purpose**: Ship Suricata logs to SIEM.

| File | Purpose |
|------|---------|
| `filebeat.yml` | Filebeat configuration for Suricata log forwarding |

---

## 🛠️ `/services` - Microservices
**Purpose**: Modular service components of the SOAR platform.

| Subdirectory | Purpose |
|---|---|
| `/services/enrichment` | Email/threat enrichment service (WHOIS, DNS, reputation checks) |
| `/services/feedback` | Feedback collection and processing service |
| `/services/phishing` | Dedicated phishing detection and response service |
| `/services/orchestrator/thehive` | TheHive integration for centralized case management |

---

## 🔍 `/siem` - Security Information & Event Management
**Purpose**: Centralized security monitoring and log analysis.

| Subdirectory | Purpose |
|---|---|
| `/siem/dashboards` | Pre-built SIEM dashboards for threat visualization |
| `/siem/opensearch` | OpenSearch configuration for log indexing and search |
| `/siem/wazuh` | Wazuh SIEM agent and manager configuration |

---

## 🧠 `/threatintel` - Threat Intelligence Integration
**Purpose**: Integration with external threat intelligence feeds.

| Subdirectory | Purpose |
|---|---|
| `/threatintel/misp` | MISP (Malware Information Sharing Platform) integration |
| `/threatintel/phishtank` | Phishtank phishing URL database integration |
| `/threatintel/urlhaus` | URLhaus malicious URL repository integration |

---

## 📦 `/artifacts` - Shared ML Artifacts
**Purpose**: Trained machine learning models accessible across services.

| File | Purpose |
|---|---|
| `phishing_model.joblib` | Serialized RandomForest phishing classifier |
| `tfidf_vectorizer.joblib` | TF-IDF vectorizer for text feature extraction |
| `confusion_matrix.png` | Model performance visualization |
| `class_distribution.png` | Training dataset class distribution visualization |

---

## 🏗️ Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                   CyberNest-SOAR Platform                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Backend (FastAPI)                                   │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ • Controllers: Email routes, Classification endpoints│   │
│  │ • Services: Email processing, Enrichment             │   │
│  │ • AI/ML: Phishing detection (RandomForest)           │   │
│  │ • Repository: Database layer (PostgreSQL)            │   │
│  │ • Client: Gmail API integration                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                             │                               │
│            ┌────────────────┼────────────────┐              │
│            │                │                │              │
│    ┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐       │
│    │  Sensors     │  │  SIEM       │  │ Threat Intel│       │
│    ├──────────────┤  ├─────────────┤  ├─────────────┤       │
│    │ • EDR        │  │ • Wazuh     │  │ • MISP      │       │
│    │ • NDR        │  │ • OpenSearch│  │ • Phishtank │       │
│    │ • Suricata   │  │ • Dashboards│  │ • URLhaus   │       │
│    │ • Zeek       │  │             │  │             │       │
│    │ • Arkime     │  │             │  │             │       │
│    └──────────────┘  └─────────────┘  └─────────────┘       │
│            │                │                │              │
│            └────────────────┼────────────────┘              │
│                             │                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Orchestration & Response (Playbooks)                │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ • Detection → Enrichment → Remediation               │   │
│  │ • Automated phishing response workflows              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Technologies & Tools

| Category | Tools |
|---|---|
| **Backend** | FastAPI, Python, Pydantic |
| **Database** | PostgreSQL |
| **ML/AI** | scikit-learn, TF-IDF, RandomForest |
| **Email Integration** | Gmail API, Google OAuth |
| **EDR** | Arkime, OSQuery, Velociraptor |
| **NDR** | Suricata, Zeek, Arkime |
| **SIEM** | Wazuh, OpenSearch |
| **Threat Intel** | MISP, Phishtank, URLhaus |
| **Orchestration** | Ansible |
| **Infrastructure** | Docker, Terraform |

---

## 📊 Data Flow

```
Gmail Inbox
    │
    ├─→ [Gmail API Client] ──→ Email Sync
    │
    └─→ [Manual Submission] ──→ POST /api/emails
                                    │
                                    ▼
                        [Email Validation & Enrichment]
                                    │
                                    ▼
                    [Phishing Detection Model (RandomForest)]
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
                  SPAM           PHISHING        CLEAN
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                                    ▼
                        [Store in PostgreSQL]
                                    │
                                    ▼
                        [User Feedback Collection]
                                    │
                                    ▼
                        [Threat Response Playbooks]
```

---

## 💾 Database Schema (Conceptual)

|          Table           |                 Purpose                  |
|--------------------------|------------------------------------------|
|         `emails`         | Email records with analysis results      |
|        `feedback`        | User feedback on classification accuracy |
| `classification_results` | Detailed classification outputs          |
|        `threats`         | Identified threats and indicators        |

---

## 🚀 Deployment Architecture

- **Container Orchestration**: Docker Compose
- **CI/CD**: Automated testing and deployment pipelines
- **Infrastructure**: Terraform-managed cloud resources
- **Monitoring**: SIEM dashboards with real-time threat visualization

---

## 📝 Summary

CyberNest-SOAR is a comprehensive security platform that:
1. **Detects** phishing emails via ML models and heuristics
2. **Enriches** threats with external intelligence (WHOIS, reputation)
3. **Logs** security events via NDR/EDR sensors and SIEM
4. **Responds** through automated Ansible playbooks
5. **Learns** from user feedback to improve detection models

The architecture separates concerns across specialized services while maintaining centralized orchestration and monitoring.

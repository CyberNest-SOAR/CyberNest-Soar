# CyberNest SOAR

**CyberNest SOAR** (Security Orchestration, Automation, and Response) integrates open-source EDR, NDR, SIEM, and AI-driven enrichment tools into a unified automation framework.

### Architecture Highlights
- Modular layered design: EDR, NDR, SIEM, SOAR, Enrichment, AI
- Integrated tools: Wazuh, Zeek, Suricata, Velociraptor, OpenSearch, TheHive, Cortex
- AI layer: ML classifier for alert prioritization & phishing detection
- CI/CD: Helm, Docker Compose, GitHub Actions ready

### Quick Start
```bash
docker-compose up -d


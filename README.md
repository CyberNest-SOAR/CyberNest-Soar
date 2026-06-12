# CyberNestSoar — AI-Enhanced SOAR Platform

> **⌬ BRANCH: `cyber`** — Active development branch. All sensor integration, Wazuh pipeline, backend enrichment, and AI model work.

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
<a href="https://www.nist.gov/">
  <img src="https://img.shields.io/badge/NIST_IR-003366?style=for-the-badge" alt="NIST IR">
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

---

## Active Development

This branch contains the latest active development work on sensor integration, Wazuh SIEM pipeline configuration, backend enrichment services, and AI model improvements.

### Key Areas
* **Sensor Integration** — Suricata, Zeek, Velociraptor, Arkime pipeline testing
* **Wazuh Configuration** — Custom decoders, rules, and filebeat pipelines
* **Backend Enrichment** — VirusTotal, AbuseIPDB, MISP, EPSS, NVD, CISA KEV, URLhaus, AlienVault OTX
* **AI Models** — Risk scoring, noise classification, patch recommendation engine



## 📟 License

This project is for **educational purposes** as part of the SOAR Project 1 at SUT.
Feel free to use or adapt it for learning or non-commercial purposes.



### [ SECURITY_NOTICE ] CyberNestSoar is currently under developement. Soon! Monitoring all incoming telemetry for anomalous signatures.

## **RAG System Integration (Semantic Router & Text-to-Query)**

This project now includes a local, containerized Semantic Router and Text-to-Query system that allows security analysts to ask natural-language questions which are routed to the correct data source (PostgreSQL or OpenSearch), translated to executable queries by a local LLM, executed, and then synthesized into an analyst-friendly summary.

**What was added & where**
- **Docker services:** Qdrant (vector DB) and Ollama (local LLM) — see [backend/infra/docker-compose.yml](backend/infra/docker-compose.yml)
- **Config:** RAG configuration in [backend/app/config/settings.py](backend/app/config/settings.py) and [backend/app/soar_backend/core/config.py](backend/app/soar_backend/core/config.py)
- **Schema seed:** Semantic schema docs in [backend/app/core/router_seed.py](backend/app/core/router_seed.py)
- **Vector manager:** Qdrant + Ollama lifecycle in [backend/app/services/vector_manager.py](backend/app/services/vector_manager.py)
- **Query generator:** LCEL routing engine in [backend/app/services/query_generator.py](backend/app/services/query_generator.py)
- **RAG service:** Business logic (execution + synthesis) in [backend/app/soar_backend/services/rag_service.py](backend/app/soar_backend/services/rag_service.py)
- **Router:** Thin API router in [backend/app/soar_backend/routers/rag.py](backend/app/soar_backend/routers/rag.py)
- **Docs:** Full user guide in `RAG_SYSTEM.md` at repo root
- **Deps:** LangChain, Qdrant, Ollama packages added to [backend/requirements.txt](backend/requirements.txt)

Quick overview:
- User asks a natural-language question to `/api/v1/rag/query`.
- The LCEL engine retrieves schema context from Qdrant and uses Ollama to generate a structured query (SQL or OpenSearch DSL).
- The service executes the query against PostgreSQL or OpenSearch (OpenSearch currently stubbed) and synthesizes results with Ollama.

Getting started (local dev)

1) Start the Docker stack (root orchestrator)

On macOS / Linux (Bash):

```bash
./run_all.sh
```

On Windows (Command Prompt / PowerShell), run the helper batch:

```bat
start_all.bat
```

If you prefer to run Docker Compose directly, the equivalent command is:

```bash
docker compose -f docker-compose.root.yml up -d --build || docker compose -f backend/infra/docker-compose.yml up -d --build
```

2) Ensure the RAG services are running and pull required models into the Ollama container (one-time)

On Unix:

```bash
# Pull embeddings model
docker compose exec ollama ollama pull nomic-embed-text

# Pull LLM used for routing (example)
docker compose exec ollama ollama pull llama3:8b-instruct
```

On Windows, use the batch helper to start services and then:

```bat
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull llama3:8b-instruct
```

If `docker compose exec` fails (service name differs), run `docker compose ps` to find the container name and use `docker exec -it <container> ollama pull <model>` instead.

3) Install backend Python deps and run the unified backend API (dev):

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

> Note: The backend now runs as a single unified app from `backend/main.py`, exposing both email ingestion routes and `/api/v1/rag/*`.

4) Test the RAG endpoint (example):

```bash
curl -X POST http://localhost:8001/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all critical incidents from the last 24 hours"}'
```

Response fields:
- `routed_query` — structured routing output (target_db, target_source, executable_query, reasoning)
- `raw_results` — the rows/documents returned by the target database
- `formatted_answer` — LLM-synthesized analyst summary

Troubleshooting
- If Qdrant or Ollama fail to initialize, the SOAR API will still start; RAG endpoints will return errors until the services are back up. Check container logs:

```bash
docker compose logs qdrant
docker compose logs ollama
```

- If `ollama pull` fails due to permissions or network, run the command on the host where the Ollama daemon runs or increase container memory.

Notes & Next Steps
- The OpenSearch execution path is currently a stub returning mock results; replace the stub with `opensearch-py` calls in [backend/app/soar_backend/services/rag_service.py](backend/app/soar_backend/services/rag_service.py) to query your cluster.
- The ingestion pipeline should be extended to upsert alerts/logs into Qdrant for improved routing accuracy (not yet wired). See `RAG_SYSTEM.md` for detailed development guidance.

If you'd like, I can open a branch, run the stack locally, and exercise the endpoint end-to-end. Tell me whether you want me to run the containers and perform a live test now.

# Semantic Router & RAG System

## Overview

The CyberNest-Soar RAG (Retrieval-Augmented Generation) system provides a **natural language interface** to your security infrastructure. Users ask questions in plain English, and the system automatically:

1. **Routes** the query to the correct database (PostgreSQL or OpenSearch)
2. **Generates** precise SQL or OpenSearch DSL queries using a local LLM
3. **Executes** the query safely
4. **Synthesizes** results into a clear analyst summary

All processing is **fully local and offline** using Ollama and Qdrant—no data leaves your network.

---

## Architecture

### Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Qdrant** | Vector database storing schema metadata | Container on port 6333 |
| **Ollama** | Local LLM for query generation & synthesis | Container on port 11434 |
| **Vector Manager** | Lifecycle and bootstrap logic | `app/services/vector_manager.py` |
| **Query Generator** | LCEL semantic routing engine | `app/services/query_generator.py` |
| **RAG Router** | FastAPI endpoints | `app/soar_backend/routers/rag.py` |
| **Router Seed** | Database schema metadata | `app/core/router_seed.py` |

### Data Flow

```
User Query
    ↓
[Query Generation Engine]
    ↓
[Vector Similarity Search] → Retrieve schema context from Qdrant
    ↓
[LLM (Ollama)] → Generate SQL/DSL query
    ↓
[Route Based on target_db]
    ├─ PostgreSQL → Execute SQL → Return rows
    └─ OpenSearch → Execute DSL → Return hits
    ↓
[LLM Synthesis] → Format answer
    ↓
Analyst Summary
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Backend running via `./run_all.sh` or `./run_backend.sh`

### Step 1: Start Services

```bash
# Start the full stack (includes Qdrant + Ollama)
./run_all.sh

# Or backend-only
./run_backend.sh
```

The compose file will start:
- PostgreSQL (db)
- Redis (cache)
- Qdrant (vector store)
- Ollama (local LLM)
- SOAR API (FastAPI)

### Step 2: Download LLM Models (One-time)

Once Ollama is running, download the models:

```bash
# Download embedding model
docker exec -it soar_ollama ollama pull nomic-embed-text

# Download LLM model
docker exec -it soar_ollama ollama pull llama3:8b-instruct
```

This caches models locally so they don't re-download.

### Step 3: Query the RAG Endpoint

```bash
curl -X POST http://localhost:8001/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all critical incidents from the last 24 hours",
    "limit": 10
  }'
```

**Response:**

```json
{
  "routed_query": {
    "target_db": "postgresql",
    "target_source": "incidents",
    "executable_query": "SELECT * FROM incidents WHERE severity = 'critical' AND created_at > NOW() - INTERVAL '24 hours' LIMIT 10",
    "reasoning": "User is asking for critical incidents within a time window, which is best answered by the PostgreSQL incidents table."
  },
  "raw_results": [
    {
      "id": 123,
      "severity": "critical",
      "status": "open",
      "description": "...",
      "created_at": "2024-06-08T12:00:00"
    }
  ],
  "formatted_answer": "Found 3 critical incidents in the past 24 hours. All are currently open and require analyst attention. The most recent was created at 2024-06-08 12:00:00 UTC."
}
```

---

## API Endpoints

### POST `/api/v1/rag/query`

**Request:**

```json
{
  "query": "What are the top IPs contacted by host 192.168.1.100 in the last hour?",
  "filters": null,
  "limit": 10
}
```

**Response:**

```json
{
  "routed_query": {
    "target_db": "opensearch",
    "target_source": "suricata-logs-*",
    "executable_query": "{ ... OpenSearch DSL ... }",
    "reasoning": "..."
  },
  "raw_results": [ ... ],
  "formatted_answer": "..."
}
```

### GET `/api/v1/rag/health`

Check RAG system status:

```bash
curl http://localhost:8001/api/v1/rag/health
```

**Response:**

```json
{
  "status": "healthy",
  "vector_store": "ready",
  "llm_model": "llama3:8b-instruct",
  "embedding_model": "nomic-embed-text"
}
```

---

## Configuration

Settings are in:
- `backend/app/soar_backend/core/config.py` (SOAR backend)
- `backend/app/config/settings.py` (Phishing API)

Key variables:

```python
QDRANT_URL = "http://qdrant:6333"
QDRANT_COLLECTION = "cybernest_router"
OLLAMA_BASE_URL = "http://ollama:11434"
EMBEDDING_MODEL = "nomic-embed-text"
ROUTING_LLM_MODEL = "llama3:8b-instruct"
```

All configurable via `.env`:

```bash
QDRANT_URL=http://localhost:6333
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
ROUTING_LLM_MODEL=llama3:8b-instruct
```

---

## Schema & Seeding

Database schemas are defined in `app/core/router_seed.py` and automatically seeded into Qdrant on startup.

**Current schemas:**

1. **PostgreSQL: Incidents & Cases**
   - Tables: incidents, playbooks, users, case_assignments, feedback
   - Use for: historical queries, case management, playbook performance

2. **OpenSearch: Network Logs**
   - Indices: suricata-logs-*, zeek-logs-*, wazuh-alerts-*
   - Use for: threat hunting, IoC lookups, real-time alerts

3. **PostgreSQL: Threat Intelligence**
   - Tables: threat_intel_cache, iocs
   - Use for: reputation queries, enrichment validation

To add new schemas, edit `router_seed.py` and restart the application.

---

## Example Queries

### Incident Management

```bash
curl -X POST http://localhost:8001/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many critical incidents were resolved in the last 7 days?"
  }'
```

### Network Threat Hunting

```bash
curl -X POST http://localhost:8001/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all DNS requests to suspicious domains in the last hour"
  }'
```

### Analyst Metrics

```bash
curl -X POST http://localhost:8001/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is analyst Bob'\''s case closure rate this month?"
  }'
```

---

## Troubleshooting

### Qdrant Not Responding

```bash
# Check Qdrant health
curl http://localhost:6333/health

# View Qdrant logs
docker logs soar_qdrant
```

### Ollama Models Not Found

```bash
# List available models
docker exec soar_ollama ollama list

# Pull missing model
docker exec soar_ollama ollama pull llama3:8b-instruct
```

### LLM Timeout

If Ollama is slow, check:
- Memory available on host
- CPU/GPU resources
- Container logs: `docker logs soar_ollama`

Increase model timeout in `QueryGenerationEngine.__init__()`:

```python
self.llm = ChatOllama(
    model=settings.ROUTING_LLM_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=0.0,
    num_ctx=4096,
    # Add timeout parameter if available in your version
)
```

---

## Performance Tips

1. **Index Selectively:** Only index critical logs and alerts; don't index all raw logs.
2. **Chunk Wisely:** Default chunk size is 512–2048 tokens. Adjust in `query_generator.py` if needed.
3. **Cache Schema:** Schema documents are cached in Qdrant; rarely change.
4. **Parallelize Queries:** Use background tasks for slow OpenSearch searches.
5. **Monitor Qdrant:** Check point count periodically; prune old documents if needed.

---

## Advanced: Custom LLMs

To use a different LLM with Ollama:

1. Pull the model:
   ```bash
   docker exec soar_ollama ollama pull mistral:latest
   ```

2. Update config:
   ```bash
   ROUTING_LLM_MODEL=mistral:latest
   ```

3. Restart the app.

---

## Security Notes

- **No External Calls:** All processing is local; no data sent to external APIs.
- **Network Isolation:** Qdrant and Ollama run inside the Docker network.
- **Query Safety:** Generated SQL is NOT sanitized; rely on database ACLs.
- **PII Handling:** Don't store raw PII in schema descriptions; use anonymized metadata.

---

## Future Enhancements

- [ ] Feedback loop: capture user corrections and retrain routing models
- [ ] Multi-hop queries: chain queries across multiple databases
- [ ] Cost estimation: predict query execution time before running
- [ ] Query caching: cache frequent queries to speed up repeats
- [ ] Advanced filtering: support complex metadata filters in requests
- [ ] RBAC: role-based access control for different query types
- [ ] Query audit log: track all executed queries for compliance

---

## Support

For issues or questions:
1. Check logs: `docker logs soar_soar_api`
2. Test connectivity: `curl http://localhost:8001/api/v1/rag/health`
3. Review `QueryGenerationEngine` output in startup logs


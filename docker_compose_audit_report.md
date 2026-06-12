# CyberNest-Soar — Complete Docker Compose Audit Report

## Phase 1: Service Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           docker-compose.root.yml                           │
│                   (Primary SOAR Stack — soc_net / wazuh / cortex)           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ BACKEND ──────────────────────────┐  ┌─ SIEM (Wazuh) ────────────────┐ │
│  │  db (postgres:15)        :5433     │  │  wazuh.manager      1514/1515 │ │
│  │  api (soar_api)          :8000     │  │  wazuh.indexer      9200      │ │
│  │  pgadmin                 :5050     │  │  wazuh.dashboard    443→5601  │ │
│  └────────────────────────────────────┘  │  wazuh.agent                  │ │
│                                          └───────────────────────────────┘ │
│  ┌─ NDR SENSORS ────────────────────┐  ┌─ EDR ──────────────────────────┐ │
│  │  suricata1        (host mode)    │  │  velociraptor    8889/8000     │ │
│  │  zeek             (host mode)    │  └────────────────────────────────┘ │
│  └────────────────────────────────────┘                                    │
│  ┌─ SOAR/ORCHESTRATOR ──── ✗ MISSING ─┐  ┌─ THREAT INTEL ─── ✗ MISSING ─┐ │
│  │  cassandra          (thehive/*)    │  │  misp_mysql       (thehive/*) │ │
│  │  thehive_elasticsearch (thehive/*) │  │  redis             (thehive/*) │ │
│  │  minio               (thehive/*)   │  │  misp              (thehive/*) │ │
│  │  cortex              (thehive/*)   │  │  misp_modules      (thehive/*) │ │
│  │  thehive             (thehive/*)   │  └────────────────────────────────┘ │
│  └────────────────────────────────────┘                                    │
│                                                                             │
│  Networks: soc_net(bridge), wazuh(bridge), cortex(bridge)                   │
│  Volumes: postgres_data, wazuh_*, filebeat_*, miniodata, cassandradata,     │
│           elasticsearchdata, thehivedata, mispsqldata                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                       docker-compose.yml (MISP Stack)                       │
│                    (Separate stack — MISCONNECTED)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  mariadb:3306 → misp → misp-worker    │  Networks: default only             │
│  redis:6379             │  elasticsearch:9200                              │
│  Volumes: misp_db_data, misp_redis_data, misp_es_data, misp_app_data,       │
│           misp_gpg                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐  ┌──────────────────────────────────┐
│  dataset_pipeline/           │  │  simulation_engine/             │
│  dataset-pipeline    :8003   │  │  simulation-engine      :8002   │
│  Networks: dataset-net       │  │  Networks: simulation-net       │
└──────────────────────────────┘  └──────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                sensors/ (Standalone sensor deployments)                     │
├──────────────┬──────────────┬──────────────┬───────────────────────────────┤
│ suricata1    │ zeek         │ velociraptor │ arkime                        │
│ (host mode)  │ (host mode)  │ :8889,:8000  │ opensearch, arkime-viewer     │
│              │              │              │ arkime-capture, arkime-init   │
│              │              │              │ :8005                         │
└──────────────┴──────────────┴──────────────┴───────────────────────────────┘
```

---

## Phase 2 & 3: Issue Detection Table

| # | Severity | Component | File | Issue | Root Cause | Recommended Fix |
|---|----------|-----------|------|-------|------------|-----------------|
| 1 | **CRITICAL** | Orchestrator | `docker-compose.root.yml:109-186` | 9 services (`cassandra`, `thehive_elasticsearch`, `minio`, `cortex`, `thehive`, `misp_mysql`, `redis`, `misp`, `misp_modules`) reference `services/orchestrator/thehive/docker-compose.yml` which does NOT exist | The file was never created or was deleted; directory is empty (only `.gitkeep` present) | Create `services/orchestrator/thehive/docker-compose.yml` with the required service definitions, or remove extends from root compose |
| 2 | **CRITICAL** | Velociraptor / API | `sensors/edr/velociraptor/docker-compose.yml:7` and `backend/infra/docker-compose.yml:27` | Port 8000 is bound by both `velociraptor` (host:8000→container:8000) and `api` (host:8000→container:8000) causing port conflict | Both services expose port 8000 on the same host interface | Change velociraptor's host port to 8001 (`"8001:8000"`) or change the API host port |
| 3 | **HIGH** | MISP / SOAR | `docker-compose.yml` vs `docker-compose.root.yml` | MISP stack (mariadb, redis, elasticsearch, misp, misp-worker) is completely isolated — no shared networks with SOAR, no interconnectivity | Two separate compose files with no `extends` or network attachment between them | Either: (a) merge MISP services into root compose and attach to `soc_net`, or (b) create a shared external network both stacks join |
| 4 | **HIGH** | Suricata-setup | `sensors/ndr/suricata/suricata-setup/docker-compose.yml:25-27` | Hardcoded absolute paths referencing `/home/omen212/soar-project/...` for SSL certificates | Developer-specific paths committed to repo | Replace with relative paths: `../../../siem/wazuh/single-node/config/...` |
| 5 | **HIGH** | Wazuh | `siem/wazuh/single-node/docker-compose.yml:128,145` | `suricata-filebeat` and `zeek-filebeat` use non-standard image `wazuh-filebeat:4.14.4` — this image does not exist in any public registry | Custom image that was never built or documented | Replace with `docker.elastic.co/beats/filebeat:7.17.13` (as used in suricata-setup) or build the custom image and document it |
| 6 | **HIGH** | Wazuh Agent | `siem/wazuh/wazuh-agent/docker-compose.yml:7` | `WAZUH_MANAGER_SERVER=<WAZUH_MANAGER_IP>` uses a placeholder IP | Placeholder never replaced with actual value | Use `WAZUH_MANAGER=wazuh.manager` like in other agent configs, or add proper env variable documentation |
| 7 | **HIGH** | Integration Stack | `Integration_Stack/suricata1/docker-compose.yml:13` | Hardcoded network interface `ens33` in suricata command | Developer's specific interface hardcoded | Use `${SURICATA_NIC}` env variable with default |
| 8 | **HIGH** | Root Compose | `docker-compose.root.yml:196-198` | Networks `wazuh` and `cortex` are declared but NO services are attached to them; all services attach to `soc_net` only | Misconfigured network topology — `extends` replaces child's networks, not merges them | Attach Wazuh services to `wazuh` network and cortex/thehive services to `cortex` network; ensure `soc_net` bridges them |
| 9 | **HIGH** | Arkime | `sensors/ndr/arkime/docker-compose.arkime.yml:15,27,43` | Three services use `image: arkime:local` but there is NO build section to create this image | Missing build configuration that would produce the `arkime:local` image | Add build section pointing to a Dockerfile, or replace with a public image |
| 10 | **MEDIUM** | Networks | `docker-compose.root.yml:193-199` | `wazuh` network name collides with `single-node_wazuh` network created by child compose files when run independently | Root compose declares `wazuh` network but child files create `single-node_wazuh` (because compose names network after project name) | Make root compose's `wazuh` network `external: true` with `name: wazuh`, or use `name: wazuh` explicitly in all child files |
| 11 | **MEDIUM** | Volumes | `docker-compose.root.yml:203-227` | Only `postgres_data` volume is declared; `wazuh_api_configuration`, `wazuh_etc`, etc. are declared but NOT the Child compose's actual volume names — Docker Compose `extends` does NOT inherit volumes from the parent extends reference | When using `extends`, the volumes declared in the child service must match exactly; but child's volumes get project-prefixed names | Declare all named volumes from child compose files at root level, or use `external: true` volumes |
| 12 | **MEDIUM** | Port Conflicts | Multiple files | `wazuh.indexer` exposes `9200:9200` in both `siem/wazuh/single-node/` and `sensors/ndr/arkime/docker-compose.arkime.yml` (opensearch) | Both Wazuh indexer and Arkime OpenSearch use Elasticsearch-compatible API on port 9200 | If both run simultaneously, move one to alternate port (e.g., `9201:9200`) or ensure they never run concurrently |
| 13 | **MEDIUM** | Wazuh duplicate | `siem/wazuh/single-node/` vs `siem/dashboards/single-node/` | Both compose files define `wazuh.manager`, `wazuh.indexer`, `wazuh.dashboard` with same ports (1514, 1515, 514/udp, 55000) | Duplicate Wazuh stack configurations that would conflict if both deployed | Document that these are alternatives (not to be run together), or consolidate into a single source of truth |
| 14 | **MEDIUM** | Healthchecks | `siem/wazuh/single-node/docker-compose.yml` | `wazuh.manager`, `wazuh.indexer`, `wazuh.dashboard` have NO healthcheck defined | Missing healthcheck configurations | Add healthchecks to all Wazuh services (e.g., `wazuh.manager`: `curl -u foo:bar -k https://localhost:55000`) |
| 15 | **MEDIUM** | depends_on | `docker-compose.root.yml:18` | `api` depends_on `db` without `condition: service_healthy` | Missing health condition; service may start before DB is ready | Change to `depends_on: db: condition: service_healthy` |
| 16 | **LOW** | .env | `.env` | Only contains Supabase variables; no Docker-related environment variables | Docker configuration variables scattered across compose files | Add `POSTGRES_PASSWORD`, `WAZUH_PASSWORD`, `API_PASSWORD`, `SURICATA_NIC`, etc. to `.env` |
| 17 | **LOW** | Deprecated | `dataset_pipeline/docker-compose.yml:1`, `simulation_engine/docker-compose.yml:1` | `version: "3.8"` is obsolete in Docker Compose v2 and can be removed | Using legacy compose file format | Remove `version:` line from both files |
| 18 | **LOW** | Duplicate restart | `Integration_Stack/soar/velociraptor/docker-compose.yml:17-18` | `restart: always` appears twice in the same service | Editing error | Remove duplicate `restart: always` |
| 19 | **LOW** | Network name | `docker-compose.root.yml:198` | `cortex` network is declared explicitly but never used by any service | Leftover or intended for future TheHive stack | Either attach Cortex/TheHive services to it, or remove the unused network declaration |
| 20 | **LOW** | Single-node vs Setup | `sensors/ndr/suricata/suricata-setup/docker-compose.yml` vs `sensors/ndr/suricata/suricata1/docker-compose.yml` | Two different Suricata setups (`jasonish/suricata:latest` vs custom `build: .`). The root compose extends only `suricata1` variant | Multiple sensor implementations without clear which is production | Consolidate to one variant or clearly document usage |

---

## Phase 4: Pipeline Verification

### SOAR Data Flow Analysis

```
Sensor → SIEM → Orchestrator → Classification → Response → Output
```

| Stage | Producer | Consumer | Path | Port | Network | Status |
|-------|----------|----------|------|------|---------|--------|
| Sensor→SIEM | suricata/zeek/velociraptor | wazuh.agent | Filebeat log mount → Wazuh agent | N/A (bind mount) | Shared filesystem | ⚠️ Filebeat configs referenced in `/tmp/filebeat-configs/` — files may not exist |
| SIEM→Orchestrator | wazuh.manager | cortex/thehive | Webhook/API | 55000 (Wazuh API) | Should be soc_net | ❌ Orchestrator services missing entirely |
| SIEM→Classifier | wazuh.indexer | API (soar_api) | Query ES | 9200 | soc_net → ??? | ❌ API doesn't reference wazuh.indexer |
| Orchestrator→Response | thehive/cortex | (response engine) | Cortex API | Unknown | cortex | ❌ Missing components |
| Response→Output | (various) | pgadmin/dashboard | Various | Various | Various | ❌ Undefined |

### Critical Pipeline Breakages

1. **Sensor Alerts → SIEM**: Bind-mount-based (filebeat monitors sensor logs). Works if filebeat configs exist at `/tmp/filebeat-configs/`.
2. **SIEM → Orchestrator**: Complete gap — no TheHive/Cortex stack exists.
3. **SIEM → SOAR API**: No mechanism connects Wazuh to the API service. Missing API integrations.
4. **SOAR API → Database**: Functional (Postgres with healthcheck dependency).
5. **End-to-end pipeline**: BROKEN at orchestration layer.

---

## Phase 5: End-to-End Testing Assessment

| Test | Scenario | Expected | Actual | Status |
|------|----------|----------|--------|--------|
| 1 | Sample sensor alert | Reaches SIEM → Orchestrator → Classifier → Response | ❌ Orchestrator layer missing entirely | BLOCKED |
| 2 | Noise alert | Noise classifier processes, suppression works | ❌ No classification pipeline exists | BLOCKED |
| 3 | Malicious alert | Full escalation, response engine triggers | ❌ No escalation path exists | BLOCKED |

**Verdict on E2E**: Cannot execute any end-to-end test — the orchestration layer (TheHive + Cortex) is absent.

---

## Phase 6: Auto-Fix Recommendations

### Fix 1: Missing TheHive/Cortex Docker Compose (CRITICAL)

**File**: `services/orchestrator/thehive/docker-compose.yml` (must be CREATED)

**Issue**: 9 services in root compose reference this non-existent file.

**Corrected YAML** (create the file):

```yaml
services:
  cassandra:
    image: cassandra:4.1
    container_name: thehive-cassandra
    environment:
      - CASSANDRA_CLUSTER_NAME=TheHiveCluster
      - CASSANDRA_COMPACTION_THROUGHPUT_MBPS=16
    volumes:
      - cassandradata:/var/lib/cassandra
    healthcheck:
      test: ["CMD", "cqlsh", "-e", "describe cluster"]
      interval: 30s
      timeout: 10s
      retries: 10

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.12
    container_name: thehive-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    volumes:
      - elasticsearchdata:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9200 >/dev/null || exit 1"]
      interval: 20s
      timeout: 10s
      retries: 5

  minio:
    image: minio/minio:RELEASE.2023-06-09T07-32-20Z
    container_name: thehive-minio
    command: ["server", "/data"]
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - miniodata:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 5

  cortex.local:
    image: thehiveproject/cortex:4.0.1
    container_name: cortex
    depends_on:
      elasticsearch:
        condition: service_healthy
    environment:
      - CORTEX_ELASTICSEARCH_URIS=http://elasticsearch:9200
      - CORTEX_JOB_DIRECTORY=/opt/cortex/jobs
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9001/api/status"]
      interval: 30s
      timeout: 10s
      retries: 10

  thehive:
    image: thehiveproject/thehive:5.2.2
    container_name: thehive
    depends_on:
      cassandra:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy
      minio:
        condition: service_started
      cortex.local:
        condition: service_healthy
    environment:
      - HIVE_CORTEX_URLS=http://cortex:9001
      - HIVE_ELASTICSEARCH_URIS=http://elasticsearch:9200
    volumes:
      - thehivedata:/opt/thp/data
    ports:
      - "9000:9000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000"]
      interval: 30s
      timeout: 10s
      retries: 10

  misp_mysql:
    image: mariadb:10.11
    container_name: misp-mariadb
    environment:
      MYSQL_ROOT_PASSWORD: ${MISP_DB_ROOT_PASSWORD:-CHANGE_THIS_ROOT_PW}
      MYSQL_DATABASE: misp
      MYSQL_USER: misp
      MYSQL_PASSWORD: ${MISP_DB_PASSWORD:-CHANGE_THIS_DB_PW}
    volumes:
      - mispsqldata:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:6-alpine
    container_name: misp-redis
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - mispredisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  misp.local:
    image: harvarditsecurity/misp:2.4
    container_name: misp
    depends_on:
      misp_mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DB_HOST: misp_mysql
      DB_PORT: 3306
      DB_NAME: misp
      DB_USER: misp
      DB_PASS: ${MISP_DB_PASSWORD:-CHANGE_THIS_DB_PW}
      REDIS_HOST: redis
      MISP_FQDN: ${MISP_FQDN:-misp.local}
    volumes:
      - mispdata:/var/www/MISP
    ports:
      - "8080:80"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost/ >/dev/null || exit 1"]
      interval: 20s
      timeout: 10s
      retries: 5

  misp-modules:
    image: harvarditsecurity/misp-modules:2.4
    container_name: misp-modules
    depends_on:
      misp.local:
        condition: service_healthy
    restart: unless-stopped

volumes:
  miniodata:
  cassandradata:
  elasticsearchdata:
  thehivedata:
  mispsqldata:
  mispdata:
  mispredisdata:
```

**Impact of fix**: Restores thehive, cortex, minio, cassandra, elasticsearch, and MISP pipeline — unblocks 9 blocked services.

---

### Fix 2: Resolve Port Conflict (CRITICAL)

**File**: `sensors/edr/velociraptor/docker-compose.yml:6-7`

**Lines**: `- "8889:8889"` and `- "8000:8000"`

**Why wrong**: Port 8000 is also used by `soar_api` from `backend/infra/docker-compose.yml:27`.

**Fixed snippet**:
```yaml
    ports:
      - "8889:8889"
      - "8001:8000"
```

**Impact**: Eliminates port conflict; velociraptor accessible on port 8001.

---

### Fix 3: Hardcoded SSL Paths (HIGH)

**File**: `sensors/ndr/suricata/suricata-setup/docker-compose.yml:25-27`

**Current**:
```yaml
      - /home/omen212/soar-project/CyberNest-Soar/siem/wazuh/single-node/config/wazuh_indexer_ssl_certs/root-ca.pem:/etc/ssl/root-ca.pem:ro
      - /home/omen212/soar-project/CyberNest-Soar/siem/wazuh/single-node/config/wazuh_indexer_ssl_certs/admin.pem:/etc/ssl/filebeat.pem:ro
      - /home/omen212/soar-project/CyberNest-Soar/siem/wazuh/single-node/config/wazuh_indexer_ssl_certs/admin-key.pem:/etc/ssl/filebeat.key:ro
```

**Fixed**:
```yaml
      - ../../../siem/wazuh/single-node/config/wazuh_indexer_ssl_certs/root-ca.pem:/etc/ssl/root-ca.pem:ro
      - ../../../siem/wazuh/single-node/config/wazuh_indexer_ssl_certs/admin.pem:/etc/ssl/filebeat.pem:ro
      - ../../../siem/wazuh/single-node/config/wazuh_indexer_ssl_certs/admin-key.pem:/etc/ssl/filebeat.key:ro
```

**Impact**: Makes deployment portable across machines.

---

### Fix 4: Non-standard Wazuh Filebeat Image (HIGH)

**File**: `siem/wazuh/single-node/docker-compose.yml:128,145`

**Current**: `image: wazuh-filebeat:4.14.4`

**Issue**: This image doesn't exist in Docker Hub or any standard registry.

**Option A** — Use official filebeat:
```yaml
  suricata-filebeat:
    image: docker.elastic.co/beats/filebeat:7.17.13
```

**Option B** — Build it with a Dockerfile and reference:
```yaml
  suricata-filebeat:
    build:
      context: ./filebeat
      dockerfile: Dockerfile
```

**Impact**: Resolves image pull failures at deployment time.

---

### Fix 5: Arkime Missing Build (HIGH)

**File**: `sensors/ndr/arkime/docker-compose.arkime.yml:15,27,43`

**Current**: `image: arkime:local`

**Fix**: Add build configuration:
```yaml
  arkime-init:
    build:
      context: .
      dockerfile: Dockerfile.arkime
    image: arkime:local
```

Or replace with a public Arkime image if available.

**Impact**: Allows Arkime services to be built and deployed.

---

### Fix 6: API depends_on Without Health Condition (MEDIUM)

**File**: `docker-compose.root.yml:18-21`

**Current**:
```yaml
  api:
    depends_on:
      - db
```

**Fixed**:
```yaml
  api:
    depends_on:
      db:
        condition: service_healthy
```

**Impact**: Prevents API startup race condition with database.

---

### Fix 7: Wazuh Healthchecks (MEDIUM)

**File**: `siem/wazuh/single-node/docker-compose.yml`

**Missing**: Healthchecks on `wazuh.manager`, `wazuh.indexer`, `wazuh.dashboard`

**Add to wazuh.manager**:
```yaml
    healthcheck:
      test: ["CMD", "curl", "-sf", "--connect-timeout", "5", "https://localhost:55000"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 120s
```

**Add to wazuh.indexer**:
```yaml
    healthcheck:
      test: ["CMD-SHELL", "curl -s https://localhost:9200/ -u admin:SecretPassword -k >/dev/null || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
```

**Add to wazuh.dashboard**:
```yaml
    healthcheck:
      test: ["CMD-SHELL", "curl -s -o /dev/null -w '%{http_code}' http://localhost:5601/status | grep -q 200 || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
```

**Impact**: Enables proper depends_on condition chains and Docker health monitoring.

---

### Fix 8: Network Integration (HIGH)

**File**: `docker-compose.root.yml:193-199`

**Issue**: Services attached only to `soc_net` but Wazuh services need the `wazuh` network.

**Fix**: Remove unused network declarations and attach all services to `soc_net`, ensuring child compose services also connect to `soc_net`:
```yaml
services:
  wazuh.manager:
    extends:
      file: siem/wazuh/single-node/docker-compose.yml
      service: wazuh.manager
    networks:
      - soc_net

networks:
  soc_net:
    driver: bridge
    name: soc_net
```

And change the Wazuh child compose file network to reference `soc_net` as external:
```yaml
networks:
  wazuh:
    name: soc_net
    external: true
```

**Impact**: All services can communicate across the unified `soc_net` network.

---

### Fix 9: Deprecated `version` Key (LOW)

**Files**: `dataset_pipeline/docker-compose.yml:1`, `simulation_engine/docker-compose.yml:1`

**Fix**: Remove `version: "3.8"` line from both files.

**Impact**: Eliminates warning messages; cleaner config.

---

### Fix 10: Duplicate `restart` (LOW)

**File**: `Integration_Stack/soar/velociraptor/docker-compose.yml:17-18`

**Fix**: Remove duplicate line:
```yaml
    restart: always
```

---

## Phase 7: Deployment Readiness Score

### Score: 32 / 100

| Category | Score | Rationale |
|----------|-------|-----------|
| **Compose Integrity** | 2/10 | Root compose references non-existent file — 9 services unresolvable |
| **Networking** | 4/10 | Networks declared but misconfigured; child compose network names don't match root expectations |
| **Service Discovery** | 3/10 | Hostnames inconsistent; no mechanism for services to discover each other across stacks |
| **Environment Configuration** | 3/10 | Passwords hardcoded; no .env for Docker; placeholder variables not replaced |
| **Pipeline Connectivity** | 2/10 | Complete gap at orchestration layer; no TheHive/Cortex; MISP isolated |
| **Runtime Stability** | 5/10 | Missing healthchecks on critical services; missing depends_on conditions |
| **End-to-End Functionality** | 0/10 | Cannot execute any E2E test — pipeline irreparably broken at orchestration layer |

---

## Phase 8: Final Verdict

# ❌ NOT READY FOR DEPLOYMENT

### Why

1. **9 services unresolvable** — The entire orchestration layer (TheHive + Cortex + supporting services + MISP) is missing because `services/orchestrator/thehive/docker-compose.yml` doesn't exist.
2. **Port conflict** — Velociraptor and SOAR API both want port 8000.
3. **Hardcoded paths** — Developer-specific filesystem paths break deployment on any other machine.
4. **Non-existent images** — Custom `wazuh-filebeat` and `arkime:local` images are referenced but never built.
5. **No pipeline integration** — The SOAR data flow is broken at every stage beyond raw sensor ingestion.
6. **Missing healthchecks** — Wazuh services have no health checks, risking false "healthy" states.
7. **Network isolation** — MISP stack on separate compose with no connectivity to the main SOAR stack.

### Required Fixes Before Deployment

1. **Create** `services/orchestrator/thehive/docker-compose.yml` (Fix 1 above) — unblocks 9 services.
2. **Resolve** port conflict on 8000 between velociraptor and API (Fix 2).
3. **Replace** hardcoded `/home/omen212/...` paths (Fix 3).
4. **Either build or replace** `wazuh-filebeat` and `arkime:local` images (Fix 4, 5).
5. **Restore** network connectivity — unify under `soc_net` or bridge appropriately (Fix 8).
6. **Add** healthchecks to all Wazuh services (Fix 7).
7. **Fix** `depends_on` conditions to use `service_healthy` (Fix 6).
8. **Consolidate** .env with all required Docker variables (Fix 16).
9. **Merge or interconnect** the MISP stack with the main SOAR network.
10. **Remove** duplicate/alternative compose files or document them clearly as alternatives, not co-deployable stacks.

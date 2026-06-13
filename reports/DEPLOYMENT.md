# Deployment Guide

## Prerequisites

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 16 GB | 32 GB |
| Disk | 100 GB SSD | 200 GB+ SSD |
| Network | 1 Gbps | 10 Gbps (for sensor data) |

### Software Requirements

- **Docker** ≥ 24.0
- **Docker Compose** ≥ 2.20 (or Docker Engine with Compose plugin)
- **Git** (to clone the repository)
- **Make** (optional, for convenience commands)

### Operating System Support

- Linux (Ubuntu 22.04+, Debian 12+, RHEL 9+)
- macOS (Docker Desktop)
- Windows (Docker Desktop with WSL2)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/CyberNest-SOAR/CyberNest-Soar.git
cd CyberNest-Soar
```

The source code is on the `source-code` branch. Switch to it if you need the full source:

```bash
git checkout source-code
```

### 2. Environment Configuration

Copy the example environment file and configure as needed:

```bash
cp .env.example .env
```

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `soar_user` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `soar_pass` | PostgreSQL password |
| `POSTGRES_DB` | `soar_db` | PostgreSQL database name |
| `SECRET_KEY` | (random) | JWT signing key |
| `VT_API_KEY` | - | VirusTotal API key |
| `ABUSEIPDB_API_KEY` | - | AbuseIPDB API key |
| `MISP_URL` | `http://misp:80` | MISP instance URL |
| `MISP_API_KEY` | - | MISP API key |

### 3. Certificate Generation (Wazuh Indexer)

The Wazuh Indexer requires TLS certificates for secure communication. Generate them with:

```bash
docker compose -f siem/wazuh/single-node/generate-indexer-certs.yml up
```

This creates SSL certificates in `siem/wazuh/single-node/config/wazuh_indexer_ssl_certs/`.

### 4. System Tuning

Increase system limits for packet capture sensors:

```bash
# Elasticsearch / OpenSearch requirements
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -w vm.max_map_count=262144
```

---

## Deployment

### Full Stack (All Services)

Deploys every component including NDR/EDR sensors:

```bash
docker compose -f docker-compose.root.yml up --detach
```

Services started: Backend API, PostgreSQL, Wazuh Manager/Indexer/Dashboard, Suricata, Zeek, Velociraptor, TheHive, Cortex, MISP, and supporting infrastructure.

### Core Stack (SIEM + SOAR + Backend)

Deploys the essential services without network sensors:

```bash
docker compose up --detach
```

Services started: Backend API, PostgreSQL, Wazuh Manager/Indexer/Dashboard, TheHive, Cortex, MISP.

### Individual Components

Each component can be started independently for development:

```bash
# Backend only
docker compose -f backend/infra/docker-compose.yml up --detach

# Wazuh SIEM only
docker compose -f siem/wazuh/single-node/docker-compose.yml up --detach

# TheHive + Cortex only
docker compose -f services/orchestrator/thehive/docker-compose.yml up --detach
```

---

## Post-Deployment Configuration

### 1. Verify Services

```bash
# Check all running containers
docker compose ps

# View logs
docker compose logs -f api          # Backend API
docker compose logs -f wazuh.manager  # Wazuh Manager
docker compose logs -f thehive       # TheHive
```

### 2. Access Dashboards

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Wazuh Dashboard | `https://localhost:8443` | `admin` / `SecretPassword` |
| Backend API | `http://localhost:8000` | - |
| Swagger Docs | `http://localhost:8000/docs` | - |
| ReDoc | `http://localhost:8000/redoc` | - |
| TheHive | `http://localhost:9000` | Configured in env |
| MISP | `http://localhost:8080` | Configured in env |
| pgAdmin | `http://localhost:5050` | Configured in env |

### 3. Configure Wazuh Agent

To enroll a Wazuh agent for endpoint monitoring:

```bash
# On the target endpoint (Linux):
WAZUH_MANAGER_IP="<manager-ip>"
curl -sO https://packages.wazuh.com/4.x/wazuh-agent-4.14.0-1.amd64.deb
sudo dpkg -i wazuh-agent-4.14.0-1.amd64.deb
sudo sed -i "s/MANAGER_IP/$WAZUH_MANAGER_IP/g" /var/ossec/etc/ossec.conf
sudo systemctl start wazuh-agent
```

---

## Running the Frontend (Development)

The React-based SOC dashboard requires Node.js:

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

The frontend connects to the backend API at `http://localhost:8000` by default. Configure via `VITE_API_URL` environment variable.

---

## Running the Dataset Pipeline

The dataset generation pipeline produces synthetic security telemetry:

```bash
cd dataset_pipeline
pip install -r requirements.txt

# Generate synthetic SOC dataset
python main.py --mode generate --output ./data/outputs

# Export to OpenSearch
python main.py --mode export --opensearch-host localhost:9200
```

---

## Maintenance

### Backups

```bash
# Backup PostgreSQL database
docker exec -t cybernest-db-1 pg_dump -U soar_user soar_db > backup_$(date +%Y%m%d).sql

# Backup Wazuh Indexer indices
docker exec -t cybernest-wazuh.indexer-1 \
  curl -k -u admin:SecretPassword \
  "https://localhost:9200/_snapshot/backup/snapshot_$(date +%Y%m%d)" -X PUT
```

### Logs

```bash
# Follow logs for a specific service
docker compose logs -f --tail=100 api

# Export logs to file
docker compose logs api > api_logs_$(date +%Y%m%d).txt
```

### Updates

```bash
# Pull latest images
docker compose pull

# Recreate containers with new images
docker compose up --detach --force-recreate
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Wazuh Indexer fails to start (SSL errors) | Regenerate certificates with `docker compose -f siem/wazuh/single-node/generate-indexer-certs.yml up` |
| Wazuh Dashboard shows "no healthy upstream" | Ensure Indexer is healthy first (`docker compose ps wazuh.indexer`), then restart dashboard |
| Backend API won't connect to DB | Check `POSTGRES_*` env vars match between `.env` and `backend/.env` |
| Suricata/Zeek can't capture packets | Ensure `network_mode: host` is set (already configured) and run on Linux with `CAP_NET_RAW` |
| Port conflicts (e.g., 443, 80) | Adjust `ports:` in `docker-compose.root.yml` or use the core compose file |
| Docker permission denied | Add user to docker group: `sudo usermod -aG docker $USER && newgrp docker` |
| vm.max_map_count error | Run `sudo sysctl -w vm.map_count=262144` |

### Health Checks

```bash
# Quick health check script
for svc in api wazuh.manager wazuh.indexer wazuh.dashboard thehive; do
  status=$(docker compose ps --format json "$svc" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('State','unknown'))" 2>/dev/null || echo "not found")
  echo "$svc: $status"
done
```

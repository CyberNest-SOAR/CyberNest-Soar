# CyberNest SOAR — Data Pipelines

## Pipeline Map

```
SENSOR       → COLLECTION    → PROCESSING   → STORAGE           → UI
──────────────────────────────────────────────────────────────────────────
Suricata
  ├─ eve.json → Wazuh Agent  → Wazuh Manager → Indexer (wazuh-alerts-*) → Dashboard
  ├─ eve.json → Filebeat     → (direct)      → Indexer (filebeat-*)
  └─ eve.json → Python Fwd   → (direct API)  → Indexer (cybernest-suricata-events)

Zeek
  ├─ *.log    → Wazuh Agent  → Wazuh Manager → Indexer (wazuh-alerts-*) → Dashboard
  ├─ *.log    → Filebeat     → (direct)      → Indexer (filebeat-*)
  ├─ conn.log → zeek_fwd.py  → UDP:514       → Wazuh Manager → Indexer
  └─ *.log    → Python Fwd   → (direct API)  → Indexer (cybernest-zeek-events)

Velociraptor
  ├─ events.json → Wazuh Agent → Wazuh Manager → Indexer (wazuh-alerts-*) → Dashboard
  └─ events.json → Filebeat  → (direct)      → Indexer

Arkime
  ├─ sessions.log → Wazuh Agent → Wazuh Manager → Indexer (wazuh-alerts-*) → Dashboard
  ├─ sessions.log → Filebeat  → (direct)      → Indexer
  ├─ API → Python Fwd        → (direct API)  → Indexer (cybernest-arkime-events)
  └─ (internal) → Arkime OpenSearch → Arkime Viewer (port 8005)
```

**3 ingestion methods:** Wazuh Agent (file monitoring), Filebeat (direct), Python forwarders (HTTP API)
**1 destination:** Wazuh Indexer (OpenSearch) → Dashboard at `https://localhost`
Custom decoders/rules process Suricata, Zeek, Velociraptor, Arkime events with severity-based alerting

---

## Backend Pipeline: Raw Log → Dashboard

```
MANAGER (wazuh.manager)
────────────────────────────────────────────────────
 1  REMOTED (port 1514 TCP / 514 UDP)
    └─ Receives from Agent → writes to internal queue

 2  ANALYSISD (analysis daemon)
    ├─ Predecoding: detect format (JSON, syslog, command)
    ├─ Decoder matching (in order):
    │    ├─ Default decoders (built-in)
    │    ├─ suricata-eve         prematch: ^{"timestamp":
    │    ├─ zeek-json            prematch: ^{"ts":
    │    ├─ velociraptor-json    prematch: "log_type":"velociraptor"
    │    ├─ arkime-json          prematch: "log_type":"arkime"
    │    └─ catch-all-json       prematch: ^{
    ├─ Rule matching (level >= 3 generates alert):
    │    ├─ 866001-866006  (Zeek rules)
    │    ├─ 866101-866107  (Suricata rules)
    │    ├─ 100021-100033  (Velociraptor/Arkime rules)
    │    └─ 100000-100044  (Custom local rules)
    └─ CDB threat intel enrichment (malicious IPs, domains, hashes)

 3  ALERT OUTPUT
    └─ /var/ossec/logs/alerts/alerts.json  (level >= 3)

 4  FILEBEAT (embedded in manager)
    └─ wazuh module reads alerts.json
    └─ HTTPS → wazuh.indexer:9200  (auth: admin/SecretPassword)

INDEXER (wazuh.indexer — OpenSearch)
────────────────────────────────────
 5  SECURITY PLUGIN (TLS + HTTP basic auth)
 6  wazuh-alerts-* index (ILM disabled, custom template)
 7  Stored in Docker volume: wazuh-indexer-data

DASHBOARD (wazuh.dashboard)
───────────────────────────
 8  Queries Indexer:  https://wazuh.indexer:9200  (OpenSearch Dashboards)
 9  Queries Manager:  https://wazuh.manager:55000  (Wazuh API, user wazuh-wui)

PLANE B (bypasses Wazuh):
  Sensor eve.json/*.log → suricata/zeek-filebeat → wazuh.indexer:9200
  (decoder/rules skipped — raw JSON only)
```

**Key ports:**
`1514/TCP` (Agent→Manager), `514/UDP` (syslog), `55000/TCP` (Manager API), `9200/TCP` (Indexer API), `443→5601` (Dashboard)

---

## Index Destinations

| Pipeline | Index Pattern | Source |
|----------|--------------|--------|
| Wazuh Agent → Manager | `wazuh-alerts-*` | All sensors via analysisd |
| Filebeat direct | `filebeat-*` | Suricata/Zeek raw JSON |
| Python forwarder | `cybernest-suricata-events` | Suricata |
| Python forwarder | `cybernest-zeek-events` | Zeek |
| Python forwarder | `cybernest-arkime-events` | Arkime |

---

## Custom Decoders & Rules

### Decoders (`siem/wazuh/single-node/custom/decoders/`)

| File | Decoder | Prematch |
|------|---------|----------|
| `0475-suricata_decoders.xml` | suricata-eve | `^{"timestamp":` |
| `0476-velociraptor_decoders.xml` | velociraptor-json | `"log_type":"velociraptor"` |
| `0476-velociraptor_decoders.xml` | arkime-json | `"log_type":"arkime"` |
| `local_decoder.xml` | zeek-json | `^{"ts":` |
| `local_decoder.xml` | catch-all-json | `^{` |

### Rules (`siem/wazuh/single-node/custom/rules/`)

| File | Rule IDs | Purpose |
|------|----------|---------|
| `0865-zeek_rules.xml` | 866001-866006 | Zeek network IDS |
| `0866-suricata_rules.xml` | 866101-866107 | Suricata alert/event types |
| `0867-velociraptor_rules.xml` | 100021-100033 | Velociraptor/Arkime severity |
| `local_rules.xml` | 100000-100044 | Custom rules (CVE, malware, severity) |

### Custom Suricata Rules (`sensors/ndr/suricata/suricata1/rules/`)

| File | SIDs | Attack Type |
|------|------|-------------|
| `phishing.rules` | 1000001-1000005 | Phishing detection |
| `ddos.rules` | 2000001-2000004 | DDoS detection |
| `brute-force.rules` | 3000001-3000005 | Brute force detection |

### Custom Zeek Scripts (`sensors/ndr/zeek/scripts/`)

| File | Detection |
|------|-----------|
| `phishing.zeek` | Suspicious URIs (login, secure, verify, bank, password) |
| `ddos.zeek` | >100 conn/sec from single source |
| `brute_force.zeek` | >5 failed SSH auth attempts |

---

## Credential Matrix

| Username | Password | Used By | Purpose |
|----------|----------|---------|---------|
| `admin` | `SecretPassword` | Filebeat, Indexer | Index ingest |
| `wazuh-wui` | `MyS3cr37P450r.*-` | Dashboard → Manager API | REST API auth |
| `kibanaserver` | `kibanaserver` | Dashboard internal | OpenSearch Dashboards |

---

## File Paths

| Component | Host Config | Container Path |
|-----------|-------------|----------------|
| Agent | `config/wazuh_agent/ossec.conf` | `/var/ossec/etc/ossec.conf` |
| Manager | `config/wazuh_cluster/wazuh_manager.conf` | `/var/ossec/etc/ossec.conf` |
| Filebeat (embedded) | `config/filebeat/filebeat.yml` | `/etc/filebeat/filebeat.yml` |
| Filebeat (suricata) | `config/filebeat/filebeat-suricata.yml` | `/etc/filebeat/filebeat.yml` |
| Filebeat (zeek) | `config/filebeat/filebeat-zeek.yml` | `/etc/filebeat/filebeat.yml` |
| Indexer | `config/wazuh_indexer/wazuh.indexer.yml` | `/usr/share/wazuh-indexer/config/opensearch.yml` |
| Dashboard | `config/wazuh_dashboard/opensearch_dashboards.yml` | `/usr/share/wazuh-dashboard/config/opensearch_dashboards.yml` |
| Custom decoders | `custom/decoders/*.xml` | `/var/ossec/etc/decoders/` |
| Custom rules | `custom/rules/*.xml` | `/var/ossec/etc/rules/` |
| SSL root CA | `config/wazuh_indexer_ssl_certs/root-ca-manager.pem` | `/etc/ssl/root-ca.pem` |
| SSL cert | `config/wazuh_indexer_ssl_certs/wazuh.manager.pem` | `/etc/ssl/filebeat.pem` |
| SSL key | `config/wazuh_indexer_ssl_certs/wazuh.manager-key.pem` | `/etc/ssl/filebeat.key` |

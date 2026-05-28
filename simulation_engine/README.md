# CyberNestSOAR Simulation Engine

Configurable attack simulation and SOC telemetry generation framework for the CyberNestSOAR XDR platform.

## Architecture

```
simulation_engine/
├── main.py                          # FastAPI orchestration
├── config.py                        # Shared config loader
├── config/
│   └── attack_profiles.yaml         # Attack distribution & IOC pools
├── generators/
│   ├── base.py                      # RawEvent + BaseGenerator
│   ├── benign_traffic.py            # Benign web/DNS/update traffic
│   ├── malware_simulator.py         # Beacon/dropper/injection
│   ├── brute_force_simulator.py     # SSH/RDP/web brute force
│   ├── phishing_simulator.py        # Credential harvest / spear-phish
│   ├── ddos_simulator.py            # SYN flood / HTTP flood / DNS amp
│   ├── lateral_movement.py          # SMB/WMI/PsExec/RDP movement
│   └── privilege_escalation.py      # UAC bypass / token theft / sudo
├── telemetry/
│   ├── wazuh_events.py              # alerts.json format
│   ├── suricata_alerts.py           # eve.json format
│   ├── zeek_logs.py                 # conn/http/dns/notice logs
│   ├── velociraptor_events.py       # Velociraptor event format
│   └── osquery_events.py            # osquery result log format
├── pipelines/
│   ├── opensearch_export.py         # Bulk indexing to OpenSearch
│   ├── thehive_cases.py             # TheHive case creation
│   └── dataset_builder.py           # Labeled dataset export (JSON/NDJSON/CSV)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Quick Start

```bash
pip install -r requirements.txt
python main.py
# Server starts on port 8002
```

Or with Docker:

```bash
docker compose up -d
```

## API Endpoints

### POST `/simulate/generate`

Generate events with configurable attack distribution.

**Parameters:**
- `total` — Total events (default: 1000)
- `campaign_id` — Override campaign ID
- `format` — Output format: `json`, `ndjson`, `wazuh`, `suricata`, `zeek`, `velociraptor`, `osquery`, `csv`, `opensearch_bulk`, `all`
- `export_opensearch` — Also bulk-index to OpenSearch
- `export_thehive` — Also create TheHive cases for high-severity events

**Example:**

```bash
curl -s "http://localhost:8002/simulate/generate?total=500&format=wazuh" | jq
```

### POST `/simulate/campaign`

Run a time-based multi-wave attack campaign with escalating intensity.

**Parameters:**
- `total` — Total events across all waves
- `waves` — Number of attack waves
- `interval_seconds` — Seconds between waves

### GET `/simulate/status`

Show current configuration, campaign ID, and generator state.

### POST `/simulate/config`

Update attack distribution at runtime.

```bash
curl -X POST "http://localhost:8002/simulate/config" \
  -H "Content-Type: application/json" \
  -d '{"attack_distribution": {"benign_traffic": 30, "malware": 25, "brute_force": 15, "phishing": 15, "ddos": 10, "privilege_escalation": 5}}'
```

## Configuring Attack Distribution

Edit `config/attack_profiles.yaml`:

```yaml
attack_distribution:
  benign_traffic: 45
  noise_alerts: 20
  malware: 10
  brute_force: 8
  phishing: 7
  ddos: 5
  privilege_escalation: 5
```

Percentages are normalized automatically. The `simulation.noise_level` controls duplicate/noise injection (0.0-1.0).

## Integration with SOAR Stack

The engine outputs telemetry compatible with:
- **Wazuh** — alerts.json format (decoder: json, filebeat-ready)
- **Suricata** — eve.json format (filebeat-ready)
- **Zeek** — conn.log / http.log / dns.log format (filebeat-ready)
- **Velociraptor** — events.json format (filebeat-ready)
- **osquery** — result log format (filebeat-ready)
- **OpenSearch** — bulk API NDJSON
- **TheHive** — case creation API

## Label Schema

Every generated event includes labels for ML/AI training:

```json
{
  "attack_type": "malware",
  "subtype": "beacon",
  "severity": 12,
  "true_positive": true,
  "noise": false,
  "confidence": 0.92,
  "mitre_technique_id": "T1204",
  "mitre_technique_name": "User Execution",
  "mitre_tactic": "Execution",
  "src_ip": "10.0.0.50",
  "dst_ip": "185.220.101.42",
  "domain": "evil-c2.fake",
  "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

## Safety

This framework uses **safe ATT&CK emulation only**:
- No real malware, ransomware, or destructive payloads
- Fake C2 domains (`.fake` TLD), simulated beaconing
- Traffic generated to test detection rules, not to compromise systems
- Designed for SOC training, purple-team exercises, and AI dataset generation

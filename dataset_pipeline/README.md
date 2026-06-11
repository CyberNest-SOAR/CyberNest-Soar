# CyberNestSOAR SOC Dataset Pipeline

Enterprise-grade SOC training dataset generator. Downloads real cybersecurity datasets,
normalizes them into a unified schema, enriches with threat intelligence and GeoIP,
simulates SOC workflows, and exports to OpenSearch, TheHive, NDJSON, and CSV.

## Architecture

```
Download → Parse → Enrich → Augment → Correlate → Export
                                                    ↓
                                           OpenSearch / TheHive / NDJSON / CSV
```

### Pipeline stages

| Stage | Description |
|---|---|
| **Download** | Fetches real datasets (CICIDS2017, CTU-13, UNSW-NB15, LANL Auth, CERT Insider) with synthetic fallback when downloads fail |
| **Parse** | Normalizes all formats into the `UnifiedAlert` schema |
| **Enrich** | Adds GeoIP, ATT&CK mappings, VirusTotal-style scores, EPSS, CVSS, MISP matches |
| **Augment** | Simulates analyst verdicts, alert fatigue, false positives, duplicates, playbook outcomes |
| **Correlate** | Builds multi-stage attack chains (phishing→exfil, web exploit→ransomware, brute force→compromise) |
| **Export** | NDJSON, CSV, OpenSearch bulk format, TheHive cases, direct OpenSearch index |

## Quick Start

```bash
# CLI mode — generate 50,000 events
python main.py --events 50000

# API mode
python main.py --api --port 8003

# Docker
docker-compose up -d
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/pipeline/run?target_events=50000` | Run full pipeline |
| GET | `/pipeline/status` | Pipeline status and stats |
| GET | `/pipeline/export/ndjson` | List NDJSON export files |
| GET | `/pipeline/export/csv` | List CSV export files |

## Dataset Sources

- **CICIDS2017**: Network flow data with attacks
- **CSE-CIC-IDS2018**: AWS-based IDS evaluation
- **CTU-13**: Botnet traffic captures
- **UNSW-NB15**: Modern attack patterns
- **LANL Auth**: Enterprise authentication logs
- **CERT Insider Threat**: Insider threat scenarios
- **Synthetic fallback**: Realistic generated data when downloads unavailable

## UnifiedAlert Schema

Core fields: `event_id`, `timestamp`, `src_ip`, `dst_ip`, `protocol`, `alert_signature`,
`alert_severity`, `attack_type`, `mitre_technique_id`, `confidence`, `true_positive`, `noise`

Augmented fields: `analyst_verdict`, `escalation_level`, `playbook_outcome`,
`campaign_id`, `cluster_id`, `attack_chain_stage`, `suppression_hit`

## Noise & Realism

- 8-15% duplicate alerts
- 15% false positive rate
- 5% alert fatigue clusters
- Timing irregularities
- Analyst mistakes (15% unassigned) 
- Mixed severity distributions

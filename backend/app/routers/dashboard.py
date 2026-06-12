import json
import logging
from pathlib import Path
from fastapi import APIRouter, Query
from typing import Optional
from services.collector import collector
from services.normalizer import normalizer
from schemas.models import UnifiedAlert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

OUTPUTS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "dataset_pipeline" / "data" / "outputs"

@router.get("/summary")
async def dashboard_summary(limit: int = Query(500, ge=1, le=10000)):
    raw_data = await collector.query_opensearch(
        limit=limit,
        query={
            "size": limit,
            "query": {"match_all": {}},
            "sort": [{"@timestamp": {"order": "desc"}}],
        },
    )
    hits = raw_data.get("hits", {}).get("hits", [])
    alerts = [normalizer.from_wazuh(hit) for hit in hits]

    severity_counts = {}
    for a in alerts:
        level = a.severity
        severity_counts[level] = severity_counts.get(level, 0) + 1

    source_counts = {}
    for a in alerts:
        src = a.source
        source_counts[src] = source_counts.get(src, 0) + 1

    recent = [
        {
            "event_id": a.event_id,
            "severity": a.severity,
            "source": a.source,
            "description": a.description[:100],
            "timestamp": a.timestamp.isoformat(),
            "host": a.host_context.hostname,
            "ip": a.host_context.ip_address,
        }
        for a in alerts[:20]
    ]

    intel_tags = {}
    for a in alerts:
        for tag in a.enrichment_data.tags:
            intel_tags[tag] = intel_tags.get(tag, 0) + 1

    return {
        "total_alerts": len(alerts),
        "severity_distribution": severity_counts,
        "source_distribution": source_counts,
        "recent_alerts": recent,
        "intel_tags": intel_tags,
        "avg_severity": round(sum(a.severity for a in alerts) / len(alerts), 2) if alerts else 0,
        "high_severity_count": sum(1 for a in alerts if a.severity >= 10),
    }

@router.get("/alerts-over-time")
async def dashboard_alerts_over_time(interval: str = Query("1h"), limit: int = Query(10000)):
    raw_data = await collector.query_opensearch(
        limit=0,
        query={
            "size": 0,
            "query": {"match_all": {}},
            "aggs": {
                "alerts_over_time": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "calendar_interval": interval,
                    }
                }
            },
        },
    )
    buckets = (
        raw_data.get("aggregations", {})
        .get("alerts_over_time", {})
        .get("buckets", [])
    )
    return {
        "interval": interval,
        "data": [
            {"timestamp": b.get("key_as_string", str(b["key"])), "count": b["doc_count"]}
            for b in buckets
        ],
    }

@router.get("/dataset-stats")
async def dataset_stats():
    stats = {}
    complete_file = OUTPUTS_DIR / "soc_dataset_complete.json"
    if complete_file.exists():
        with open(complete_file) as f:
            data = json.load(f)
        stats["soc_dataset"] = {
            "file": "soc_dataset_complete.json",
            "total_events": len(data) if isinstance(data, list) else 1,
        }

    thehive_files = sorted(OUTPUTS_DIR.glob("thehive_cases_*.json"))
    if thehive_files:
        with open(thehive_files[-1]) as f:
            cases = json.load(f)
        stats["thehive_cases"] = {
            "file": thehive_files[-1].name,
            "total_cases": len(cases) if isinstance(cases, list) else 1,
        }

    llm_dir = OUTPUTS_DIR / "llm_datasets"
    if llm_dir.exists():
        for f in llm_dir.iterdir():
            if f.is_file():
                with open(f) as fh:
                    data = json.load(fh)
                key = f.stem.rsplit("_", 1)[0]
                stats[f"llm_{key}"] = {
                    "file": f.name,
                    "total_entries": len(data) if isinstance(data, list) else 1,
                }

    return stats

@router.get("/pipeline-summary")
async def pipeline_summary(limit: int = Query(50000, ge=1, le=300000)):
    latest_ndjson = next(
        (sorted(OUTPUTS_DIR.glob("soc_dataset_*.ndjson"))[-1:]),
        None,
    )
    if isinstance(latest_ndjson, list) and latest_ndjson:
        latest_ndjson = latest_ndjson[0]
    if not latest_ndjson:
        return {"error": "No pipeline dataset found"}

    total = 0
    by_attack = Counter()
    by_severity = Counter()
    by_verdict = Counter()
    by_source = Counter()
    by_suppression = Counter()
    by_noise = Counter()
    by_mitre = Counter()
    playbook_actions = Counter()
    escalation_levels = Counter()

    with open(latest_ndjson) as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            total += 1
            by_attack[event.get("attack_type", "unknown")] += 1
            by_severity[event.get("alert_severity", 0)] += 1
            by_verdict[event.get("analyst_verdict", "unknown")] += 1
            by_source[event.get("dataset_source", "unknown")] += 1
            sup = event.get("suppression_hit", False)
            by_suppression["suppressed" if sup else "not_suppressed"] += 1
            noi = event.get("noise", False)
            by_noise["noise" if noi else "not_noise"] += 1
            tactic = event.get("mitre_tactic")
            if tactic and tactic != "None":
                by_mitre[tactic] += 1
            pa = event.get("playbook_outcome")
            if pa:
                playbook_actions[pa] += 1
            el = event.get("escalation_level")
            if el and el != "none":
                escalation_levels[el] += 1

    return {
        "source": latest_ndjson.name,
        "total_events": total,
        "attack_type_distribution": dict(by_attack.most_common()),
        "severity_distribution": dict(sorted(by_severity.items())),
        "analyst_verdicts": dict(by_verdict.most_common()),
        "dataset_sources": dict(by_source.most_common()),
        "suppression": dict(by_suppression),
        "noise_classification": dict(by_noise),
        "mitre_tactics": dict(by_mitre.most_common()),
        "playbook_outcomes": dict(playbook_actions.most_common()),
        "escalation_levels": dict(escalation_levels.most_common()),
    }

@router.get("/health-summary")
async def health_summary():
    os_status = False
    try:
        response = await collector.client.get(
            f"{collector.os_host}/_cluster/health",
            auth=collector.os_auth,
        )
        if response.status_code == 200:
            os_status = True
            os_data = response.json()
    except Exception:
        os_data = {}

    return {
        "opensearch": {
            "connected": os_status,
            "cluster_name": os_data.get("cluster_name", "unknown"),
            "status": os_data.get("status", "unknown"),
            "nodes": os_data.get("number_of_nodes", 0),
        },
        "datasets_available": (OUTPUTS_DIR / "soc_dataset_complete.json").exists(),
        "llm_datasets_available": (OUTPUTS_DIR / "llm_datasets").exists(),
        "thehive_cases_available": bool(list(OUTPUTS_DIR.glob("thehive_cases_*.json"))),
    }

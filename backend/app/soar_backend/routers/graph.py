import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Query
from typing import Optional
from services.collector import collector
from services.normalizer import normalizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["Graph & Visualization"])

OUTPUTS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "dataset_pipeline" / "data" / "outputs"

def _get_latest_ndjson():
    files = sorted(OUTPUTS_DIR.glob("soc_dataset_*.ndjson"))
    return files[-1] if files else None

def _iter_ndjson(path: Path, max_lines: int = None):
    with open(path) as f:
        for i, line in enumerate(f):
            if max_lines and i >= max_lines:
                break
            line = line.strip()
            if line:
                yield json.loads(line)

# ─── Pipeline graph endpoints (from ndjson data, 78 fields) ───

@router.get("/pipeline/attack-type-distribution")
async def pipeline_attack_type_distribution(limit: int = Query(50000, ge=1, le=300000)):
    latest = _get_latest_ndjson()
    if not latest:
        return {"error": "No pipeline dataset found"}
    counts = Counter()
    total = 0
    for event in _iter_ndjson(latest, limit):
        at = event.get("attack_type", "unknown")
        counts[at] += 1
        total += 1
    return {
        "source": latest.name,
        "total_events": total,
        "distribution": [{"attack_type": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])],
    }

@router.get("/pipeline/severity-distribution")
async def pipeline_severity_distribution(limit: int = Query(50000, ge=1, le=300000)):
    latest = _get_latest_ndjson()
    if not latest:
        return {"error": "No pipeline dataset found"}
    counts = Counter()
    total = 0
    for event in _iter_ndjson(latest, limit):
        sev = event.get("alert_severity", 0)
        counts[sev] += 1
        total += 1
    return {
        "source": latest.name,
        "total_events": total,
        "distribution": [{"severity": k, "count": v} for k, v in sorted(counts.items())],
    }

@router.get("/pipeline/mitre-tactics")
async def pipeline_mitre_tactics(limit: int = Query(50000, ge=1, le=300000)):
    latest = _get_latest_ndjson()
    if not latest:
        return {"error": "No pipeline dataset found"}
    counts = Counter()
    total = 0
    for event in _iter_ndjson(latest, limit):
        tactic = event.get("mitre_tactic", "None")
        if tactic and tactic != "None":
            counts[tactic] += 1
        total += 1
    return {
        "source": latest.name,
        "total_events": total,
        "distribution": [{"tactic": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])],
    }

@router.get("/pipeline/analyst-verdicts")
async def pipeline_analyst_verdicts(limit: int = Query(50000, ge=1, le=300000)):
    latest = _get_latest_ndjson()
    if not latest:
        return {"error": "No pipeline dataset found"}
    counts = Counter()
    total = 0
    for event in _iter_ndjson(latest, limit):
        verdict = event.get("analyst_verdict", "unknown")
        counts[verdict] += 1
        total += 1
    return {
        "source": latest.name,
        "total_events": total,
        "distribution": [{"verdict": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])],
    }

@router.get("/pipeline/timeline")
async def pipeline_timeline(
    interval: str = Query("1h", description="Aggregation interval (1h, 1d)"),
    limit: int = Query(100000, ge=1, le=300000),
):
    latest = _get_latest_ndjson()
    if not latest:
        return {"error": "No pipeline dataset found"}
    buckets = {}
    for event in _iter_ndjson(latest, limit):
        ts_str = event.get("timestamp")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if interval == "1d":
            key = ts.strftime("%Y-%m-%d")
        elif interval == "1h":
            key = ts.strftime("%Y-%m-%dT%H:00:00")
        else:
            key = ts.strftime("%Y-%m-%dT%H:00:00")
        buckets[key] = buckets.get(key, 0) + 1
    return {
        "source": latest.name,
        "interval": interval,
        "timeline": [{"timestamp": k, "count": v} for k, v in sorted(buckets.items())],
    }

@router.get("/alerts/severity-distribution")
async def severity_distribution(limit: int = Query(1000, ge=1, le=10000)):
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

    severity_counts = Counter(a.severity for a in alerts)
    distribution = [
        {"severity": level, "count": count}
        for level, count in sorted(severity_counts.items(), key=lambda x: x[0])
    ]
    return {
        "total_alerts": len(alerts),
        "severity_distribution": distribution,
        "avg_severity": round(sum(a.severity for a in alerts) / len(alerts), 2) if alerts else 0,
    }

@router.get("/alerts/timeline")
async def alert_timeline(
    interval: str = Query("1h", description="Aggregation interval (e.g. 1h, 30m, 1d)"),
    limit: int = Query(5000, ge=1, le=50000),
):
    raw_data = await collector.query_opensearch(
        limit=limit,
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
            "sort": [{"@timestamp": {"order": "desc"}}],
        },
    )
    buckets = (
        raw_data.get("aggregations", {})
        .get("alerts_over_time", {})
        .get("buckets", [])
    )
    timeline = [
        {"timestamp": b.get("key_as_string", b["key"]), "count": b["doc_count"]}
        for b in buckets
    ]
    return {"interval": interval, "timeline": timeline}

@router.get("/alerts/top-rules")
async def top_rules(limit: int = Query(10, ge=1, le=100), top_n: int = Query(5000, ge=1, le=50000)):
    raw_data = await collector.query_opensearch(
        limit=0,
        query={
            "size": 0,
            "query": {"match_all": {}},
            "aggs": {
                "top_rules": {
                    "terms": {"field": "rule.description.keyword", "size": limit}
                }
            },
        },
    )
    buckets = (
        raw_data.get("aggregations", {})
        .get("top_rules", {})
        .get("buckets", [])
    )
    return {
        "top_rules": [
            {"rule": b["key"], "count": b["doc_count"]} for b in buckets
        ]
    }

@router.get("/alerts/source-breakdown")
async def source_breakdown(limit: int = Query(5000, ge=1, le=50000)):
    raw_data = await collector.query_opensearch(
        limit=0,
        query={
            "size": 0,
            "query": {"match_all": {}},
            "aggs": {
                "by_source": {
                    "terms": {"field": "agent.name.keyword", "size": 50}
                }
            },
        },
    )
    buckets = (
        raw_data.get("aggregations", {})
        .get("by_source", {})
        .get("buckets", [])
    )
    return {
        "source_breakdown": [
            {"source": b["key"], "count": b["doc_count"]} for b in buckets
        ]
    }

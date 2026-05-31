"""Dataset builder — export events as labeled datasets for ML/AI training."""

import csv
import json
import io
from datetime import timezone
from typing import Dict, Any, List, TextIO

from generators.base import RawEvent
from config import get_config


def build_labeled_record(event: RawEvent) -> Dict[str, Any]:
    """Produce a flat labeled record suitable for ML training."""
    cfg = get_config().get("labels", {})
    record = {
        "event_id": event.event_id,
        "campaign_id": event.campaign_id,
        "attack_type": event.attack_type,
        "subtype": event.subtype or "",
        "timestamp": event.timestamp.astimezone(timezone.utc).isoformat(),
        "severity": event.severity,
        "confidence": event.confidence,
        "true_positive": event.true_positive,
        "noise": event.noise,
        "src_ip": event.src_ip or "",
        "dst_ip": event.dst_ip or "",
        "src_port": event.src_port or 0,
        "dst_port": event.dst_port or 0,
        "protocol": event.protocol or "",
        "hostname": event.hostname or "",
        "domain": event.domain or "",
        "uri": event.uri or "",
        "user_agent": event.user_agent or "",
        "process_name": event.process_name or "",
        "command_line": event.command_line or "",
        "username": event.username or "",
        "file_hash_md5": event.file_hash_md5 or "",
        "file_hash_sha256": event.file_hash_sha256 or "",
        "description": event.description or "",
        "tool_target": event.tool_target or "",
    }

    if cfg.get("include_mitre", True):
        record.update({
            "mitre_technique_id": event.mitre_technique_id,
            "mitre_technique_name": event.mitre_technique_name,
            "mitre_tactic": event.mitre_tactic,
        })
    if cfg.get("include_ioc", True):
        record.update({
            "ioc_ip": event.src_ip or "",
            "ioc_domain": event.domain or "",
            "ioc_hash": event.file_hash_sha256 or "",
        })
    if cfg.get("include_noise", True):
        record["is_noise"] = event.noise
    if cfg.get("include_confidence", True):
        record["confidence"] = event.confidence

    return record


def build_normalized_json(events: List[RawEvent]) -> List[Dict[str, Any]]:
    """Build a normalized JSON array of labeled records."""
    return [build_labeled_record(e) for e in events]


def build_ndjson(events: List[RawEvent]) -> str:
    """Build NDJSON string."""
    lines = [json.dumps(build_labeled_record(e)) for e in events]
    return "\n".join(lines)


def build_csv(events: List[RawEvent], file: TextIO = None) -> str:
    """Build CSV string or write to file."""
    records = build_normalized_json(events)
    if not records:
        return ""
    fieldnames = list(records[0].keys())
    output = io.StringIO() if file is None else None
    writer = csv.DictWriter(file or output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue() if output else ""


def build_opensearch_bulk(events: List[RawEvent]) -> str:
    """Build OpenSearch bulk API NDJSON."""
    lines = []
    for ev in events:
        record = build_labeled_record(ev)
        action = {"index": {"_index": f"simulation-dataset-{ev.campaign_id}"}}
        lines.append(json.dumps(action))
        lines.append(json.dumps(record))
    return "\n".join(lines)


def build_dataset(
    events: List[RawEvent],
    formats: List[str] = None,
) -> Dict[str, str]:
    """Build a dataset dict of format -> content.

    Supported formats: json, ndjson, csv, opensearch_bulk.
    """
    formats = formats or ["json", "ndjson"]
    result = {}
    if "json" in formats:
        result["json"] = json.dumps(build_normalized_json(events), indent=2)
    if "ndjson" in formats:
        result["ndjson"] = build_ndjson(events)
    if "csv" in formats:
        result["csv"] = build_csv(events)
    if "opensearch_bulk" in formats:
        result["opensearch_bulk"] = build_opensearch_bulk(events)
    return result

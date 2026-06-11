import csv
import io
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from parsers.normalizer import UnifiedAlert
from config.settings import OUTPUTS_DIR

logger = logging.getLogger(__name__)


def export_ndjson(alerts: List[UnifiedAlert], path: Optional[Path] = None) -> Path:
    dest = path or (OUTPUTS_DIR / f"soc_dataset_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.ndjson")
    with open(dest, "w") as f:
        for alert in alerts:
            f.write(json.dumps(alert.to_dict()) + "\n")
    logger.info("Exported %d alerts to %s", len(alerts), dest)
    return dest


def export_csv(alerts: List[UnifiedAlert], path: Optional[Path] = None) -> Path:
    dest = path or (OUTPUTS_DIR / f"soc_dataset_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv")
    if not alerts:
        dest.write_text("")
        return dest
    fields = [
        "event_id", "timestamp", "dataset_source", "event_type",
        "src_ip", "src_port", "dst_ip", "dst_port", "protocol",
        "alert_signature", "alert_severity", "alert_category",
        "attack_type", "mitre_technique_id", "mitre_tactic",
        "confidence", "true_positive", "noise", "analyst_verdict",
        "escalation_level", "playbook_outcome", "campaign_id",
        "cluster_id", "attack_chain_stage",
        "geoip_src_country", "geoip_dst_country",
        "enrichment_vt_score", "enrichment_abuse_score",
    ]
    with open(dest, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for alert in alerts:
            writer.writerow(alert.to_dict())
    logger.info("Exported %d alerts to %s", len(alerts), dest)
    return dest


def export_opensearch_bulk(alerts: List[UnifiedAlert],
                           path: Optional[Path] = None,
                           index: str = "soc-dataset-4.x") -> Path:
    dest = path or (OUTPUTS_DIR / f"soc_dataset_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_bulk.ndjson")
    with open(dest, "w") as f:
        for alert in alerts:
            action = {"index": {"_index": index, "_id": alert.event_id}}
            f.write(json.dumps(action) + "\n")
            f.write(json.dumps(alert.to_elasticsearch_doc()) + "\n")
    logger.info("Exported %d bulk docs to %s", len(alerts), dest)
    return dest


def export_thehive(alerts: List[UnifiedAlert],
                   path: Optional[Path] = None) -> Dict[str, Any]:
    high_sev = [a for a in alerts if a.alert_severity and a.alert_severity >= 10 and a.true_positive]
    if not high_sev:
        logger.info("No high-severity alerts for TheHive export")
        return {"cases": 0, "alerts": 0}

    cases = []
    for alert in high_sev[:50]:
        case = {
            "title": f"[{alert.severity_label.upper()}] {alert.alert_signature or 'Security Alert'}",
            "description": (
                f"Dataset source: {alert.dataset_source}\n"
                f"Attack type: {alert.attack_type}\n"
                f"MITRE: {alert.mitre_technique_id} - {alert.mitre_technique_name}\n"
                f"Source: {alert.src_ip}:{alert.src_port} -> {alert.dst_ip}:{alert.dst_port}\n"
                f"Severity: {alert.alert_severity}\n"
                f"Confidence: {alert.confidence}\n"
                f"Campaign: {alert.campaign_id}\n"
            ),
            "severity": min(4, max(1, (alert.alert_severity or 5) // 3)),
            "tags": [
                alert.attack_type or "unknown",
                alert.mitre_tactic or "unknown",
                alert.dataset_source,
                "soc-dataset",
            ],
            "observables": [],
            "tasks": [
                {"title": "Investigate source IP", "description": f"Check {alert.src_ip} in threat intel feeds", "status": "Waiting"},
                {"title": "Check endpoint logs", "description": "Review endpoint telemetry for signs of compromise", "status": "Waiting"},
                {"title": "Contain affected assets", "description": f"Isolate {alert.dst_ip} if confirmed malicious", "status": "Pending"},
            ],
        }
        if alert.src_ip:
            case["observables"].append({"dataType": "ip", "data": alert.src_ip, "message": "Source IP"})
        if alert.dst_ip:
            case["observables"].append({"dataType": "ip", "data": alert.dst_ip, "message": "Destination IP"})
        if alert.ioc_hash:
            case["observables"].append({"dataType": "hash", "data": alert.ioc_hash, "message": "IOC Hash"})
        if alert.ioc_domain:
            case["observables"].append({"dataType": "domain", "data": alert.ioc_domain, "message": "IOC Domain"})
        cases.append(case)

    dest = path or (OUTPUTS_DIR / f"thehive_cases_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json")
    with open(dest, "w") as f:
        json.dump(cases, f, indent=2)

    logger.info("Exported %d TheHive cases to %s", len(cases), dest)
    return {"cases": len(cases), "alerts": len(high_sev), "path": str(dest)}

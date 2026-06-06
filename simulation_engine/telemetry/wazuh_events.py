"""Telemetry formatter: RawEvent -> Wazuh-compatible alert JSON (alerts.json format)."""

import json
from datetime import timezone
from typing import Dict, Any, List

from generators.base import RawEvent
from config import pick_random_hostname


SEVERITY_MAP = {
    "benign": 3,
    "noise": 2,
    "malware": 12,
    "brute_force": 10,
    "phishing": 10,
    "ddos": 12,
    "lateral_movement": 10,
    "privilege_escalation": 12,
}

RULE_ID_MAP = {
    "benign": 100001,
    "noise": 100002,
    "malware": 100010,
    "brute_force": 100020,
    "phishing": 100030,
    "ddos": 100040,
    "lateral_movement": 100050,
    "privilege_escalation": 100060,
}

WAZUH_DECODER_MAP = {
    "benign": "json",
    "malware": "json",
    "brute_force": "ssh",
    "phishing": "json",
    "ddos": "json",
    "lateral_movement": "wmi",
    "privilege_escalation": "windows",
}


def format_wazuh_alert(event: RawEvent) -> Dict[str, Any]:
    ts = event.timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    rule_id = RULE_ID_MAP.get(event.attack_type, 100000)
    severity = event.severity or SEVERITY_MAP.get(event.attack_type, 5)
    decoder = WAZUH_DECODER_MAP.get(event.attack_type, "json")

    raw = {
        "event_id": event.event_id,
        "attack_type": event.attack_type,
        "subtype": event.subtype,
        "campaign_id": event.campaign_id,
        "mitre": {
            "technique_id": event.mitre_technique_id,
            "technique_name": event.mitre_technique_name,
            "tactic": event.mitre_tactic,
        },
        "src_ip": event.src_ip or "0.0.0.0",
        "dst_ip": event.dst_ip or "0.0.0.0",
        "src_port": event.src_port or 0,
        "dst_port": event.dst_port or 0,
        "protocol": event.protocol or "TCP",
        "hostname": event.hostname or pick_random_hostname(),
        "process": {
            "name": event.process_name,
            "pid": event.process_pid,
            "parent": event.parent_process,
        },
        "username": event.username,
        "command_line": event.command_line,
        "file_hash": {
            "md5": event.file_hash_md5,
            "sha1": event.file_hash_sha1,
            "sha256": event.file_hash_sha256,
        },
        "domain": event.domain,
        "uri": event.uri,
        "user_agent": event.user_agent,
        "description": event.description,
        "iocs": event.iocs,
        "true_positive": event.true_positive,
        "noise": event.noise,
    }

    return {
        "timestamp": ts,
        "rule": {
            "id": str(rule_id),
            "level": severity,
            "description": event.description or f"Simulated {event.attack_type} alert",
        },
        "agent": {
            "id": "002",
            "name": event.hostname or pick_random_hostname(),
            "ip": event.src_ip or "0.0.0.0",
        },
        "manager": {
            "name": "wazuh-manager-sim",
        },
        "data": raw,
        "decoder": {"name": decoder},
        "location": f"/var/log/{event.attack_type}/simulation.log",
        "full_log": json.dumps(raw),
        "simulation": {
            "campaign_id": event.campaign_id,
            "event_id": event.event_id,
            "attack_type": event.attack_type,
            "mitre_technique_id": event.mitre_technique_id,
            "mitre_tactic": event.mitre_tactic,
        },
    }


def format_wazuh_batch(events: List[RawEvent]) -> List[Dict[str, Any]]:
    return [format_wazuh_alert(e) for e in events]


def format_wazuh_ndjson(events: List[RawEvent]) -> str:
    return "\n".join(json.dumps(format_wazuh_alert(e)) for e in events)

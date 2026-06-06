"""Telemetry formatter: RawEvent -> osquery-compatible event format."""

import json
from datetime import timezone
from typing import Dict, Any, List

from generators.base import RawEvent
from config import pick_random_ip, pick_random_hostname


def format_osquery_event(event: RawEvent) -> Dict[str, Any]:
    ts = int(event.timestamp.timestamp())
    host = event.hostname or pick_random_hostname()

    result = {
        "name": f"pack_simulation_{event.attack_type}",
        "hostIdentifier": host,
        "calendarTime": event.timestamp.astimezone(timezone.utc).strftime("%a %b %d %H:%M:%S %Y UTC"),
        "unixTime": ts,
        "epoch": ts,
        "counter": 0,
        "decorations": {
            "hostname": host,
            "username": event.username or "sim-user",
        },
        "columns": {
            "pid": str(event.process_pid or 1234),
            "name": event.process_name or "sim_agent",
            "path": f"/usr/bin/{event.process_name or 'sim_agent'}",
            "cmdline": event.command_line or "",
            "parent": str(1000),
            "uid": "1000",
            "gid": "1000",
            "username": event.username or "sim-user",
        },
        "action": "added",
        "simulation": {
            "campaign_id": event.campaign_id,
            "event_id": event.event_id,
            "attack_type": event.attack_type,
            "mitre_technique_id": event.mitre_technique_id,
            "mitre_tactic": event.mitre_tactic,
            "true_positive": event.true_positive,
            "noise": event.noise,
        },
    }

    if event.attack_type == "malware":
        result["name"] = "pack_incident_response_malware"
        result["columns"].update({
            "md5": event.file_hash_md5 or "",
            "sha256": event.file_hash_sha256 or "",
            "domain": event.domain or "",
        })
    elif event.attack_type == "brute_force":
        result["name"] = "pack_incident_response_bruteforce"
        result["columns"].update({
            "src_ip": event.src_ip or "",
            "dst_ip": event.dst_ip or "",
            "dst_port": str(event.dst_port or 0),
        })

    return result


def format_osquery_batch(events: List[RawEvent]) -> List[Dict[str, Any]]:
    return [format_osquery_event(e) for e in events]


def format_osquery_ndjson(events: List[RawEvent]) -> str:
    return "\n".join(json.dumps(format_osquery_event(e)) for e in events)

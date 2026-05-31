"""Telemetry formatter: RawEvent -> Velociraptor event format."""

import json
from datetime import timezone
from typing import Dict, Any, List

from generators.base import RawEvent
from config import pick_random_ip, pick_random_hostname


def format_velociraptor_event(event: RawEvent) -> Dict[str, Any]:
    ts = event.timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    artifact = event.attack_type.upper()
    flow_id = hash(event.event_id) & 0x7FFFFFFFFFFFFFFF

    return {
        "timestamp": ts,
        "event_id": event.event_id,
        "flow_id": flow_id,
        "artifact": f"Custom.Simulation.{artifact}",
        "client_id": "sim-client-001",
        "hostname": event.hostname or pick_random_hostname(),
        "process": {
            "name": event.process_name or "sim_agent",
            "pid": event.process_pid or 1234,
            "ppid": 1000,
            "command_line": event.command_line or "",
            "exe": f"/usr/bin/{event.process_name or 'sim_agent'}",
        },
        "user": {
            "username": event.username or "sim-user",
            "sid": "S-1-5-21-sim",
        },
        "network": {
            "src_ip": event.src_ip or pick_random_ip(public=False),
            "dst_ip": event.dst_ip or pick_random_ip(public=True),
            "src_port": event.src_port or 50000,
            "dst_port": event.dst_port or 443,
            "protocol": event.protocol or "TCP",
        },
        "domain": event.domain or "",
        "uri": event.uri or "",
        "file": {
            "md5": event.file_hash_md5 or "",
            "sha1": event.file_hash_sha1 or "",
            "sha256": event.file_hash_sha256 or "",
        },
        "registry": {
            "key": "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\SimulationEvent",
            "value": event.command_line or "",
        },
        "description": event.description or f"Simulated {event.attack_type} event",
        "severity": event.severity or 5,
        "status": "PROCESSED",
        "log_type": f"simulation_{event.attack_type}",
        "simulation": {
            "campaign_id": event.campaign_id,
            "attack_type": event.attack_type,
            "subtype": event.subtype,
            "mitre_technique_id": event.mitre_technique_id,
            "mitre_tactic": event.mitre_tactic,
            "true_positive": event.true_positive,
            "noise": event.noise,
        },
    }


def format_velociraptor_batch(events: List[RawEvent]) -> List[Dict[str, Any]]:
    return [format_velociraptor_event(e) for e in events]


def format_velociraptor_ndjson(events: List[RawEvent]) -> str:
    return "\n".join(json.dumps(format_velociraptor_event(e)) for e in events)

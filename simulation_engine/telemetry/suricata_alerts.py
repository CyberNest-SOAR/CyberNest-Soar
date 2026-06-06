"""Telemetry formatter: RawEvent -> Suricata eve.json format."""

import json
from datetime import timezone
from typing import Dict, Any, List

from generators.base import RawEvent
from config import pick_random_ip

_CVE_POOL = [
    "CVE-2024-4577", "CVE-2023-38831", "CVE-2024-6387", "CVE-2021-40444",
    "CVE-2024-9999", "CVE-2023-23397", "CVE-2024-21410", "CVE-2021-34527",
]

SIGNATURE_TEMPLATES = {
    "malware": "ET TROJAN Win32/{family} Malicious Beacon Activity (CVE-{cve})",
    "brute_force": "ET EXPLOIT SSH Brute-Force Attempt Against {service} Server",
    "phishing": "ET MALWARE Win32/Phishing Kit Landing Page Detected",
    "ddos": "ET DDoS HTTP GET Flood Targeting {service} (severity: 1)",
    "lateral_movement": "ET EXPLOIT SMB Lateral Movement via {service}",
    "privilege_escalation": "ET MALWARE Privilege Escalation via {technique}",
    "noise": "Simulated Background Noise Alert",
    "benign": "Simulated Benign Traffic",
}

FAMILIES = ["Emotet", "Trickbot", "Dridex", "QakBot", "IcedID", "BumbleBee"]
TECHNIQUES = ["DLLHijack", "UACBypass", "TokenTheft", "NamedPipeImpersonation"]


def _make_signature(event: RawEvent) -> str:
    template = SIGNATURE_TEMPLATES.get(event.attack_type, "Simulated {attack_type} alert")
    cve = event.iocs.get("cve") or __import__("random").choice(_CVE_POOL)
    family = __import__("random").choice(FAMILIES)
    technique = __import__("random").choice(TECHNIQUES)
    service = event.subtype or "unknown"
    return template.format(
        family=family, cve=cve, service=service, technique=technique,
        attack_type=event.attack_type,
    )


def format_suricata_alert(event: RawEvent) -> Dict[str, Any]:
    ts = event.timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    signature = _make_signature(event)

    return {
        "timestamp": ts,
        "event_type": "alert",
        "src_ip": event.src_ip or pick_random_ip(public=True),
        "src_port": event.src_port or 0,
        "dest_ip": event.dst_ip or pick_random_ip(public=False),
        "dest_port": event.dst_port or 80,
        "proto": event.protocol or "TCP",
        "app_proto": "http",
        "alert": {
            "action": "allowed",
            "gid": 1,
            "signature_id": hash(event.attack_type) % 100000 + 2000000,
            "rev": 1,
            "signature": signature,
            "category": "Malware C2",
            "severity": 1 if event.severity and event.severity >= 12 else 2 if event.severity and event.severity >= 8 else 3,
        },
        "flow_id": hash(event.event_id) & 0x7FFFFFFFFFFFFFFF,
        "payload": "",
        "payload_printable": "",
        "stream": 0,
        "packet": "",
        "host": event.hostname or "simulation-sensor",
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


def format_suricata_batch(events: List[RawEvent]) -> List[Dict[str, Any]]:
    return [format_suricata_alert(e) for e in events]


def format_suricata_ndjson(events: List[RawEvent]) -> str:
    return "\n".join(json.dumps(format_suricata_alert(e)) for e in events)

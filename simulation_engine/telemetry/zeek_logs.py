"""Telemetry formatter: RawEvent -> Zeek conn.log / http.log / dns.log format."""

import json
from datetime import timezone
from typing import Dict, Any, List

from generators.base import RawEvent
from config import pick_random_ip


def format_zeek_conn(event: RawEvent) -> Dict[str, Any]:
    ts = event.timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    duration = 0.5
    orig_bytes = 512
    resp_bytes = 2048
    conn_state = "SF"

    return {
        "ts": ts,
        "uid": f"C{hash(event.event_id) & 0x7FFFFFFF:012x}",
        "id.orig_h": event.src_ip or pick_random_ip(public=False),
        "id.orig_p": event.src_port or 50000,
        "id.resp_h": event.dst_ip or pick_random_ip(public=True),
        "id.resp_p": event.dst_port or 80,
        "proto": event.protocol or "tcp",
        "service": event.subtype or "-",
        "duration": duration,
        "orig_bytes": orig_bytes,
        "resp_bytes": resp_bytes,
        "conn_state": conn_state,
        "local_orig": True,
        "local_resp": False,
        "missed_bytes": 0,
        "history": "ShADTdT",
        "orig_pkts": 10,
        "orig_ip_bytes": orig_bytes + 400,
        "resp_pkts": 8,
        "resp_ip_bytes": resp_bytes + 320,
        "tunnel_parents": [],
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


def format_zeek_http(event: RawEvent) -> Dict[str, Any]:
    ts = event.timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    return {
        "ts": ts,
        "uid": f"C{hash(event.event_id) & 0x7FFFFFFF:012x}",
        "id.orig_h": event.src_ip or pick_random_ip(public=False),
        "id.orig_p": event.src_port or 50000,
        "id.resp_h": event.dst_ip or pick_random_ip(public=True),
        "id.resp_p": event.dst_port or 80,
        "trans_depth": 1,
        "method": "GET",
        "host": event.domain or "example.com",
        "uri": event.uri or "/",
        "referrer": "-",
        "version": "1.1",
        "user_agent": event.user_agent or "Mozilla/5.0",
        "request_body_len": 0,
        "response_body_len": 2048,
        "status_code": 200,
        "status_msg": "OK",
        "info_code": None,
        "info_msg": None,
        "tags": [],
        "username": event.username or "-",
        "password": "-",
        "proxied": None,
        "orig_fuids": [],
        "orig_mime_types": [],
        "resp_fuids": [],
        "resp_mime_types": [],
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


def format_zeek_dns(event: RawEvent) -> Dict[str, Any]:
    ts = event.timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    return {
        "ts": ts,
        "uid": f"C{hash(event.event_id) & 0x7FFFFFFF:012x}",
        "id.orig_h": event.src_ip or pick_random_ip(public=False),
        "id.orig_p": event.src_port or 50000,
        "id.resp_h": "8.8.8.8",
        "id.resp_p": 53,
        "proto": "udp",
        "trans_id": hash(event.event_id) & 0xFFFF,
        "query": event.domain or "example.com",
        "qclass": 1,
        "qclass_name": "C_INTERNET",
        "qtype": 1,
        "qtype_name": "A",
        "rcode": 0,
        "rcode_name": "NOERROR",
        "AA": False,
        "TC": False,
        "RD": True,
        "RA": True,
        "Z": 0,
        "answers": [event.dst_ip or "93.184.216.34"],
        "TTLs": [300],
        "rejected": False,
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


def format_zeek_notice(event: RawEvent) -> Dict[str, Any]:
    ts = event.timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    return {
        "ts": ts,
        "uid": f"C{hash(event.event_id) & 0x7FFFFFFF:012x}",
        "id.orig_h": event.src_ip or pick_random_ip(public=False),
        "id.orig_p": event.src_port or 0,
        "id.resp_h": event.dst_ip or pick_random_ip(public=True),
        "id.resp_p": event.dst_port or 0,
        "fuid": None,
        "file_mime_type": None,
        "file_desc": None,
        "proto": event.protocol or "tcp",
        "note": f"Simulated::{event.attack_type.upper()}",
        "msg": event.description or f"Simulated {event.attack_type}",
        "sub": "-",
        "src": event.src_ip or pick_random_ip(public=False),
        "dst": event.dst_ip or pick_random_ip(public=True),
        "p": event.dst_port or 0,
        "n": event.dst_port or 0,
        "peer_descr": "simulation",
        "actions": [],
        "email_dest": None,
        "suppress_for": None,
        "remote_location": None,
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


def format_zeek_log(event: RawEvent, log_type: str = "conn") -> Dict[str, Any]:
    m = {
        "conn": format_zeek_conn,
        "http": format_zeek_http,
        "dns": format_zeek_dns,
        "notice": format_zeek_notice,
    }
    fmt = m.get(log_type, format_zeek_conn)
    return fmt(event)


def format_zeek_batch(events: List[RawEvent], log_type: str = "conn") -> List[Dict[str, Any]]:
    return [format_zeek_log(e, log_type) for e in events]


def format_zeek_ndjson(events: List[RawEvent], log_type: str = "conn") -> str:
    return "\n".join(json.dumps(format_zeek_log(e, log_type)) for e in events)

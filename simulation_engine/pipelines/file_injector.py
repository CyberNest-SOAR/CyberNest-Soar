"""
pipelines/file_injector.py — Inject generated events into real Wazuh-monitored log files.

Writes synthetic Suricata eve.json, Zeek logs, Velociraptor events.json, and
Arkime sessions.log entries to the actual host filesystem paths that the Wazuh
agent monitors.  This causes analysisd to process them through decoders/rules
and produce alerts visible in the Wazuh dashboard.

Paths are resolved relative to the project root
(``/home/omen212/soar-project/CyberNest-Soar/``).
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from generators.base import RawEvent
from telemetry.suricata_alerts import format_suricata_alert
from telemetry.zeek_logs import format_zeek_log
from telemetry.velociraptor_events import format_velociraptor_event

logger = logging.getLogger(__name__)

# Resolve project root (simulation_engine is at project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SENSORS = _PROJECT_ROOT / "sensors"

_LOG_PATHS = {
    "suricata": _SENSORS / "ndr" / "suricata" / "suricata-setup" / "suricata" / "logs" / "eve.json",
    "velociraptor": _SENSORS / "edr" / "velociraptor" / "data" / "events.json",
    "arkime": _SENSORS / "ndr" / "arkime" / "arkime-logs" / "sessions.log",
    "zeek_conn": _SENSORS / "ndr" / "zeek" / "logs" / "conn.log",
    "zeek_http": _SENSORS / "ndr" / "zeek" / "logs" / "http.log",
    "zeek_dns": _SENSORS / "ndr" / "zeek" / "logs" / "dns.log",
    "zeek_notice": _SENSORS / "ndr" / "zeek" / "logs" / "notice.log",
    "zeek_ssl": _SENSORS / "ndr" / "zeek" / "logs" / "ssl.log",
}


def _append_line(path: Path, line: str):
    """Append a single JSON line to a log file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(line + "\n")
        logger.debug("Appended line to %s", path)
        return True
    except PermissionError:
        logger.warning("Permission denied writing to %s — try sudo", path)
        return False
    except Exception as e:
        logger.warning("Failed to write to %s: %s", path, e)
        return False


def _format_arkime_session(event: RawEvent) -> Dict[str, Any]:
    """Convert a RawEvent into an Arkime sessions.log entry."""
    ts = event.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return {
        "ts": ts,
        "uid": event.event_id[:20],
        "src_ip": event.src_ip or "0.0.0.0",
        "src_port": event.src_port or 0,
        "dst_ip": event.dst_ip or "0.0.0.0",
        "dst_port": event.dst_port or 0,
        "protocol": (event.protocol or "TCP").lower(),
        "method": event.subtype or "-",
        "host": event.domain or "-",
        "uri": event.uri or "-",
        "user_agent": event.user_agent or "-",
        "status_code": 200,
        "body_size": 1024,
        "tags": [f"sim:{event.attack_type}", f"mitre:{event.mitre_technique_id}"],
        "source": "simulation-engine",
    }


def inject_suricata(events: List[RawEvent]) -> int:
    """Append Suricata-formatted alerts to eve.json."""
    path = _LOG_PATHS["suricata"]
    count = 0
    for ev in events:
        alert = format_suricata_alert(ev)
        if _append_line(path, json.dumps(alert)):
            count += 1
    logger.info("Injected %d/%d Suricata alerts into %s", count, len(events), path)
    return count


def inject_velociraptor(events: List[RawEvent]) -> int:
    """Append Velociraptor-formatted events to events.json."""
    path = _LOG_PATHS["velociraptor"]
    count = 0
    for ev in events:
        formatted = format_velociraptor_event(ev)
        if _append_line(path, json.dumps(formatted)):
            count += 1
    logger.info("Injected %d/%d Velociraptor events into %s", count, len(events), path)
    return count


def inject_arkime(events: List[RawEvent]) -> int:
    """Append Arkime sessions to sessions.log."""
    path = _LOG_PATHS["arkime"]
    count = 0
    for ev in events:
        session = _format_arkime_session(ev)
        if _append_line(path, json.dumps(session)):
            count += 1
    logger.info("Injected %d/%d Arkime sessions into %s", count, len(events), path)
    return count


def inject_zeek(events: List[RawEvent]) -> Dict[str, int]:
    """Append Zeek-formatted events to conn.log, http.log, dns.log, notice.log."""
    log_types = ["conn", "http", "dns", "notice"]
    counts: Dict[str, int] = {}
    for lt in log_types:
        path = _LOG_PATHS[f"zeek_{lt}"]
        c = 0
        for ev in events:
            formatted = format_zeek_log(ev, lt)
            if _append_line(path, json.dumps(formatted)):
                c += 1
        counts[lt] = c
        logger.info("Injected %d/%d Zeek %s log entries into %s", c, len(events), lt, path)
    return counts


def inject_all(events: List[RawEvent]) -> Dict[str, Any]:
    """Inject events into all monitored log files."""
    return {
        "suricata": inject_suricata(events),
        "velociraptor": inject_velociraptor(events),
        "arkime": inject_arkime(events),
        "zeek": inject_zeek(events),
    }

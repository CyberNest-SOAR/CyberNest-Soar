"""TheHive case pipeline — create cases from high-severity events."""

import json
import logging
from typing import Dict, Any, List

from config import get_telemetry_setting
from generators.base import RawEvent

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


def _build_case(event: RawEvent) -> Dict[str, Any]:
    title = f"[SIM-{event.campaign_id}] {event.attack_type.upper()} — {event.subtype or ''}"
    description = (
        f"## Simulated {event.attack_type} alert\n\n"
        f"**Campaign:** {event.campaign_id}\n"
        f"**Event ID:** {event.event_id}\n"
        f"**Timestamp:** {event.timestamp.isoformat()}\n"
        f"**MITRE ATT&CK:** {event.mitre_technique_id} — {event.mitre_technique_name} ({event.mitre_tactic})\n"
        f"**Source IP:** {event.src_ip}\n"
        f"**Destination IP:** {event.dst_ip}\n"
        f"**Hostname:** {event.hostname}\n"
        f"**Process:** {event.process_name}\n"
        f"**User:** {event.username}\n"
        f"**Description:** {event.description}\n"
    )
    return {
        "title": title,
        "description": description,
        "severity": 3 if event.severity and event.severity >= 12 else 2 if event.severity and event.severity >= 8 else 1,
        "tlp": 2,
        "pap": 2,
        "tags": [
            f"simulation:{event.campaign_id}",
            f"attack:{event.attack_type}",
            f"mitre:{event.mitre_technique_id}",
            f"source:{event.tool_target or 'unknown'}",
        ],
        "flag": event.severity and event.severity >= 12,
        "customFields": {
            "eventId": {"string": event.event_id},
            "campaignId": {"string": event.campaign_id},
            "mitreTechnique": {"string": event.mitre_technique_id},
            "ioc": {"string": event.src_ip or ""},
        },
    }


async def export_to_thehive(events: List[RawEvent], api_key: str = None) -> int:
    """Create TheHive cases from high-severity (>=12) events."""
    high_sev = [e for e in events if e.severity and e.severity >= 12]
    if not high_sev:
        logger.info("No high-severity events to create TheHive cases")
        return 0

    url = get_telemetry_setting("thehive", "url", "https://localhost:9000")
    key = api_key or get_telemetry_setting("thehive", "api_key", "")

    if not key:
        logger.warning("TheHive API key not configured — skipping case creation")
        return 0

    if not HAS_HTTPX:
        logger.warning("httpx not installed — skipping TheHive export")
        return 0

    created = 0
    async with httpx.AsyncClient(verify=False, timeout=10) as client:
        for event in high_sev:
            case = _build_case(event)
            try:
                resp = await client.post(
                    f"{url}/api/v1/case",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json=case,
                )
                if resp.status_code in (200, 201):
                    created += 1
                    logger.info("TheHive case created for %s", event.event_id)
                else:
                    logger.warning("TheHive case creation failed: HTTP %d — %s", resp.status_code, resp.text[:200])
            except Exception as e:
                logger.warning("TheHive case creation error for %s: %s", event.event_id, e)

    return created


def format_thehive_cases_json(events: List[RawEvent]) -> str:
    """Export high-severity events as TheHive case JSON (for file-based import)."""
    high_sev = [e for e in events if e.severity and e.severity >= 12]
    return json.dumps([_build_case(e) for e in high_sev], indent=2)

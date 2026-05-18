from datetime import datetime, timezone
from typing import Dict, Any
from schemas.models import UnifiedAlert, HostContext, EnrichmentData
import logging
import uuid

logger = logging.getLogger(__name__)


def _extract_best_ip(source: Dict[str, Any]) -> str:
    """
    Extract the most meaningful IP from a Wazuh alert.

    Priority order:
    1. data.srcip  — the actual attacker/source IP from the alert data
    2. data.dstip  — the destination IP (useful for outbound threat detection)
    3. data.src_ip — alternative field name used by some decoders
    4. data.dst_ip — alternative destination field name
    5. agent.ip    — the Wazuh agent's own IP (usually private, fallback only)
    """
    data = source.get("data", {})
    if isinstance(data, dict):
        for field in ("srcip", "dstip", "src_ip", "dst_ip"):
            ip = data.get(field)
            if ip and ip.strip() and ip.strip().lower() != "unknown":
                return ip.strip()

    # Fallback to agent IP
    agent_ip = source.get("agent", {}).get("ip", "unknown")
    return agent_ip


class Normalizer:
    @staticmethod
    def from_wazuh(raw: Dict[str, Any]) -> UnifiedAlert:
        _source = raw.get("_source", {}) if "_source" in raw else raw
        
        # Extract basic fields
        event_id = _source.get("id", str(uuid.uuid4()))
        timestamp_str = _source.get("@timestamp")
        try:
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                timestamp = datetime.now(timezone.utc)
        except ValueError:
            timestamp = datetime.now(timezone.utc)
            
        rule = _source.get("rule", {})
        description = rule.get("description", "Unknown Alert")
        severity = rule.get("level", 0)
        
        agent = _source.get("agent", {})
        ip_address = _extract_best_ip(_source)

        host_context = HostContext(
            hostname=agent.get("name", "unknown"),
            ip_address=ip_address,
        )

        logger.debug(
            "Normalised alert %s: ip=%s, severity=%s, desc=%.60s",
            event_id, ip_address, severity, description,
        )
        
        return UnifiedAlert(
            event_id=event_id,
            source="wazuh",
            timestamp=timestamp,
            description=description,
            severity=severity,
            host_context=host_context,
            raw_data=raw,
            enrichment_data=EnrichmentData()
        )

    @staticmethod
    def from_suricata(raw: Dict[str, Any]) -> UnifiedAlert:
        event_id = str(uuid.uuid4())
        return UnifiedAlert(
            event_id=event_id,
            source="suricata",
            timestamp=datetime.now(timezone.utc),
            description="Suricata Alert",
            severity=3,
            host_context=HostContext(hostname="unknown", ip_address="unknown"),
            raw_data=raw,
            enrichment_data=EnrichmentData()
        )

normalizer = Normalizer()

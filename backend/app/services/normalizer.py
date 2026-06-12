from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.schemas.models import UnifiedAlert, HostContext, EnrichmentData, SocReasoningData
import logging
import uuid

logger = logging.getLogger(__name__)


def _extract_source(raw: Dict[str, Any]) -> str:
    """Detect whether the alert originated from Suricata or Wazuh."""
    _source = raw.get("_source", raw)
    rule = _source.get("rule", {})
    groups = rule.get("groups", [])
    decoder_name = _source.get("decoder", {}).get("name", "")
    event_type = _source.get("data", {}).get("event_type", "")

    if "suricata" in groups:
        return "suricata"
    if decoder_name == "json" and event_type == "alert":
        return "suricata"
    return "wazuh"


def _extract_event_id(source: Dict[str, Any]) -> str:
    return source.get("id") or str(uuid.uuid4())


def _extract_timestamp(source: Dict[str, Any]) -> datetime:
    ts = source.get("@timestamp") or source.get("timestamp")
    if ts:
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass
    return datetime.now(timezone.utc)


def _extract_severity(source: Dict[str, Any]) -> int:
    return source.get("rule", {}).get("level", 0)


def _extract_description(source: Dict[str, Any], source_type: str) -> str:
    rule = source.get("rule", {})
    desc = rule.get("description", "")
    if desc:
        return desc
    if source_type == "suricata":
        return source.get("data", {}).get("alert", {}).get("signature", "Suricata Alert")
    return "Unknown Alert"


def _extract_best_ip(source: Dict[str, Any]) -> str:
    """
    Extract the most meaningful IP from an alert.

    Priority order:
    1. data.src_ip  — actual attacker/source IP (Suricata field)
    2. data.srcip   — legacy field name
    3. data.dest_ip — destination IP (Suricata field)
    4. data.dstip   — legacy destination field
    5. data.dst_ip  — alternative destination field
    6. agent.ip     — Wazuh agent IP (fallback)
    """
    data = source.get("data", {})
    if isinstance(data, dict):
        for field in ("src_ip", "srcip", "dest_ip", "dstip", "dst_ip"):
            ip = data.get(field)
            if ip and isinstance(ip, str) and ip.strip().lower() not in ("", "unknown"):
                return ip.strip()

    agent_ip = source.get("agent", {}).get("ip", "unknown")
    return agent_ip


def _extract_os_name(source: Dict[str, Any]) -> Optional[str]:
    agent = source.get("agent", {})
    return agent.get("os", {}).get("name") if isinstance(agent.get("os"), dict) else None


def _extract_soc_reasoning(source: Dict[str, Any]) -> SocReasoningData:
    """Extract SOC reasoning fields from pipeline-format raw_data."""
    def _get(*keys):
        for k in keys:
            v = source.get(k)
            if v is not None:
                return v
            data = source.get("data", {})
            if isinstance(data, dict):
                v = data.get(k)
                if v is not None:
                    return v
        return None

    return SocReasoningData(
        asset_criticality=_get("asset_criticality"),
        analyst_verdict=_get("analyst_verdict"),
        analyst_notes=_get("analyst_notes"),
        analyst_assigned=_get("analyst_assigned"),
        escalation_level=_get("escalation_level"),
        playbook_outcome=_get("playbook_outcome"),
        suppression_hit=_get("suppression_hit"),
        true_positive=_get("true_positive"),
        noise=_get("noise"),
        mitre_technique_id=_get("mitre_technique_id"),
        mitre_technique_name=_get("mitre_technique_name"),
        mitre_tactic=_get("mitre_tactic"),
        attack_type=_get("attack_type"),
        campaign_id=_get("campaign_id"),
        cluster_id=_get("cluster_id"),
        confidence=_get("confidence"),
        risk_adjusted_priority=_get("risk_adjusted_priority"),
        asset_value=_get("asset_value"),
        host_role=_get("host_role"),
        department=_get("department"),
        business_unit=_get("business_unit"),
        owner_team=_get("owner_team"),
        user_role=_get("user_role"),
        environment_context=_get("environment_context"),
        closure_reason=_get("closure_reason"),
        repeated_behavior_score=_get("repeated_behavior_score"),
        similar_alerts_last_hour=_get("similar_alerts_last_hour"),
        historically_seen=_get("historically_seen"),
        historical_false_positive_rate=_get("historical_false_positive_rate"),
        recurring_alert=_get("recurring_alert"),
        prior_case_count=_get("prior_case_count"),
        timeline_position=_get("timeline_position"),
        remediation_action=_get("remediation_action") or _get("recommended_action", "playbook_action"),
        dataset_source=_get("dataset_source") or source.get("dataset_source"),
    )


def _build_alert(
    raw: Dict[str, Any],
    source_type: str,
    event_id: str,
    timestamp: datetime,
    description: str,
    severity: int,
    host_context: HostContext,
) -> UnifiedAlert:
    """Build a UnifiedAlert, storing only _source (not the full ES hit) as raw_data."""
    clean_raw = raw.get("_source", raw)

    logger.debug(
        "Normalised %s alert %s: ip=%s, severity=%s, desc=%.60s",
        source_type, event_id, host_context.ip_address, severity, description,
    )

    return UnifiedAlert(
        event_id=event_id,
        source=source_type,
        timestamp=timestamp,
        description=description,
        severity=severity,
        host_context=host_context,
        raw_data=clean_raw,
        enrichment_data=EnrichmentData(),
        soc_reasoning=_extract_soc_reasoning(clean_raw),
    )


class Normalizer:
    @staticmethod
    def from_wazuh(raw: Dict[str, Any]) -> UnifiedAlert:
        _source = raw.get("_source", raw) if "_source" in raw else raw

        event_id = _extract_event_id(_source)
        timestamp = _extract_timestamp(_source)
        severity = _extract_severity(_source)
        source_type = _extract_source(raw)
        description = _extract_description(_source, source_type)
        ip_address = _extract_best_ip(_source)

        agent = _source.get("agent", {})

        host_context = HostContext(
            hostname=agent.get("name", "unknown"),
            ip_address=ip_address,
            mac_address=agent.get("mac", None),
            os_name=_extract_os_name(_source),
        )

        return _build_alert(
            raw=raw,
            source_type=source_type,
            event_id=event_id,
            timestamp=timestamp,
            description=description,
            severity=severity,
            host_context=host_context,
        )

    @staticmethod
    def from_suricata(raw: Dict[str, Any]) -> UnifiedAlert:
        _source = raw.get("_source", raw) if "_source" in raw else raw

        event_id = _extract_event_id(_source)
        timestamp = _extract_timestamp(_source)

        alert_data = _source.get("data", {})
        alert_info = alert_data.get("alert", {})
        description = alert_info.get("signature", "Suricata Alert")
        severity = int(alert_info.get("severity", 3))
        ip_address = _extract_best_ip(_source)

        host_context = HostContext(
            hostname="unknown",
            ip_address=ip_address,
        )

        return _build_alert(
            raw=raw,
            source_type="suricata",
            event_id=event_id,
            timestamp=timestamp,
            description=description,
            severity=severity,
            host_context=host_context,
        )


normalizer = Normalizer()

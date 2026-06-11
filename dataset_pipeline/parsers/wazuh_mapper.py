"""
wazuh_mapper.py — Converts live Wazuh/OpenSearch alerts into the
dataset_pipeline UnifiedAlert format so that AI models trained on
pipeline data can consume live alerts with the same schema.

Usage:
    from parsers.wazuh_mapper import wazuh_to_unified_alert

    # From an OpenSearch hit _source dict
    alert = wazuh_to_unified_alert(opensearch_hit["_source"])

    # After enrichment (backend EnrichmentData)
    from parsers.wazuh_mapper import apply_enrichment_flat
    apply_enrichment_flat(alert, backend_enrichment_data)
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)

# Suricata/Wazuh field name variants to check
_SRC_IP_FIELDS = ["src_ip", "srcip", "src_addr"]
_DST_IP_FIELDS = ["dst_ip", "dstip", "dest_ip", "dst_addr"]
_SRC_PORT_FIELDS = ["src_port", "sport", "src_port"]
_DST_PORT_FIELDS = ["dst_port", "dport", "dst_port"]
_PROTO_FIELDS = ["protocol", "proto"]


def _deep_get(d: dict, *keys, default=None):
    """Safely traverse nested dicts."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return default
    return d if d is not None else default


def _first_of(data: dict, *keys):
    """Return the first non-None value from a list of keys."""
    for k in keys:
        v = data.get(k)
        if v is not None:
            return v
    return None


def _extract_ip(data: dict, keys: List[str]) -> Optional[str]:
    for k in keys:
        v = data.get(k)
        if v and isinstance(v, str) and v.strip().lower() not in ("", "unknown"):
            return v.strip()
    return None


def wazuh_to_unified_alert(source: Dict[str, Any]) -> UnifiedAlert:
    """
    Convert a Wazuh OpenSearch document ``_source`` into a
    dataset_pipeline ``UnifiedAlert`` (flat 100+ field schema).

    Handles Wazuh-native alerts (rule/agent/data.*) and direct
    sensor logs (Suricata eve.json, Zeek, Velociraptor).
    """
    data = source.get("data", {}) or {}
    if not isinstance(data, dict):
        data = {}

    rule = source.get("rule", {}) or {}
    agent = source.get("agent", {}) or {}
    decoder = source.get("decoder", {}) or {}

    # Source detection
    decoder_name = decoder.get("name", "")
    event_type_data = data.get("event_type", "")
    rule_groups = rule.get("groups", [])
    if "suricata" in rule_groups or (decoder_name == "json" and event_type_data == "alert"):
        dataset_source = "suricata"
    elif "zeek" in rule_groups or decoder_name == "zeek-json-events":
        dataset_source = "zeek"
    elif decoder_name in ("velociraptor-json", "arkime-json"):
        dataset_source = decoder_name.rstrip("-json").replace("-", "_")
    else:
        dataset_source = "wazuh"

    # Timestamp
    ts = source.get("@timestamp") or source.get("timestamp")
    if isinstance(ts, str):
        try:
            timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            timestamp = datetime.now(timezone.utc)
    elif isinstance(ts, datetime):
        timestamp = ts
    else:
        timestamp = datetime.now(timezone.utc)

    # Event ID
    event_id = source.get("id") or source.get("event_id") or str(uuid.uuid4())

    # IPs
    src_ip = _extract_ip(data, _SRC_IP_FIELDS) or _extract_ip(source, _SRC_IP_FIELDS)
    dst_ip = _extract_ip(data, _DST_IP_FIELDS) or _extract_ip(source, _DST_IP_FIELDS)
    if not src_ip:
        src_ip = agent.get("ip")

    # Ports
    src_port = _first_of(data, *["src_port", "sport", "srcport"])
    dst_port = _first_of(data, *["dst_port", "dport", "dstport"])
    protocol = _first_of(data, *["protocol", "proto"])

    # Alert fields
    alert_info = data.get("alert", {}) or {}
    alert_signature = (
        alert_info.get("signature")
        or data.get("alert_signature")
        or rule.get("description", "")
    )
    alert_severity = (
        alert_info.get("severity")
        or data.get("alert_severity")
        or rule.get("level", 0)
    )
    alert_category = (
        alert_info.get("category")
        or data.get("alert_category")
        or (rule_groups[0] if rule_groups else None)
    )

    # Process fields
    process = data.get("process", {}) or {}
    process_name = process.get("name") or data.get("process_name")
    parent_process = process.get("parent") or data.get("parent_process")
    command_line = data.get("command_line") or data.get("cmdline")

    # File hashes
    file_hash_raw = data.get("file_hash", {}) or {}
    file_hash = (
        file_hash_raw.get("sha256")
        or file_hash_raw.get("sha1")
        or file_hash_raw.get("md5")
        or data.get("file_hash")
    )

    # HTTP fields
    http = data.get("http", {}) or {}
    http_method = http.get("http_method") or http.get("method")
    http_uri = http.get("http_uri") or http.get("uri") or data.get("uri")
    http_user_agent = http.get("http_user_agent") or http.get("user_agent") or data.get("user_agent")
    http_status = http.get("http_status") or http.get("status_code") or http.get("status")

    # DNS / TLS
    dns = data.get("dns", {}) or {}
    dns_query = dns.get("dns_query") or dns.get("query") or data.get("dns_query") or data.get("domain")
    dns_answer = dns.get("dns_answer") or dns.get("answers")
    tls = data.get("tls", {}) or data.get("ssl", {})
    tls_sni = tls.get("tls_sni") or tls.get("sni") or tls.get("server_name")

    # MITRE from data block or alert
    mitre_id = data.get("mitre", {}).get("technique_id") or data.get("mitre_technique_id")
    mitre_name = data.get("mitre", {}).get("technique_name") or data.get("mitre_technique_name")
    mitre_tactic = data.get("mitre", {}).get("tactic") or data.get("mitre_tactic")

    # Attack type (from simulation engine)
    attack_type = data.get("attack_type")

    # True positive / noise (from simulation engine)
    true_positive = data.get("true_positive")
    noise = data.get("noise")

    # Simulation metadata
    simulation = source.get("simulation", {}) or {}
    campaign_id = simulation.get("campaign_id") or data.get("campaign_id")
    is_simulated = bool(simulation) or bool(data.get("event_id", "").startswith("sim-"))

    # Hostnames
    src_hostname = data.get("hostname") or agent.get("name")
    dst_hostname = agent.get("name") if not src_hostname else None

    # User
    src_user = data.get("username") or data.get("src_user")

    # GeoIP (from enrichment in Wazuh or simulation)
    geoip_src_country = data.get("geoip", {}).get("src_country") or data.get("geoip_src_country")
    geoip_src_asn = data.get("geoip", {}).get("src_asn") or data.get("geoip_src_asn")
    geoip_dst_country = data.get("geoip", {}).get("dst_country") or data.get("geoip_dst_country")
    geoip_dst_asn = data.get("geoip", {}).get("dst_asn") or data.get("geoip_dst_asn")

    # Bytes / duration
    bytes_sent = data.get("bytes_sent") or data.get("bytes_out")
    bytes_received = data.get("bytes_received") or data.get("bytes_in")
    duration = data.get("duration")

    # IOC fields
    ioc_domain = data.get("domain") or dns_query
    ioc_url = data.get("uri") or http_uri
    ioc_hash = data.get("file_hash") or file_hash

    alert = UnifiedAlert(
        event_id=event_id,
        timestamp=timestamp,
        dataset_source=dataset_source,
        event_type=data.get("event_type", "alert"),
        # Network
        src_ip=src_ip,
        src_port=src_port,
        dst_ip=dst_ip,
        dst_port=dst_port,
        protocol=protocol,
        src_hostname=src_hostname,
        dst_hostname=dst_hostname,
        src_user=src_user,
        # Process
        process_name=process_name,
        command_line=command_line,
        parent_process=parent_process,
        file_hash=file_hash,
        # Alert metadata
        alert_signature=alert_signature,
        alert_severity=alert_severity,
        alert_category=alert_category,
        # MITRE / attack type
        attack_type=attack_type,
        mitre_technique_id=mitre_id,
        mitre_technique_name=mitre_name,
        mitre_tactic=mitre_tactic,
        # Labels
        true_positive=true_positive,
        noise=noise,
        confidence=data.get("confidence"),
        # Campaign
        campaign_id=campaign_id,
        # HTTP / DNS / TLS
        http_method=http_method,
        http_uri=http_uri,
        http_user_agent=http_user_agent,
        http_status=http_status,
        dns_query=dns_query,
        dns_answer=dns_answer,
        tls_sni=tls_sni,
        # IOC
        ioc_domain=ioc_domain,
        ioc_url=ioc_url,
        ioc_hash=ioc_hash,
        # GeoIP
        geoip_src_country=geoip_src_country,
        geoip_src_asn=geoip_src_asn,
        geoip_dst_country=geoip_dst_country,
        geoip_dst_asn=geoip_dst_asn,
        # Network stats
        bytes_sent=bytes_sent,
        bytes_received=bytes_received,
        duration=duration,
        # SOC reasoning defaults for live data (see apply_soc_reasoning_defaults)
        asset_criticality="medium",
        host_role="unknown",
        department="unknown",
        business_unit="unknown",
        compliance_scope="unknown",
        user_role="unknown",
        mfa_used=False,
        authentication_method="unknown",
        integrity_level="unknown",
        signed_binary=False,
        # Extra context
        extra_fields={
            "source_wazuh_rule_id": rule.get("id"),
            "source_wazuh_rule_level": rule.get("level"),
            "source_decoder": decoder_name,
            "source_location": source.get("location"),
            "is_simulated": is_simulated,
            "agent_id": agent.get("id"),
            "agent_name": agent.get("name"),
            "agent_os": agent.get("os", {}).get("name") if isinstance(agent.get("os"), dict) else None,
        },
    )

    return alert


def apply_enrichment_flat(alert: UnifiedAlert, enrichment_data: Any) -> None:
    """
    Map backend ``EnrichmentData`` (nested dicts) to the dataset_pipeline's
    flat enrichment fields (``enrichment_vt_score``, ``enrichment_abuse_score``,
    etc.) so AI models see the same schema as training data.
    """
    vt = getattr(enrichment_data, "virus_total", None) or {}
    alert.enrichment_vt_score = vt.get("score") if isinstance(vt, dict) else None

    abuse = getattr(enrichment_data, "abuse_ipdb", None) or {}
    alert.enrichment_abuse_score = abuse.get("score") if isinstance(abuse, dict) else None

    misp = getattr(enrichment_data, "misp", None) or {}
    alert.enrichment_misp_matches = misp.get("matches") if isinstance(misp, dict) else None

    epss = getattr(enrichment_data, "epss", None) or {}
    alert.enrichment_epss_score = epss.get("score") if isinstance(epss, dict) else None

    nvd = getattr(enrichment_data, "nvd", None) or {}
    alert.enrichment_cvss_score = nvd.get("cvss") if isinstance(nvd, dict) else None

    tags = getattr(enrichment_data, "tags", None) or []
    alert.extra_fields["enrichment_tags"] = tags
    alert.extra_fields["enrichment_risk_score"] = getattr(enrichment_data, "risk_score", None)


def batch_map_wazuh_hits(hits: List[Dict[str, Any]]) -> List[UnifiedAlert]:
    """Map a list of OpenSearch hits to UnifiedAlerts."""
    return [wazuh_to_unified_alert(h.get("_source", h)) for h in hits]

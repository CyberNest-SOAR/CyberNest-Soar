"""
UnifiedAlert schema — canonical SOC event format for the dataset pipeline.
All dataset parsers convert their native formats into this schema.
Includes full SOC reasoning fields for LLM training and enterprise SOAR.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


@dataclass
class UnifiedAlert:
    event_id: str
    timestamp: datetime
    dataset_source: str
    event_type: str

    src_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_ip: Optional[str] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = None

    src_hostname: Optional[str] = None
    dst_hostname: Optional[str] = None
    src_user: Optional[str] = None
    dst_user: Optional[str] = None
    process_name: Optional[str] = None
    command_line: Optional[str] = None
    file_name: Optional[str] = None
    file_hash: Optional[str] = None
    registry_key: Optional[str] = None
    service_name: Optional[str] = None
    image_path: Optional[str] = None

    alert_signature: Optional[str] = None
    alert_severity: Optional[int] = None
    alert_category: Optional[str] = None
    alert_action: Optional[str] = None

    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None
    duration: Optional[float] = None
    packets: Optional[int] = None

    attack_type: Optional[str] = None
    mitre_technique_id: Optional[str] = None
    mitre_technique_name: Optional[str] = None
    mitre_tactic: Optional[str] = None
    confidence: Optional[float] = None
    true_positive: Optional[bool] = None
    noise: Optional[bool] = None

    ioc_ip: Optional[str] = None
    ioc_domain: Optional[str] = None
    ioc_url: Optional[str] = None
    ioc_hash: Optional[str] = None

    http_method: Optional[str] = None
    http_uri: Optional[str] = None
    http_user_agent: Optional[str] = None
    http_referrer: Optional[str] = None
    http_status: Optional[int] = None

    dns_query: Optional[str] = None
    dns_answer: Optional[str] = None
    dns_type: Optional[str] = None

    tls_sni: Optional[str] = None
    tls_version: Optional[str] = None
    ja3_hash: Optional[str] = None

    geoip_src_country: Optional[str] = None
    geoip_src_asn: Optional[str] = None
    geoip_dst_country: Optional[str] = None
    geoip_dst_asn: Optional[str] = None

    enrichment_vt_score: Optional[int] = None
    enrichment_abuse_score: Optional[int] = None
    enrichment_misp_matches: Optional[List[str]] = None
    enrichment_epss_score: Optional[float] = None
    enrichment_cvss_score: Optional[float] = None

    analyst_verdict: Optional[str] = None
    analyst_assigned: Optional[str] = None
    analyst_notes: Optional[str] = None
    suppression_hit: Optional[bool] = None
    escalation_level: Optional[str] = None
    playbook_outcome: Optional[str] = None

    cluster_id: Optional[str] = None
    campaign_id: Optional[str] = None
    attack_chain_stage: Optional[int] = None

    # === SOC REASONING FIELDS (Steps 1-8) ===

    # STEP 1 — SOC Operational Context
    closure_reason: Optional[str] = None
    escalation_reason: Optional[str] = None
    suppression_reason: Optional[str] = None
    playbook_action: Optional[str] = None
    playbook_success: Optional[bool] = None
    recommended_action: Optional[str] = None
    risk_adjusted_priority: Optional[int] = None

    # STEP 2 — Environmental Context
    maintenance_window: Optional[bool] = None
    patch_window: Optional[bool] = None
    known_admin_activity: Optional[bool] = None
    vulnerability_scan: Optional[bool] = None
    scheduled_backup: Optional[bool] = None
    business_hours: Optional[bool] = None
    weekend_activity: Optional[bool] = None
    environment_context: Optional[str] = None

    # STEP 3 — Asset & Business Context
    asset_criticality: Optional[str] = None
    host_role: Optional[str] = None
    department: Optional[str] = None
    business_unit: Optional[str] = None
    owner_team: Optional[str] = None
    compliance_scope: Optional[str] = None
    asset_value: Optional[int] = None

    # STEP 4 — Identity & Process Context
    user_role: Optional[str] = None
    mfa_used: Optional[bool] = None
    authentication_method: Optional[str] = None
    parent_process: Optional[str] = None
    process_hash: Optional[str] = None
    integrity_level: Optional[str] = None
    signed_binary: Optional[bool] = None

    # STEP 5 — Temporal & Correlation
    timeline_position: Optional[str] = None
    previous_alert_id: Optional[str] = None
    next_alert_id: Optional[str] = None
    session_id: Optional[str] = None
    repeated_behavior_score: Optional[int] = None
    similar_alerts_last_hour: Optional[int] = None
    attack_burst_id: Optional[str] = None
    alert_storm_id: Optional[str] = None

    # STEP 6 — Historical Memory
    historically_seen: Optional[bool] = None
    historical_false_positive_rate: Optional[float] = None
    recurring_alert: Optional[bool] = None
    prior_case_count: Optional[int] = None

    raw_log: Optional[str] = None
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_malicious(self) -> bool:
        return self.true_positive is True and (self.alert_severity or 0) >= 5

    @property
    def severity_label(self) -> str:
        if not self.alert_severity:
            return "info"
        if self.alert_severity >= 12:
            return "critical"
        if self.alert_severity >= 8:
            return "high"
        if self.alert_severity >= 5:
            return "medium"
        return "low"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat() if self.timestamp else None
        return {k: v for k, v in d.items() if v is not None or k in ("extra_fields",)}

    def to_elasticsearch_doc(self) -> Dict[str, Any]:
        doc = self.to_dict()
        doc["@timestamp"] = doc.pop("timestamp", None)
        return doc

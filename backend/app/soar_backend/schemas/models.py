from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- ENTITY MODELS (New) ---

class NetworkSession(BaseModel):
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = None
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None
    session_duration: Optional[float] = None
    connection_state: Optional[str] = None
    service: Optional[str] = None

class EndpointProcess(BaseModel):
    pid: Optional[int] = None
    ppid: Optional[int] = None
    process_name: Optional[str] = None
    parent_process_name: Optional[str] = None
    command_line: Optional[str] = None
    binary_path: Optional[str] = None
    binary_hash_md5: Optional[str] = None
    binary_hash_sha1: Optional[str] = None
    binary_hash_sha256: Optional[str] = None
    user: Optional[str] = None
    integrity_level: Optional[str] = None
    signed: Optional[bool] = None
    signature_status: Optional[str] = None

class AssetContext(BaseModel):
    hostname: str
    ip_address: str
    mac_address: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    os_patch_level: Optional[str] = None
    host_role: Optional[str] = None
    department: Optional[str] = None
    business_unit: Optional[str] = None
    owner_team: Optional[str] = None
    asset_value: Optional[int] = None
    criticality: Optional[str] = None
    agent_status: Optional[str] = None  # online, offline, tampered, uninstalled
    last_seen: Optional[datetime] = None
    vulnerabilities: Optional[List[str]] = Field(default_factory=list, description="List of active CVE IDs")
    vulnerability_count: Optional[int] = None

class ThreatContext(BaseModel):
    attack_chain_stage: Optional[str] = None  # Reconnaissance, Weaponization, Delivery, Exploitation, Installation, C2, Actions
    campaign_id: Optional[str] = None
    mitre_tactic: Optional[str] = None
    mitre_technique_id: Optional[str] = None
    mitre_technique_name: Optional[str] = None
    mitre_group: Optional[str] = None
    ioc_ips: Optional[List[str]] = Field(default_factory=list)
    ioc_domains: Optional[List[str]] = Field(default_factory=list)
    ioc_hashes: Optional[List[str]] = Field(default_factory=list)
    ioc_urls: Optional[List[str]] = Field(default_factory=list)
    false_positive_indicators: Optional[List[str]] = Field(default_factory=list)

class TimelineEvent(BaseModel):
    containment_timestamp: Optional[datetime] = None
    escalation_timestamp: Optional[datetime] = None
    closure_timestamp: Optional[datetime] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    timeline_position: Optional[str] = None
    attack_chain_stage: Optional[str] = None

# --- CORE SCHEMAS ---

class HostContext(BaseModel):
    hostname: str
    ip_address: str
    mac_address: Optional[str] = None
    os_name: Optional[str] = None

class EnrichmentData(BaseModel):
    tags: List[str] = Field(default_factory=list)
    risk_score: Optional[int] = None
    debug_info: Dict[str, str] = Field(default_factory=dict)

    virus_total: Optional[Dict[str, Any]] = None
    abuse_ipdb: Optional[Dict[str, Any]] = None
    misp: Optional[Dict[str, Any]] = None
    epss: Optional[Dict[str, Any]] = None
    nvd: Optional[Dict[str, Any]] = None
    cisa_kev: Optional[Dict[str, Any]] = None
    urlhaus: Optional[Dict[str, Any]] = None
    alienvault_otx: Optional[Dict[str, Any]] = None

class SocReasoningData(BaseModel):
    asset_criticality: Optional[str] = None
    analyst_verdict: Optional[str] = None
    analyst_notes: Optional[str] = None
    analyst_assigned: Optional[str] = None
    escalation_level: Optional[str] = None
    playbook_outcome: Optional[str] = None
    suppression_hit: Optional[bool] = None
    true_positive: Optional[bool] = None
    noise: Optional[bool] = None
    prediction: Optional[str] = None
    confidence_level: Optional[str] = None
    mitre_technique_id: Optional[str] = None
    mitre_technique_name: Optional[str] = None
    mitre_tactic: Optional[str] = None
    attack_type: Optional[str] = None
    campaign_id: Optional[str] = None
    cluster_id: Optional[str] = None
    confidence: Optional[float] = None
    risk_adjusted_priority: Optional[int] = None
    asset_value: Optional[int] = None
    host_role: Optional[str] = None
    department: Optional[str] = None
    business_unit: Optional[str] = None
    owner_team: Optional[str] = None
    user_role: Optional[str] = None
    environment_context: Optional[str] = None
    closure_reason: Optional[str] = None
    repeated_behavior_score: Optional[int] = None
    similar_alerts_last_hour: Optional[int] = None
    historically_seen: Optional[bool] = None
    historical_false_positive_rate: Optional[float] = None
    recurring_alert: Optional[bool] = None
    prior_case_count: Optional[int] = None
    timeline_position: Optional[str] = None
    remediation_action: Optional[str] = None
    dataset_source: Optional[str] = None

class UnifiedAlert(BaseModel):
    event_id: str
    source: str
    timestamp: datetime
    description: str
    severity: int
    host_context: HostContext
    raw_data: Dict[str, Any]
    enrichment_data: EnrichmentData = Field(default_factory=EnrichmentData)
    soc_reasoning: SocReasoningData = Field(default_factory=SocReasoningData)

    # New entity-embedded fields for enriched context
    network_session: Optional[NetworkSession] = None
    endpoint_process: Optional[EndpointProcess] = None
    asset_context: Optional[AssetContext] = None
    threat_context: Optional[ThreatContext] = None
    timeline: Optional[TimelineEvent] = None

# --- TEAM 0: CORE DATA ---
class AlertStats(BaseModel):
    by_severity: Dict[str, int]
    top_rules: List[Dict[str, str]]

# --- TEAM 1: RISK SCORING ---
class RiskScoreRequest(BaseModel):
    alert: UnifiedAlert

class RiskBatchRequest(BaseModel):
    alerts: List[UnifiedAlert]

class RiskScoreResponse(BaseModel):
    event_id: str
    risk_score: int
    priority: str
    predicted_analyst_verdict: str
    confidence: float
    features: Dict[str, float]

# --- TEAM 2: PATCH RECOMMENDATION ---
class Recommendation(BaseModel):
    cve: str
    cvss: float
    epss: float
    priority: str
    action: str
    exploit_likelihood: Optional[float] = None
    time_to_exploit_days: Optional[float] = None
    attack_patterns: Optional[List[str]] = None
    ml_confidence: Optional[float] = None

class PatchResponse(BaseModel):
    host: str
    recommendations: List[Recommendation]
    analysis_timestamp: Optional[datetime] = None

# --- TEAM 3: FILTERING & NOISE ---
class FilterRequest(BaseModel):
    alerts: List[UnifiedAlert]

class FilterResult(BaseModel):
    alert_id: str
    classification: str
    confidence: float
    summary: Optional[str] = None

class ClusterItem(BaseModel):
    type: str
    count: int

class ClusterResponse(BaseModel):
    clusters: List[ClusterItem]

# --- TEAM 4: PLAYBOOKS ---
class PlaybookDecisionRequest(BaseModel):
    alert: UnifiedAlert

class PlaybookDecisionResponse(BaseModel):
    action: str
    confidence: float
    automation_level: str
    reason: str = ""

class PlaybookExecuteRequest(BaseModel):
    action: str
    target: str

# --- TEAM 5: THREAT INTEL ---
class IntelResponse(BaseModel):
    ioc: str
    malicious: bool
    reputation: int
    sources: List[str]

class CveDetails(BaseModel):
    cve: str
    cvss: float
    description: str

class MispSyncResponse(BaseModel):
    status: str
    synced_events: int
    events: List[Dict[str, Any]] = Field(default_factory=list)

# --- METRICS & CASES ---
class HygieneBreakdown(BaseModel):
    patch: int
    auth: int
    config: int
    integrity: int
    threat: int

class HygieneScore(BaseModel):
    score: int
    breakdown: HygieneBreakdown

class CaseCreate(BaseModel):
    title: str
    severity: int = 2
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    event_id: str = ""
    source_ip: str = ""
    destination_ip: str = ""
    attack_type: str = ""
    mitre_tactic: str = ""

# --- TIMELINE & SLA MODELS ---
class SlaMetrics(BaseModel):
    triage_sla_minutes: int = 15
    containment_sla_minutes: int = 60
    triage_breach_count: int = 0
    containment_breach_count: int = 0
    avg_triage_time_minutes: Optional[float] = None
    avg_containment_time_minutes: Optional[float] = None
    mttd_minutes: Optional[float] = None
    mttr_minutes: Optional[float] = None

class IocLookupRequest(BaseModel):
    ioc: str
    ioc_type: str  # "ip", "domain", "hash", "url"

class IocLookupResult(BaseModel):
    ioc: str
    malicious: bool
    reputation: int
    sources: List[str]
    enrichment: Dict[str, Any] = Field(default_factory=dict)

# --- THREAT INTEL PROVIDER MODELS ---
class ThreatIntelProvider(BaseModel):
    id: str
    name: str
    enabled: bool
    api_key_configured: bool
    health_status: str = "unknown"  # healthy, degraded, offline
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None

class ThreatIntelProviderConfig(BaseModel):
    provider_id: str
    name: str
    api_key: str = ""
    base_url: Optional[str] = None
    enabled: bool = True

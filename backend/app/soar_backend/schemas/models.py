from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- CORE SCHEMAS ---
class HostContext(BaseModel):
    hostname: str
    ip_address: str
    mac_address: Optional[str] = None
    os_name: Optional[str] = None

class EnrichmentData(BaseModel):
    tags: List[str] = Field(default_factory=list)
    risk_score: Optional[int] = None   # Populated by Team 1 risk-scoring service
    debug_info: Dict[str, str] = Field(
        default_factory=dict,
        description="Per-service error/debug messages captured during enrichment.",
    )

    # Per-service enrichment blocks — each populated by its respective
    # lookup when data is found.  None = not enriched / no data.
    virus_total: Optional[Dict[str, Any]] = None      # {score, malicious, suspicious, harmless}
    abuse_ipdb: Optional[Dict[str, Any]] = None         # {score, total_reports}
    misp: Optional[Dict[str, Any]] = None               # {matches: [uuid, ...], count}
    epss: Optional[Dict[str, Any]] = None               # {score, percentile}
    nvd: Optional[Dict[str, Any]] = None                # {cvss, severity}
    cisa_kev: Optional[Dict[str, Any]] = None             # {cve, dateAdded, shortDescription, ...}
    urlhaus: Optional[Dict[str, Any]] = None              # {matched, url_status, threat, tags}
    alienvault_otx: Optional[Dict[str, Any]] = None        # {matched, pulse_count, pulses, ...}

class UnifiedAlert(BaseModel):
    event_id: str
    source: str  # e.g., 'wazuh', 'suricata'
    timestamp: datetime
    description: str
    severity: int
    host_context: HostContext
    raw_data: Dict[str, Any]
    enrichment_data: EnrichmentData = Field(default_factory=EnrichmentData)

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
    confidence: float
    features: Dict[str, float]

# --- TEAM 2: PATCH RECOMMENDATION ---
class Recommendation(BaseModel):
    cve: str
    cvss: float
    epss: float
    priority: str
    action: str

class PatchResponse(BaseModel):
    host: str
    recommendations: List[Recommendation]

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
    reason: str = ""  # Human-readable explanation of the decision

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
    severity: str
    event_id: str

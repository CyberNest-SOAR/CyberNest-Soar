from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

# --- TEAM 0: CORE DATA ---
class AlertRule(BaseModel):
    id: str
    description: str
    level: int

class AlertAgent(BaseModel):
    name: str
    ip: str

class Alert(BaseModel):
    id: str
    timestamp: datetime
    rule: AlertRule
    agent: AlertAgent

class AlertStats(BaseModel):
    by_severity: Dict[str, int]
    top_rules: List[Dict[str, str]]

# --- TEAM 1: RISK SCORING ---
class RiskScoreRequest(BaseModel):
    event_id: str

class RiskBatchRequest(BaseModel):
    event_ids: List[str]

class RiskScoreResponse(BaseModel):
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
    alert_ids: List[str]

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
    event_id: str

class PlaybookDecisionResponse(BaseModel):
    action: str
    confidence: float
    automation_level: str

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

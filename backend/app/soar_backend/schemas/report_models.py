from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class ReportType(str, Enum):
    EXECUTIVE = "executive"
    SOC_OPERATIONS = "soc_operations"
    INCIDENT = "incident"
    THREAT_INTEL = "threat_intel"
    HYGIENE = "hygiene"
    SHIFT_HANDOVER = "shift_handover"


class ReportFormat(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"


class TimePeriod(BaseModel):
    start: datetime
    end: datetime
    label: str = ""


class Finding(BaseModel):
    finding: str
    confidence: float
    severity: str = "medium"
    recommended_action: str = ""


class TrendPoint(BaseModel):
    date: str
    value: float


class CriticalIncident(BaseModel):
    incident_id: str
    title: str
    severity: int
    status: str = "open"
    mttr_hours: float = 0
    attack_type: str = ""
    affected_assets: list[str] = []
    business_impact: str = ""


class ExecutiveSecurityReport(BaseModel):
    report_id: str
    report_type: str = "executive_security"
    generated_at: datetime
    period: TimePeriod
    organization: dict = {}
    executive_summary: dict = {}
    ai_insights: dict = {}
    risk_overview: dict = {}
    security_trends: dict = {}
    critical_incidents: list[CriticalIncident] = []


class SocOperationsReport(BaseModel):
    report_id: str
    report_type: str = "soc_operations"
    generated_at: datetime
    period: TimePeriod
    alert_overview: dict = {}
    analyst_performance: dict = {}
    escalation_analysis: dict = {}
    detection_effectiveness: dict = {}
    noise_reduction: dict = {}
    automation_performance: dict = {}
    case_metrics: dict = {}
    workload_analysis: dict = {}
    recommendations: list[str] = []


class IncidentIntelligenceReport(BaseModel):
    report_id: str
    report_type: str = "incident_intelligence"
    generated_at: datetime
    incident_id: str
    incident_summary: dict = {}
    attack_narrative: dict = {}
    timeline_reconstruction: dict = {}
    mitre_mapping: list[dict] = []
    ioc_analysis: dict = {}
    impact_assessment: dict = {}
    root_cause: str = ""
    containment_actions: list[dict] = []
    lessons_learned: list[str] = []


class ThreatIntelligenceReport(BaseModel):
    report_id: str
    report_type: str = "threat_intelligence"
    generated_at: datetime
    period: TimePeriod
    ioc_overview: dict = {}
    internal_ioc_hits: dict = {}
    active_campaigns: list[dict] = []
    threat_actor_correlations: dict = {}
    feed_health: dict = {}
    ioc_trends: list[TrendPoint] = []
    intelligence_gaps: list[str] = []
    recommended_actions: list[str] = []


class ITHygieneReport(BaseModel):
    report_id: str
    report_type: str = "it_hygiene"
    generated_at: datetime
    period: TimePeriod
    hygiene_score: dict = {}
    patch_compliance: dict = {}
    vulnerability_exposure: dict = {}
    authentication_health: dict = {}
    configuration_health: dict = {}
    endpoint_health: dict = {}
    asset_risk_ranking: list[dict] = []
    remediation_recommendations: list[dict] = []
    predicted_risk_reduction: dict = {}


class ShiftHandoverReport(BaseModel):
    report_id: str
    report_type: str = "shift_handover"
    generated_at: datetime
    shift: dict = {}
    new_incidents: dict = {}
    resolved_incidents: dict = {}
    open_incidents: dict = {}
    escalations: dict = {}
    threat_intel_hits: dict = {}
    playbook_executions: dict = {}
    analyst_notes: list[dict] = []
    shift_summary: str = ""


class ReportSchedule(BaseModel):
    id: Optional[str] = None
    report_type: ReportType
    name: str
    description: str = ""
    cron_expression: str
    format: ReportFormat = ReportFormat.PDF
    recipients: list[dict] = []
    filters: dict = {}
    enabled: bool = True
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None


class ReportLogEntry(BaseModel):
    id: str
    report_type: ReportType
    schedule_id: Optional[str] = None
    period_start: datetime
    period_end: datetime
    format: ReportFormat
    status: str = "pending"
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    generated_at: datetime
    delivery_status: str = "pending"

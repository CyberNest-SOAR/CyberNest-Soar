from pydantic import BaseModel, Field

class AlertRequest(BaseModel):
    alert_id: str = Field(..., description="Unique identifier of the Wazuh alert")
    alert_severity: int = Field(..., description="Raw severity score of the alert (e.g. 1-15)")
    enrichment_vt_score: float = Field(..., description="VirusTotal malicious score/percentage")
    enrichment_abuse_score: float = Field(..., description="AbuseIPDB abuse confidence score")
    asset_criticality: str = Field(..., description="Asset criticality classification (e.g. high, medium, low)")
    similar_alerts_last_hour: int = Field(..., description="Count of similar alerts seen in the last hour")
    maintenance_window: bool = Field(..., description="True if the alert occurred during a scheduled maintenance window")
    known_admin_activity: bool = Field(..., description="True if the alert is associated with known administrative actions")
    noise_confidence: float = Field(..., description="The confidence score of the XGBoost Noise Reduction model (0.0 to 1.0)")

class AlertResponse(BaseModel):
    verdict: str = Field(..., description="Final analysis verdict: 'actionable' or 'noise'")
    confidence: float = Field(..., description="Confidence score for the final verdict (0.0 to 1.0)")
    severity: str = Field(..., description="Adjusted severity rating based on context: 'low', 'medium', 'high', or 'critical'")
    reasoning: str = Field(..., description="Detailed explanation detailing why the verdict was reached")

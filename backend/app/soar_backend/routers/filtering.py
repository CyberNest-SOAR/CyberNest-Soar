from fastapi import APIRouter, HTTPException, Body
from schemas.models import FilterRequest, FilterResult, UnifiedAlert
from typing import List
from services.filtering import classify_alert

router = APIRouter(prefix="/alerts", tags=["Team 3: Log Filtering & Noise Reduction"])

@router.post("/filter", response_model=List[FilterResult])
async def classify_alerts(request: FilterRequest):
    """
    LLM-Assisted Classification:
    Takes alert IDs, aggregates raw data features, and returns a classification (noise vs. important).
    """
    results = []
    for alert in request.alerts:
        merged_payload = prepare_llm_payload(alert)
        classification = await classify_alert(merged_payload)
        
        results.append(
            FilterResult(
                alert_id=alert.event_id,
                classification=classification["classification"],
                confidence=classification["confidence"],
                summary=f"Rule {merged_payload['rule_id']} marked as {classification['classification']}"
            )
        )
    return results

# Internal helper to demonstrate how your raw data is merged for the LLM
def prepare_llm_payload(alert: UnifiedAlert) -> dict:
    """
    Merges the three raw data sources into the structured POST format 
    required for the classification engine.
    """
    # 1. Base Alert (rule_id, severity, etc.)
    rule_id = alert.raw_data.get("rule", {}).get("id", "unknown") if "rule" in alert.raw_data else alert.raw_data.get("rule_id", "unknown")
    severity = alert.severity
    description = alert.description
    
    # 2. Statistics (event_count_5m, unique_ips, etc.)
    # We simulate statistics extraction from raw_data if not explicitly populated
    stats = alert.raw_data.get("stats", {})
    event_count_5m = stats.get("event_count_5m", 1)
    unique_ips = stats.get("unique_ips", 1)
    
    # 3. Context (asset_criticality, ip_reputation)
    asset_criticality = alert.raw_data.get("context", {}).get("asset_criticality", "low")
    ip_reputation = alert.enrichment_data.vt_score or 100
    
    return {
        "rule_id": rule_id,
        "severity": severity,
        "description": description,
        "event_count_5m": event_count_5m,
        "unique_ips": unique_ips,
        "ip_reputation": ip_reputation,
        "asset_criticality": asset_criticality,
        "label": None  # To be filled by the LLM
    }
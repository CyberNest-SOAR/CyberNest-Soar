from schemas.models import UnifiedAlert

async def calculate_risk_score(alert: UnifiedAlert) -> dict:
    base_score = alert.severity * 10
    
    enrichment_score = 0
    cvss = alert.enrichment_data.cvss_score or 0.0
    epss = alert.enrichment_data.epss_score or 0.0
    
    # Adding CVSS and EPSS scoring logic
    if cvss:
        enrichment_score += cvss * 5
    if epss:
        enrichment_score += epss * 50

    if alert.enrichment_data.abuse_score:
        enrichment_score += alert.enrichment_data.abuse_score * 0.5
    if alert.enrichment_data.vt_score:
        enrichment_score += alert.enrichment_data.vt_score * 0.5
        
    final_score = int(base_score + enrichment_score)
    priority = "High" if final_score > 70 else "Medium" if final_score > 30 else "Low"
    
    return {
        "risk_score": min(final_score, 100),
        "priority": priority,
        "confidence": 0.85,
        "features": {
            "base_severity": base_score, 
            "enrichment": enrichment_score,
            "cvss": cvss,
            "epss": epss
        }
    }

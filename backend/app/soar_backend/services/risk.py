from schemas.models import UnifiedAlert

async def calculate_risk_score(alert: UnifiedAlert) -> dict:
    base_score = alert.severity * 10
    
    enrichment_score = 0
    
    nvd = alert.enrichment_data.nvd
    cvss = nvd.get("cvss") if nvd else None
    if cvss is not None:
        enrichment_score += cvss * 5
        
    epss = alert.enrichment_data.epss
    epss_score = epss.get("score") if epss else None
    if epss_score is not None:
        enrichment_score += epss_score * 50

    abuse = alert.enrichment_data.abuse_ipdb
    abuse_score = abuse.get("score") if abuse else None
    if abuse_score is not None:
        enrichment_score += abuse_score * 0.5
        
    vt = alert.enrichment_data.virus_total
    vt_score = vt.get("score") if vt else None
    if vt_score is not None:
        enrichment_score += vt_score * 0.5
        
    final_score = int(base_score + enrichment_score)
    priority = "High" if final_score > 70 else "Medium" if final_score > 30 else "Low"
    
    return {
        "risk_score": min(final_score, 100),
        "priority": priority,
        "confidence": 0.85,
        "features": {
            "base_severity": base_score, 
            "enrichment": enrichment_score,
            "cvss": cvss or 0.0,
            "epss": epss_score or 0.0,
        },
    }

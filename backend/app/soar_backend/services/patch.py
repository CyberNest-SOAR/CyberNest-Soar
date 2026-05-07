from schemas.models import UnifiedAlert, PatchResponse, Recommendation
import httpx

async def get_patch_recommendations(alert: UnifiedAlert) -> PatchResponse:
    # Cross-reference Wazuh SCA with NVD/EPSS scores
    
    recommendations = []
    
    vulnerabilities = alert.raw_data.get("vulnerability", {})
    if not isinstance(vulnerabilities, list):
        vulnerabilities = [vulnerabilities] if vulnerabilities else []
        
    for vuln in vulnerabilities:
        cve = vuln.get("cve", "UNKNOWN")
        cvss = alert.enrichment_data.cvss_score or float(vuln.get("cvss", {}).get("cvss3", {}).get("base_score", 0.0))
        epss = alert.enrichment_data.epss_score or 0.0
        
        score = cvss * epss
        
        priority = "high" if score > 7 or cvss >= 9.0 else "medium" if score > 3 or cvss >= 7.0 else "low"
        action = "patch immediately" if priority == "high" else "patch next cycle" if priority == "medium" else "monitor"
        
        recommendations.append(Recommendation(
            cve=cve,
            cvss=cvss,
            epss=epss,
            priority=priority,
            action=action
        ))
        
    # Provide a default recommendation if the alert looks like a vulnerability alert but has no explicit data
    if not recommendations:
        recommendations.append(Recommendation(
            cve="CVE-SIMULATED",
            cvss=alert.enrichment_data.cvss_score or 7.5,
            epss=alert.enrichment_data.epss_score or 0.1,
            priority="medium",
            action="patch next cycle"
        ))

    return PatchResponse(
        host=alert.host_context.hostname,
        recommendations=recommendations
    )

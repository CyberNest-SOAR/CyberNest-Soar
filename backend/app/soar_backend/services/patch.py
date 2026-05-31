from schemas.models import UnifiedAlert, PatchResponse, Recommendation
import httpx

async def get_patch_recommendations(alert: UnifiedAlert) -> PatchResponse:
    # Cross-reference alert data with NVD/EPSS enrichment scores
    
    recommendations = []
    
    # Wazuh vulnerability-detector writes to wazuh-states-vulnerabilities-*
    # (separate index), not wazuh-alerts-*.  When a vulnerability alert does
    # appear in the alerts index, the data lives under data.vulnerability.
    raw_data = alert.raw_data
    vulnerabilities = (
        raw_data.get("data", {}).get("vulnerability", [])
        if isinstance(raw_data.get("data"), dict)
        else raw_data.get("vulnerability", [])
    )
    if not isinstance(vulnerabilities, list):
        vulnerabilities = [vulnerabilities] if vulnerabilities else []
        
    for vuln in vulnerabilities:
        cve = vuln.get("cve", "UNKNOWN")
        cvss = (alert.enrichment_data.nvd or {}).get("cvss") or 0.0
        epss = (alert.enrichment_data.epss or {}).get("score") or 0.0
        
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
        
    # Fallback: if no explicit vulnerability data was found, use enrichment scores
    nvd = alert.enrichment_data.nvd
    epss = alert.enrichment_data.epss
    if not recommendations and (nvd or epss):
        recommendations.append(Recommendation(
            cve="CVE-SIMULATED",
            cvss=(nvd or {}).get("cvss") or 7.5,
            epss=(epss or {}).get("score") or 0.1,
            priority="medium",
            action="patch next cycle"
        ))

    return PatchResponse(
        host=alert.host_context.hostname,
        recommendations=recommendations
    )

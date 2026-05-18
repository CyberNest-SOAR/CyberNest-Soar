from schemas.models import UnifiedAlert

async def get_playbook_decision(alert: UnifiedAlert) -> dict:
    risk_score = alert.enrichment_data.risk_score if alert.enrichment_data and alert.enrichment_data.risk_score else 0
    tags = alert.enrichment_data.tags if alert.enrichment_data else []
    
    # Append inferred tags
    if alert.enrichment_data and alert.enrichment_data.misp_matches:
        tags.append("misp_hit")
        
    rule_desc = alert.description.lower()
    if "brute force" in rule_desc or "authentication failed" in rule_desc:
        tags.append("brute_force")

    # Default state
    action = "log_event"
    confidence = 0.5
    automation_level = "manual"
    reason = "Low risk event"

    # 1. CRITICAL: Known C2, misp_hit, or Extreme Risk Score
    if "C2" in tags or "misp_hit" in tags or risk_score >= 80 or alert.severity >= 12:
        action = "isolate_host"
        confidence = 0.98
        automation_level = "full"
        reason = "Critical threat detected (MISP match or C2): Automated host isolation triggered."

    # 2. HIGH: Malware tags, brute force or High Risk Score
    elif "malware" in tags or "brute_force" in tags or risk_score >= 60 or alert.severity >= 8:
        action = "block_ip"
        confidence = 0.85
        automation_level = "full"
        reason = "High risk activity (Brute force or Malware): Automated IP block initiated."

    # 3. MEDIUM: Needs Analyst Review
    elif risk_score >= 40 or alert.severity >= 5:
        action = "create_case"
        confidence = 0.70
        automation_level = "semi"
        reason = "Potential threat: Incident case created for analyst review."

    return {
        "action": action,
        "confidence": confidence,
        "automation_level": automation_level,
        "reason": reason
    }
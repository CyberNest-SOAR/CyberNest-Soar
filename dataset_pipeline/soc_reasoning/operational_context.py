import logging
import random
from typing import List, Optional

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)

_ANALYST_NOTES = {
    "benign": [
        "Known Nessus scanner during scheduled maintenance window.",
        "PowerShell activity appears linked to SCCM deployment.",
        "Scheduled backup traffic — no action required.",
        "Legitimate admin RDP session from jumpbox.",
        "Developer deploying via CI/CD pipeline.",
        "Monitoring agent heartbeat — expected behavior.",
        "Vulnerability scan burst — known false positive pattern.",
        "Certificate renewal traffic, matches change window.",
        "DNS query for CDN domain — legitimate business use.",
        "MSI installer signed by Microsoft — whitelisted.",
    ],
    "suspicious": [
        "Outbound connection to newly registered domain — investigate.",
        "Unusual time of day for this user's activity.",
        "Service account making interactive login — possible lateral movement.",
        "PowerShell execution with obfuscated arguments.",
        "Multiple failed logins followed by success — password spray?",
        "Process launched from temp directory by non-admin user.",
        "Scheduled task created via WMI — possible persistence.",
        "RDP connection from external IP to domain controller.",
        "Unusual SMB traversal by non-admin account.",
        "First-time connection to this external IP for this host.",
    ],
    "true_positive": [
        "Confirmed C2 beacon — traffic matches known IOCs for Emotet.",
        "Ransomware encryption event detected on finance server.",
        "Credential dumping via LSASS access from non-SYSTEM process.",
        "Exfiltration detected — large outbound data transfer to unknown IP.",
        "Lateral movement via WMI from compromised workstation.",
        "Persistence mechanism installed in Run registry key.",
        "Phishing payload executed — confirmed malware beacon.",
        "Privilege escalation via UAC bypass — attacker gained admin.",
        "DNS tunneling detected — base64-encoded subdomains.",
        "Backdoor installed — matches C2 infrastructure for APT29.",
    ],
    "false_positive": [
        "Likely false positive caused by vulnerability scan burst.",
        "Red-team exercise during approved testing window.",
        "SIEM rule too broad — legitimate admin tool flagged.",
        "Duplicate alert from multiple collectors — suppress.",
        "Network scanner triggered IDS rule during asset discovery.",
        "Web app firewall blocked legitimate API call — false positive.",
        "Aggressive threshold on brute-force rule — normal auth patterns.",
        "Legitimate remote access tool flagged as C2 beacon.",
        "Email security gateway quarantined internal phishing test.",
        "Software update traffic from trusted vendor IPs.",
    ],
    "investigating": [
        "Opened case — correlation across multiple data sources pending.",
        "Escalated to Tier 2 for beacon analysis.",
        "Waiting on endpoint investigation results.",
        "Cross-referencing with threat intel feeds — enrichment in progress.",
        "User interview scheduled — need to verify activity context.",
        "Packet capture requested for this session.",
        "Memory forensics analysis in progress on affected endpoint.",
        "Checking SIEM for related logon events in past 24h.",
        "Engaged threat intel team — checking for related campaigns.",
        "Awaiting log retention extension for deeper analysis.",
    ],
}

_CLOSURE_REASONS = {
    "true_positive": [
        "Incident remediated — IOCs blocked, endpoint isolated.",
        "Credential rotation completed, session terminated.",
        "C2 domain sinkholed, affected hosts quarantined.",
        "Threat contained — firewall rules updated.",
        "Malware removed via EDR quarantine, scan completed.",
    ],
    "false_positive": [
        "Rule updated — signature added to exclusion list.",
        "Threshold adjusted to reduce future false positives.",
        "Whitelist updated with legitimate admin tool hash.",
        "Confirmed normal behavior — closed.",
        "Vulnerability scanner excluded from correlation rules.",
    ],
    "benign": [
        "Expected behavior during maintenance window.",
        "Approved administrative activity confirmed.",
        "Scheduled task executed as designed.",
        "Monitoring agent activity — informational only.",
        "Business-as-usual traffic pattern.",
    ],
}

_ESCALATION_REASONS = [
    "Confirmed malware beacon — requires immediate containment.",
    "Multiple hosts affected — potential worm/spread scenario.",
    "Data exfiltration confirmed — engage incident response.",
    "Privilege escalation to domain admin detected.",
    "Ransomware encryption detected on critical asset.",
    "Attack chain in progress — multiple stages observed.",
    "Compromised credentials used across multiple services.",
    "Zero-day exploit signature match — escalate to threat intel.",
]

_PLAYBOOK_ACTIONS = {
    "brute_force": ["Block source IP on firewall", "Reset affected accounts", "Enable MFA", "Review auth logs"],
    "malware": ["Quarantine host", "Block C2 domain", "Run EDR scan", "Collect memory dump"],
    "phishing": ["Remove email from inboxes", "Reset user credentials", "Block sender domain", "User awareness training"],
    "ddos": ["Enable DDoS protection", "Rate-limit source ASN", "Engage ISP", "Scale infrastructure"],
    "lateral_movement": ["Isolate compromised host", "Reset service accounts", "Review network segmentation", "Hunt for persistence"],
    "privilege_escalation": ["Remove elevated privileges", "Rebuild host", "Review privilege assignment", "Audit local admins"],
    "exfiltration": ["Block destination IP", "DLP policy review", "Data leak assessment", "Engage legal"],
    "scanning": ["Rate-limit source IP", "Review firewall rules", "Add to watchlist", "Honeypot engagement"],
    "web_attack": ["WAF rule update", "Block exploit payload", "Patch vulnerable app", "Code review"],
    "benign": ["No action needed", "Monitor", "Update baseline"],
    "noise": ["Suppress similar alerts", "Tune rule", "Close"],
}

_RECOMMENDED_ACTIONS = [
    "Immediately isolate affected host from network.",
    "Reset credentials for all accounts accessed from this source.",
    "Block source IP at perimeter firewall for 24 hours.",
    "Scan affected endpoint with EDR for additional IOCs.",
    "Review authentication logs for related brute force attempts.",
    "Quarantine email and notify recipient of phishing attempt.",
    "Escalate to incident response team for containment.",
    "Update WAF rules to block this exploit pattern.",
    "Run memory forensics on endpoint to identify persistence.",
    "Implement network segmentation to restrict lateral movement.",
    "Enable additional logging on affected servers.",
    "Conduct user awareness training for phishing identification.",
    "Perform threat hunting for related C2 infrastructure.",
    "Review firewall logs for outbound connections to known bad IPs.",
    "No action required — alert suppressed due to maintenance activity.",
]


def add_operational_context(alerts: List[UnifiedAlert],
                            seed: Optional[int] = None) -> List[UnifiedAlert]:
    rng = random.Random(seed)
    for alert in alerts:
        verdict = alert.analyst_verdict or "investigating"

        # Analyst notes
        note_pool = _ANALYST_NOTES.get(verdict, _ANALYST_NOTES["investigating"])
        alert.analyst_notes = rng.choice(note_pool)

        # Playbook action based on attack type
        atk = alert.attack_type or "benign"
        actions = _PLAYBOOK_ACTIONS.get(atk, _PLAYBOOK_ACTIONS["benign"])
        alert.playbook_action = rng.choice(actions)
        alert.playbook_success = None
        if alert.playbook_outcome and alert.playbook_outcome != "no_action_taken":
            alert.playbook_success = rng.random() < 0.75

        # Risk-adjusted priority (1-10)
        base = min(10, (alert.alert_severity or 0))
        if alert.true_positive:
            base = min(10, base + 2)
        if alert.noise:
            base = max(1, base - 3)
        alert.risk_adjusted_priority = max(1, min(10, rng.randint(base - 1, base + 1)))

        # Recommended action
        alert.recommended_action = rng.choice(_RECOMMENDED_ACTIONS)

        # Closure reason
        if alert.analyst_verdict:
            reasons = _CLOSURE_REASONS.get(alert.analyst_verdict, ["Case reviewed and closed."])
            alert.closure_reason = rng.choice(reasons)

        # Escalation reason
        if alert.escalation_level == "incident":
            alert.escalation_reason = rng.choice(_ESCALATION_REASONS)
        elif alert.escalation_level == "tier2":
            alert.escalation_reason = rng.choice([
                "Requires deeper forensic analysis.",
                "Pattern matches known APT activity.",
                "Multiple data sources need correlation.",
                "Suspicious behavior spans multiple endpoints.",
            ])

        # Suppression reason
        if alert.suppression_hit:
            alert.suppression_reason = rng.choice([
                "Same signature triggered 20+ times in last hour.",
                "Known false positive — vulnerability scanner.",
                "Maintenance window — approved admin activity.",
                "Duplicate alert from multiple log sources.",
                "Alert fatigue suppression — similar pattern previously closed as FP.",
            ])

    return alerts

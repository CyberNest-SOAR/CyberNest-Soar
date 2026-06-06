import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

_ATTACK_MAP = {
    "brute_force": ("T1110", "Brute Force", "Credential Access"),
    "ssh_bf": ("T1110.001", "SSH Brute Force", "Credential Access"),
    "rdp_bf": ("T1110.002", "RDP Brute Force", "Credential Access"),
    "password_spray": ("T1110.003", "Password Spraying", "Credential Access"),
    "credential_dumping": ("T1003", "OS Credential Dumping", "Credential Access"),
    "malware": ("T1204", "User Execution", "Execution"),
    "beacon": ("T1071", "C2", "Command and Control"),
    "c2_comm": ("T1071.001", "Web C2", "Command and Control"),
    "phishing": ("T1566", "Phishing", "Initial Access"),
    "spear_phishing": ("T1566.002", "Spear-phishing Link", "Initial Access"),
    "credential_harvest": ("T1566.003", "Spear-phishing via Service", "Initial Access"),
    "ddos": ("T1498", "Network Denial of Service", "Impact"),
    "syn_flood": ("T1498.001", "SYN Flood", "Impact"),
    "udp_flood": ("T1498.002", "UDP Flood", "Impact"),
    "lateral_movement": ("T1021", "Remote Services", "Lateral Movement"),
    "rdp": ("T1021.001", "Remote Desktop", "Lateral Movement"),
    "smb": ("T1021.002", "SMB/Windows Admin Shares", "Lateral Movement"),
    "ssh": ("T1021.004", "SSH", "Lateral Movement"),
    "privilege_escalation": ("T1059", "Command and Scripting Interpreter", "Execution"),
    "scheduled_task": ("T1053.005", "Scheduled Task", "Persistence"),
    "uac_bypass": ("T1548.002", "Bypass UAC", "Privilege Escalation"),
    "exfiltration": ("T1048", "Exfiltration Over Alternative Protocol", "Exfiltration"),
    "dns_exfil": ("T1048.003", "DNS Exfiltration", "Exfiltration"),
    "scanning": ("T1046", "Network Service Scanning", "Discovery"),
    "port_scan": ("T1046", "Network Service Scanning", "Discovery"),
    "web_attack": ("T1190", "Exploit Public-Facing Application", "Initial Access"),
    "sql_injection": ("T1190", "SQL Injection", "Initial Access"),
    "xss": ("T1189", "Drive-by Compromise", "Initial Access"),
    "persistence": ("T1547", "Boot or Logon Autostart", "Persistence"),
    "registry_run": ("T1547.001", "Registry Run Keys", "Persistence"),
    "defense_evasion": ("T1562", "Impair Defenses", "Defense Evasion"),
    "process_injection": ("T1055", "Process Injection", "Defense Evasion"),
    "discovery": ("T1087", "Account Discovery", "Discovery"),
    "collection": ("T1119", "Automated Collection", "Collection"),
    "benign": ("T9999", "Benign", "None"),
    "noise": ("T9999", "Noise", "None"),
}

_FALLBACK = ("T9999", "Unknown", "Other")


def map_attack_type(attack_type: Optional[str], subtype: Optional[str] = None) -> Tuple[str, str, str]:
    key = subtype or attack_type
    if not key:
        return _FALLBACK
    key = key.lower().replace(" ", "_")
    result = _ATTACK_MAP.get(key)
    if result:
        return result
    result = _ATTACK_MAP.get(attack_type.lower().replace(" ", "_")) if attack_type else None
    return result or _FALLBACK

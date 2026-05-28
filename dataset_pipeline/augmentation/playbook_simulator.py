import logging
import random
from typing import Dict, List, Optional

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)

_PLAYBOOK_OUTCOMES = [
    "automated_block", "automated_quarantine", "ticket_created",
    "password_reset", "session_terminated", "ip_blocked",
    "domain_blocked", "no_action_taken", "manual_review",
    "case_escalated", "false_positive_closed",
]

_ATTACK_PLAYBOOK_MAP: Dict[str, List[str]] = {
    "brute_force": ["automated_block", "ip_blocked", "password_reset", "session_terminated"],
    "malware": ["automated_quarantine", "case_escalated", "ticket_created"],
    "phishing": ["password_reset", "ticket_created", "manual_review", "automated_block"],
    "ddos": ["automated_block", "manual_review", "ip_blocked"],
    "lateral_movement": ["session_terminated", "case_escalated", "automated_quarantine"],
    "privilege_escalation": ["session_terminated", "password_reset", "case_escalated"],
    "exfiltration": ["case_escalated", "automated_block", "manual_review"],
    "scanning": ["no_action_taken", "ip_blocked", "automated_block"],
    "web_attack": ["automated_block", "ip_blocked", "case_escalated"],
    "benign": ["no_action_taken", "false_positive_closed"],
    "noise": ["no_action_taken", "false_positive_closed"],
}


def simulate_playbooks(alerts: List[UnifiedAlert],
                       seed: Optional[int] = None) -> List[UnifiedAlert]:
    rng = random.Random(seed)
    for alert in alerts:
        if not alert.true_positive and not alert.is_malicious:
            alert.playbook_outcome = rng.choices(
                ["no_action_taken", "false_positive_closed"],
                weights=[0.6, 0.4], k=1
            )[0]
            continue

        atk = alert.attack_type or "benign"
        outcomes = _ATTACK_PLAYBOOK_MAP.get(atk, ["manual_review", "no_action_taken"])
        alert.playbook_outcome = rng.choice(outcomes)

        if alert.escalation_level == "incident" and alert.is_malicious:
            alert.playbook_outcome = rng.choices(
                ["case_escalated", "automated_quarantine"],
                weights=[0.6, 0.4], k=1
            )[0]

    return alerts

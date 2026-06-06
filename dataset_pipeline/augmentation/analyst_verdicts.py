import logging
import random
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)

_ANALYST_NAMES = ["jdoe", "asmith", "mwilson", "klee", "tpark", "lchen",
                  "rjones", "ablack", "sgarcia", "pwhite"]

_ANALYST_NOTES = [
    "Confirmed malicious — C2 beacon pattern observed",
    "Escalated to Tier 2 for further investigation",
    "Suppressed — known false positive from monitoring agent",
    "Benign traffic, closed as informational",
    "Matches previous campaign FIN7 activity",
    "Correlated with endpoint telemetry — confirmed compromise",
    "Sentinel alert — no action needed",
    "Reviewed and escalated to incident response",
    "False positive — legitimate admin activity during maintenance window",
    "Coincides with phishing campaign targeting finance team",
]

_VERDICTS = ["true_positive", "false_positive", "benign", "suspicious", "investigating"]
_VERDICT_WEIGHTS = [0.35, 0.30, 0.20, 0.10, 0.05]
_ESCALATIONS = ["none", "tier2", "incident", "false_positive"]
_ESCALATION_WEIGHTS = [0.70, 0.15, 0.10, 0.05]


def simulate_analyst_verdicts(alerts: List[UnifiedAlert],
                              seed: Optional[int] = None) -> List[UnifiedAlert]:
    rng = random.Random(seed)
    for alert in alerts:
        if rng.random() < 0.15:
            continue  # 15% remain unassigned (SOC backlog)

        alert.analyst_assigned = rng.choice(_ANALYST_NAMES)
        alert.analyst_verdict = rng.choices(_VERDICTS, weights=_VERDICT_WEIGHTS, k=1)[0]
        alert.analyst_notes = rng.choice(_ANALYST_NOTES)
        alert.suppression_hit = rng.random() < 0.12
        alert.escalation_level = rng.choices(_ESCALATIONS, weights=_ESCALATION_WEIGHTS, k=1)[0]

        if alert.is_malicious and rng.random() < 0.85:
            alert.analyst_verdict = "true_positive"
            alert.escalation_level = rng.choices(["tier2", "incident"], weights=[0.7, 0.3], k=1)[0]

        if alert.noise and rng.random() < 0.7:
            alert.analyst_verdict = "false_positive"
            alert.suppression_hit = True
            alert.escalation_level = "none"

    return alerts

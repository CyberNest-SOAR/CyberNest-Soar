import logging
import random
from typing import Dict, List, Optional, Tuple

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)


def add_historical_memory(alerts: List[UnifiedAlert],
                          seed: Optional[int] = None) -> List[UnifiedAlert]:
    if not alerts:
        return alerts
    rng = random.Random(seed)

    # Track "historical" memory per signature key
    history: Dict[str, Dict] = {}

    for alert in alerts:
        sig_key = (alert.alert_signature or alert.attack_type or "unknown")

        if sig_key not in history:
            history[sig_key] = {
                "count": 0,
                "fp_count": 0,
                "tp_count": 0,
                "case_count": 0,
            }
        h = history[sig_key]
        h["count"] += 1

        # Historically seen — after 3+ occurrences
        alert.historically_seen = h["count"] >= 3

        # Historical false positive rate
        if h["count"] > 1:
            h["fp_rate"] = h["fp_count"] / max(1, h["count"] - 1)
        else:
            h["fp_rate"] = 0.0
        alert.historical_false_positive_rate = round(h["fp_rate"], 4)

        # Recurring alert — seen across multiple time windows
        alert.recurring_alert = h["count"] >= 5

        # Prior case count — unique cases that referenced this signature
        if alert.true_positive:
            h["case_count"] += 1
        # Add some randomness — not every TP gets a case
        alert.prior_case_count = h["case_count"]

        # Track FP vs TP decisions for historical rate
        if alert.analyst_verdict == "false_positive":
            h["fp_count"] += 1
        elif alert.analyst_verdict == "true_positive":
            h["tp_count"] += 1

    # Inject historical inconsistency: 10% of alerts have contradictory FP rates
    for alert in alerts:
        if rng.random() < 0.10:
            sig_key = (alert.alert_signature or alert.attack_type or "unknown")
            h = history[sig_key]
            if h["count"] >= 3:
                # Flip the historical FP to create analyst inconsistency
                old_fp = alert.historical_false_positive_rate
                alert.historical_false_positive_rate = round(max(0.0, min(1.0, old_fp + rng.uniform(-0.3, 0.3))), 4)
                alert.extra_fields["historical_inconsistency"] = True

    return alerts

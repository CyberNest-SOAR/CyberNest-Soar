import logging
import random
import uuid
from datetime import timedelta
from typing import List, Optional

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)


def inject_soc_noise(alerts: List[UnifiedAlert],
                     duplicate_rate: float = 0.08,
                     false_positive_rate: float = 0.15,
                     alert_fatigue_rate: float = 0.05,
                     seed: Optional[int] = None) -> List[UnifiedAlert]:
    if not alerts:
        return alerts
    rng = random.Random(seed)
    result = list(alerts)
    seen_signatures = {}

    for alert in alerts:
        key = (alert.alert_signature, alert.alert_category, alert.attack_type)

        # Duplicate alerts
        if rng.random() < duplicate_rate:
            dup = UnifiedAlert(
                event_id=f"dup-{alert.event_id}",
                timestamp=alert.timestamp + timedelta(seconds=rng.randint(30, 300)),
                dataset_source=alert.dataset_source,
                event_type=alert.event_type,
                src_ip=alert.src_ip,
                dst_ip=alert.dst_ip,
                src_port=alert.src_port,
                dst_port=alert.dst_port,
                protocol=alert.protocol,
                alert_signature=alert.alert_signature,
                alert_severity=alert.alert_severity,
                alert_category=alert.alert_category,
                attack_type=alert.attack_type or "noise",
                mitre_technique_id=alert.mitre_technique_id,
                mitre_technique_name=alert.mitre_technique_name,
                mitre_tactic=alert.mitre_tactic,
                true_positive=False,
                noise=True,
                confidence=min(1.0, (alert.confidence or 0.9) * 0.7),
                extra_fields={"duplicate_of": alert.event_id, "fatigue": True},
            )
            result.append(dup)

        # False positive tagging
        if key in seen_signatures and rng.random() < false_positive_rate:
            if rng.random() < 0.5:
                alert.true_positive = False
                alert.analyst_verdict = "false_positive"
                alert.noise = True
                alert.extra_fields["suppression_reason"] = "known FP from similar past alerts"

        seen_signatures[key] = seen_signatures.get(key, 0) + 1

        # Alert fatigue: high-frequency signature suppression
        if seen_signatures[key] >= 20:
            if rng.random() < alert_fatigue_rate:
                alert.noise = True
                alert.true_positive = False
                alert.suppression_hit = True
                alert.extra_fields["fatigue"] = True

    rng.shuffle(result)
    return result

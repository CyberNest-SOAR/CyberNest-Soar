"""
soc_reasoning/reasoning_pipeline.py — Transforms telemetry-centric alerts into
enterprise SOC reasoning datasets suitable for LLM training.

Runs all 7 enrichment+augmentation stages in sequence:
  1. Operational context (analyst notes, closures, playbooks)
  2. Environmental context (maintenance, patches, scans)
  3. Asset & business context (criticality, roles, departments)
  4. Identity & process context (users, processes, auth)
  5. Temporal correlation (timeline, bursts, storms)
  6. Historical memory (recurrence, FP rates)
  7. Enterprise SOC noise (SCCM, scanners, backups, storms, inconsistencies)
"""
import logging
from typing import List, Optional

from parsers.normalizer import UnifiedAlert
from soc_reasoning.operational_context import add_operational_context
from soc_reasoning.environmental_context import add_environmental_context
from soc_reasoning.asset_context import add_asset_context
from soc_reasoning.identity_context import add_identity_context
from soc_reasoning.temporal_correlation import add_temporal_correlation
from soc_reasoning.historical_memory import add_historical_memory
from soc_reasoning.soc_noise import inject_enterprise_noise

logger = logging.getLogger(__name__)


def transform_to_soc_reasoning_dataset(
    alerts: List[UnifiedAlert],
    seed: Optional[int] = None,
) -> List[UnifiedAlert]:
    logger.info("=" * 60)
    logger.info("SOC REASONING TRANSFORMATION")
    logger.info("=" * 60)

    logger.info("Step 1/7: Operational context (notes, closures, playbooks)")
    alerts = add_operational_context(alerts, seed=seed)

    logger.info("Step 2/7: Environmental context (maintenance, patches, scans)")
    alerts = add_environmental_context(alerts, seed=seed)

    logger.info("Step 3/7: Asset & business context (criticality, roles, departments)")
    alerts = add_asset_context(alerts, seed=seed)

    logger.info("Step 4/7: Identity & process context (users, processes, auth)")
    alerts = add_identity_context(alerts, seed=seed)

    logger.info("Step 5/7: Temporal correlation (timeline, bursts, storms)")
    alerts = add_temporal_correlation(alerts, seed=seed)

    logger.info("Step 6/7: Historical memory (recurrence, FP rates)")
    alerts = add_historical_memory(alerts, seed=seed)

    logger.info("Step 7/7: Enterprise SOC noise (SCCM, scanners, backups, storms)")
    alerts = inject_enterprise_noise(alerts, seed=seed)

    logger.info("SOC reasoning transformation complete — %d alerts", len(alerts))
    return alerts


# LLM-specific exports extracted for focused training datasets
def extract_analyst_notes_dataset(alerts: List[UnifiedAlert]) -> list:
    return [
        {
            "event_id": a.event_id,
            "alert_signature": a.alert_signature,
            "attack_type": a.attack_type,
            "alert_severity": a.alert_severity,
            "analyst_verdict": a.analyst_verdict,
            "analyst_notes": a.analyst_notes,
            "analyst_assigned": a.analyst_assigned,
            "true_positive": a.true_positive,
            "noise": a.noise,
            "suppression_hit": a.suppression_hit,
            "mitre_technique_id": a.mitre_technique_id,
        }
        for a in alerts if a.analyst_notes
    ]


def extract_suppression_reason_dataset(alerts: List[UnifiedAlert]) -> list:
    return [
        {
            "event_id": a.event_id,
            "alert_signature": a.alert_signature,
            "attack_type": a.attack_type,
            "suppression_reason": a.suppression_reason,
            "suppression_hit": a.suppression_hit,
            "environment_context": a.environment_context,
            "historical_false_positive_rate": a.historical_false_positive_rate,
            "recurring_alert": a.recurring_alert,
        }
        for a in alerts if a.suppression_hit and a.suppression_reason
    ]


def extract_escalation_decision_dataset(alerts: List[UnifiedAlert]) -> list:
    return [
        {
            "event_id": a.event_id,
            "alert_signature": a.alert_signature,
            "attack_type": a.attack_type,
            "alert_severity": a.alert_severity,
            "asset_criticality": a.asset_criticality,
            "escalation_level": a.escalation_level,
            "escalation_reason": a.escalation_reason,
            "analyst_verdict": a.analyst_verdict,
            "confidence": a.confidence,
            "risk_adjusted_priority": a.risk_adjusted_priority,
            "true_positive": a.true_positive,
            "repeated_behavior_score": a.repeated_behavior_score,
            "similar_alerts_last_hour": a.similar_alerts_last_hour,
        }
        for a in alerts if a.escalation_level and a.escalation_level != "none"
    ]

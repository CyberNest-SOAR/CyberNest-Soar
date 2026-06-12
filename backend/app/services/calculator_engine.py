"""
calculator_engine.py — Mathematical computation engine for report metrics.

Computes:
  - Security posture score (weighted composite)
  - Risk score (weighted composite)
  - MTTR / MTTD
  - SLA compliance / breach rate
  - Risk concentration (top-N asset analysis)
  - F1 score from verdict counts
  - Hygiene score (5-dimension breakdown)
"""

import logging
from collections import Counter

logger = logging.getLogger(__name__)


class CalculatorEngine:
    """Stateless computation engine for all report metrics."""

    def compute_posture_score(
        self,
        f1_score: float = 0,
        hygiene_overall: float = 0,
        sla_compliance: float = 0,
        noise_rate: float = 0,
        suppression_rate: float = 0,
    ) -> float:
        """Weighted composite:
        - Detection quality (F1-based): 30%
        - Hygiene adherence: 30%
        - Response effectiveness (SLA): 20%
        - Noise management: 20%
        """
        detection = f1_score * 100 * 0.30
        hygiene = hygiene_overall * 0.30
        sla = sla_compliance * 0.20
        noise_mgmt = ((100 - noise_rate) * 0.60 + (100 - suppression_rate) * 0.40) * 0.20
        return round(detection + hygiene + sla + noise_mgmt, 1)

    def compute_risk_score(
        self,
        critical_alerts: int = 0,
        total_events: int = 0,
        f1_score: float = 0,
        hygiene_overall: float = 0,
    ) -> float:
        """Weighted composite risk:
        - Alert criticality: 40%
        - Detection gaps (1 - F1): 30%
        - Hygiene gaps (100 - hygiene): 30%
        """
        criticality = (critical_alerts / max(total_events, 1)) * 100 * 0.40
        detection_gap = (1 - f1_score) * 100 * 0.30
        hygiene_gap = (100 - hygiene_overall) * 0.30
        return round(criticality + detection_gap + hygiene_gap, 1)

    def compute_f1_score(
        self, true_positives: int = 0, false_positives: int = 0, false_negatives: int = 0
    ) -> float:
        """F1 = 2 * (precision * recall) / (precision + recall)."""
        precision = true_positives / max(true_positives + false_positives, 1)
        recall = true_positives / max(true_positives + false_negatives, 1)
        if precision + recall == 0:
            return 0.0
        return round(2 * (precision * recall) / (precision + recall), 3)

    def compute_mttr_hours(self, containment_times: list[float]) -> float:
        """Mean Time to Respond = AVG(closure - containment) in hours."""
        if not containment_times:
            return 0.0
        return round(sum(containment_times) / len(containment_times), 1)

    def compute_mttd_hours(self, detection_times: list[float]) -> float:
        """Mean Time to Detect = AVG(detection - earliest_activity) in hours."""
        if not detection_times:
            return 0.0
        return round(sum(detection_times) / len(detection_times), 1)

    def compute_sla_metrics(
        self, triage_times_min: list[float], sla_threshold_min: int = 15
    ) -> dict:
        """Compute SLA breach rate and average triage time."""
        breaches = sum(1 for t in triage_times_min if t > sla_threshold_min)
        total = len(triage_times_min)
        return {
            "total_triage_events": total,
            "sla_breaches": breaches,
            "breach_rate": round(breaches / max(total, 1) * 100, 1),
            "avg_triage_time_min": round(sum(triage_times_min) / max(total, 1), 1),
        }

    def compute_risk_concentration(
        self, assets: list[dict], top_n: int = 5
    ) -> list[dict]:
        """Identify assets contributing most to organizational risk.

        Args:
            assets: List of dicts with keys hostname, risk_score, critical_vulnerabilities, department
            top_n: Number of top assets to return

        Returns:
            List of top risk assets with percentage breakdown
        """
        sorted_assets = sorted(assets, key=lambda a: a.get("risk_score", 0), reverse=True)
        total_risk = sum(a.get("risk_score", 0) for a in sorted_assets)
        top_assets = sorted_assets[:top_n]
        top_risk = sum(a.get("risk_score", 0) for a in top_assets)

        result = [
            {
                "hostname": a.get("hostname", "unknown"),
                "risk_score": a.get("risk_score", 0),
                "pct_of_total": round(a.get("risk_score", 0) / max(total_risk, 1) * 100, 1),
                "critical_vulns": a.get("critical_vulnerabilities", 0),
                "department": a.get("department", "unknown"),
            }
            for a in top_assets
        ]
        result.append({
            "note": f"Top {top_n} assets account for {round(top_risk / max(total_risk, 1) * 100, 1)}% of total risk"
        })
        return result

    def compute_hygiene_score(self, events: list[dict]) -> dict:
        """Compute 5-dimension hygiene score from event data.

        Dimensions:
        - Patch: events in maintenance/patch windows
        - Authentication: events without MFA or using legacy auth
        - Logging/Monitoring: noise events
        - Integrity: suppression hits or unsigned binaries
        - Threat: true positive events
        """
        total = len(events) or 1
        patch_issues = sum(1 for e in events if e.get("maintenance_window") or e.get("patch_window"))
        auth_issues = sum(1 for e in events if not e.get("mfa_used") or e.get("authentication_method") == "password")
        config_issues = sum(1 for e in events if e.get("noise") and not e.get("suppression_hit"))
        integrity_issues = sum(1 for e in events if e.get("suppression_hit") or not e.get("signed_binary", True))
        threat_issues = sum(1 for e in events if e.get("true_positive"))

        return {
            "overall": round(100 - ((patch_issues + auth_issues + config_issues + integrity_issues + threat_issues) / total * 100), 1),
            "breakdown": {
                "patch_hygiene": round(100 - (patch_issues / total * 100), 1),
                "authentication_hygiene": round(100 - (auth_issues / total * 100), 1),
                "logging_hygiene": round(100 - (config_issues / total * 100), 1),
                "integrity_hygiene": round(100 - (integrity_issues / total * 100), 1),
                "threat_hygiene": round(100 - (threat_issues / total * 100), 1),
            },
        }

    def compute_week_over_week(self, current: float, previous: float) -> dict:
        """Compute WoW percentage change with direction."""
        if previous == 0:
            return {"pct_change": 0, "direction": "stable"}
        pct = ((current - previous) / previous) * 100
        return {
            "pct_change": round(pct, 1),
            "direction": "increased" if pct > 0 else "decreased" if pct < 0 else "stable",
        }

    def determine_severity_label(self, severity: int) -> str:
        if severity >= 10:
            return "critical"
        elif severity >= 7:
            return "high"
        elif severity >= 4:
            return "medium"
        return "low"

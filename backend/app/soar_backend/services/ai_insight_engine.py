"""
ai_insight_engine.py — Generates data-driven executive findings,
risk assessments, trends, and recommended actions.

Uses a rule-based + LLM-refinable architecture:
  - Statistical Analyzer: week-over-week comparisons, threshold detection
  - Trend Comparator: multi-metric trend analysis
  - Anomaly Detector: statistical deviation detection
  - Insight Generator: synthesis into natural-language findings
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class StatComparison:
    metric: str
    current_value: float
    previous_value: float
    pct_change: float
    direction: str
    significance: str
    confidence: float


@dataclass
class Finding:
    finding: str
    confidence: float
    severity: str
    recommended_action: str
    category: str = "general"


class StatisticalAnalyzer:
    """Compares current metrics against previous period."""

    THRESHOLDS = {
        "critical_alerts": 10,
        "false_positive_rate": 15,
        "noise_rate": 15,
        "suppression_rate": 20,
        "mttr_hours": 10,
        "ioc_hits": 20,
        "attack_type_shift": 15,
        "analyst_workload_imbalance": 25,
    }

    def compare(self, current: float, previous: float, metric: str) -> Optional[StatComparison]:
        if previous == 0:
            return None
        pct_change = ((current - previous) / previous) * 100
        threshold = self.THRESHOLDS.get(metric, 10)

        if abs(pct_change) < threshold:
            return None

        direction = "increased" if pct_change > 0 else "decreased"
        significance = (
            "high" if abs(pct_change) > 30
            else "medium" if abs(pct_change) > 15
            else "low"
        )
        confidence = min(abs(pct_change) / 100, 0.95)

        return StatComparison(
            metric=metric,
            current_value=current,
            previous_value=previous,
            pct_change=round(pct_change, 1),
            direction=direction,
            significance=significance,
            confidence=round(confidence, 3),
        )


class TrendComparator:
    """Analyzes trends across multiple metrics."""

    def analyze(self, current: dict, previous: dict) -> list[Finding]:
        findings = []
        analyzer = StatisticalAnalyzer()

        metric_map = {
            "critical_alerts": "Critical alerts",
            "false_positive_rate": "False positive rate",
            "noise_rate": "Noise rate",
            "mttr_hours": "Mean Time to Respond",
            "ioc_hits": "IOC hit rate",
            "total_incidents": "Total incidents",
        }

        for key, label in metric_map.items():
            cur_val = current.get(key, 0)
            prev_val = previous.get(key, 0)
            if isinstance(cur_val, (int, float)) and isinstance(prev_val, (int, float)):
                stat = analyzer.compare(cur_val, prev_val, key)
                if stat:
                    direction_word = "increased" if stat.pct_change > 0 else "decreased"
                    findings.append(Finding(
                        finding=f"{label} {direction_word} {abs(stat.pct_change)}% "
                                f"({prev_val:.0f} → {cur_val:.0f})",
                        confidence=stat.confidence,
                        severity=stat.significance,
                        recommended_action=self._recommend_action(key, stat),
                        category="trend",
                    ))

        return findings

    def _recommend_action(self, metric: str, stat: StatComparison) -> str:
        actions = {
            "critical_alerts": "Investigate root cause of critical alert surge; review rule tuning" if stat.pct_change > 0 else "",
            "false_positive_rate": "Review and tune detection rules to reduce FP rate" if stat.pct_change > 0 else "FP reduction efforts are effective — continue tuning",
            "noise_rate": "Review suppression rules; possible sensor misconfiguration" if stat.pct_change > 0 else "",
            "mttr_hours": "Investigate response process bottlenecks" if stat.pct_change > 0 else "Response efficiency improving — document best practices",
            "ioc_hits": "Active threat campaign possible — escalate to threat intel team" if stat.pct_change > 0 else "",
        }
        return actions.get(metric, "")


class AnomalyDetector:
    """Detects statistical anomalies in metrics."""

    def detect(self, stats: dict) -> list[Finding]:
        findings = []

        # Risk concentration
        assets = stats.get("assets", [])
        if assets:
            sorted_assets = sorted(assets, key=lambda a: a.get("risk_score", 0), reverse=True)
            total_risk = sum(a.get("risk_score", 0) for a in sorted_assets)
            if total_risk > 0:
                top2_pct = sum(a.get("risk_score", 0) for a in sorted_assets[:2]) / total_risk * 100
                if top2_pct > 40:
                    findings.append(Finding(
                        finding=f"Top 2 assets account for {top2_pct:.0f}% of organizational risk "
                                f"— prioritize remediation",
                        confidence=round(min(top2_pct / 100, 0.95), 3),
                        severity="high",
                        recommended_action="Patch top 2 highest-risk assets within 7 days",
                        category="concentration",
                    ))

        # Workload imbalance
        analyst_activity = stats.get("analyst_activity", {})
        if analyst_activity:
            loads = list(analyst_activity.values())
            if loads:
                ratio = max(loads) / max(min(loads), 1)
                if ratio > 2.5:
                    findings.append(Finding(
                        finding=f"Analyst workload imbalance detected ({ratio:.1f}:1 max:min) "
                                f"— rebalance assignments",
                        confidence=round(min((ratio - 2) / 5, 0.9), 3),
                        severity="medium",
                        recommended_action="Review analyst queue distribution and redistribute alerts",
                        category="workload",
                    ))

        return findings


class AIInsightEngine:
    """Generates structured insights for all report types."""

    def __init__(self):
        self.statistical_analyzer = StatisticalAnalyzer()
        self.trend_comparator = TrendComparator()
        self.anomaly_detector = AnomalyDetector()

    async def generate_executive_insights(self, current: dict, previous: Optional[dict] = None) -> dict:
        findings = []

        if previous:
            trend_findings = self.trend_comparator.analyze(current, previous)
            findings.extend(trend_findings)

        anomaly_findings = self.anomaly_detector.detect(current)
        findings.extend(anomaly_findings)

        # Sort by confidence descending
        findings.sort(key=lambda f: f.confidence, reverse=True)

        return {
            "executive_findings": [
                {
                    "finding": f.finding,
                    "confidence": f.confidence,
                    "severity": f.severity,
                    "recommended_action": f.recommended_action,
                }
                for f in findings[:10]
            ],
            "confidence_score": round(
                sum(f.confidence for f in findings) / max(len(findings), 1), 2
            ) if findings else 0,
        }

    async def generate_soc_insights(self, stats: dict) -> list[str]:
        """Generate SOC management recommendations."""
        recommendations = []

        if stats.get("analyst_activity"):
            loads = list(stats["analyst_activity"].values())
            if loads:
                ratio = max(loads) / max(min(loads), 1)
                if ratio > 3:
                    recommendations.append(
                        f"Tier 1 workload exceeds capacity — {ratio:.1f}:1 load imbalance. "
                        "Consider shift adjustment."
                    )

        if stats.get("suppression_rate", 0) > 40:
            recommendations.append(
                f"Suppression rate at {stats['suppression_rate']}% — "
                "review rules; consider pre-filtering at ingestion."
            )

        if stats.get("false_positive_rate", 0) > 25:
            recommendations.append(
                f"False positive rate at {stats['false_positive_rate']}% — "
                "review and tune detection rules."
            )

        sla_breach = stats.get("sla_breach_rate", 0)
        if sla_breach > 10:
            recommendations.append(
                f"SLA breach rate at {sla_breach}% — "
                "investigate triage workflow bottlenecks."
            )

        return recommendations

    async def generate_shift_summary(self, shift_data: dict) -> str:
        """Generate concise AI shift summary."""
        parts = []

        new = shift_data.get("new_incidents", {})
        parts.append(
            f"Shift handled {new.get('total', 0):,} new incidents "
            f"({new.get('critical', 0)} critical, {new.get('high', 0)} high)."
        )

        resolved = shift_data.get("resolved_incidents", {})
        parts.append(f"{resolved.get('total', 0)} resolved.")

        open_inc = shift_data.get("open_incidents", {})
        if open_inc.get("critical", 0) > 0:
            parts.append(f"{open_inc['critical']} critical incidents remain open.")

        ti_hits = shift_data.get("threat_intel_hits", {})
        if ti_hits.get("total", 0) > 0:
            malicious_pct = (
                ti_hits.get("malicious", 0) / max(ti_hits.get("total", 1), 1) * 100
            )
            parts.append(f"{ti_hits['total']} threat intel hits ({malicious_pct:.0f}% malicious).")

        pb = shift_data.get("playbook_executions", {})
        if pb.get("total", 0) > 0:
            parts.append(f"{pb['total']} playbook executions ({pb.get('automated_actions', 0)} automated).")

        return " ".join(parts)

"""
report_generator.py — Core report generation service.

Aggregates data from pipeline + OpenSearch + TheHive + threat intel,
applies calculator engine for metrics, and produces structured report objects.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta

from app.services.aggregation_pipeline import AggregationPipeline
from app.services.calculator_engine import CalculatorEngine
from app.services.ai_insight_engine import AIInsightEngine

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates structured report objects for all report types."""

    def __init__(self):
        self.aggregator = AggregationPipeline()
        self.calculator = CalculatorEngine()
        self.ai_engine = AIInsightEngine()

    def _report_id(self) -> str:
        return str(uuid.uuid4())

    def _period_days(self, period_start: datetime, period_end: datetime) -> str:
        delta = (period_end - period_start).days
        if delta <= 1:
            return "24h"
        return f"{delta}d"

    async def generate_executive_report(self, period_start: datetime, period_end: datetime) -> dict:
        """Executive Security Report for CISO / SOC Director."""
        report_id = self._report_id()

        # Aggregate pipeline data for period
        stats = await self.aggregator.pipeline_summary()
        thehive = await self.aggregator.thehive_summary()
        sla = await self.aggregator.sla_compliance()
        monthly_trend = await self.aggregator.monthly_trend()

        verdicts = dict(stats.verdicts)
        tp = verdicts.get("true_positive", 0)
        fp = verdicts.get("false_positive", 0)
        fn = verdicts.get("true_positive", 0)  # conservative: undetected TP = TP
        f1 = self.calculator.compute_f1_score(tp, fp, fn)

        critical = sum(v for k, v in stats.severity.items() if k >= 10)
        high = sum(v for k, v in stats.severity.items() if 7 <= k < 10)

        hygiene = self.calculator.compute_hygiene_score([])

        posture = self.calculator.compute_posture_score(
            f1_score=f1,
            hygiene_overall=hygiene.get("overall", 70),
            sla_compliance=100 - sla.get("breach_rate", 0),
            noise_rate=round(stats.noise_count / max(stats.total, 1) * 100, 1),
            suppression_rate=round(stats.suppressed / max(stats.total, 1) * 100, 1),
        )

        risk = self.calculator.compute_risk_score(
            critical_alerts=critical,
            total_events=stats.total,
            f1_score=f1,
            hygiene_overall=hygiene.get("overall", 70),
        )

        current_snapshot = {
            "critical_alerts": critical,
            "false_positive_rate": round(fp / max(stats.total, 1) * 100, 1),
            "noise_rate": round(stats.noise_count / max(stats.total, 1) * 100, 1),
            "mttr_hours": sla.get("mttr_hours", 0),
            "ioc_hits": len(stats.ioc_ips) + len(stats.ioc_domains),
            "total_incidents": stats.total,
            "analyst_activity": dict(stats.analyst_activity),
            "assets": [
                {"hostname": ip, "risk_score": cnt}
                for ip, cnt in stats.asset_alert_counts.most_common(50)
            ],
            "suppression_rate": round(stats.suppressed / max(stats.total, 1) * 100, 1),
            "sla_breach_rate": sla.get("breach_rate", 0),
        }

        insights = await self.ai_engine.generate_executive_insights(current_snapshot)

        trend_data = []
        for month, count in monthly_trend.items():
            trend_data.append({"date": month, "value": count})

        return {
            "report_id": report_id,
            "report_type": "executive_security",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
                "label": f"Last {self._period_days(period_start, period_end)}",
            },
            "executive_summary": {
                "security_posture_score": posture,
                "posture_trend": "stable",
                "risk_score": risk,
                "risk_score_trend": "stable",
                "critical_incidents": critical,
                "high_incidents": high,
                "total_alerts": stats.total,
                "mttd_hours": self.calculator.compute_mttd_hours([]),
                "mttr_hours": sla.get("mttr_hours", 0),
                "sla_compliance_pct": round(100 - sla.get("breach_rate", 0), 1),
                "sla_trend": "stable",
            },
            "risk_overview": {
                "current_risk_level": "elevated" if risk > 50 else "moderate" if risk > 25 else "low",
                "top_risks": [
                    {
                        "risk": f"Top attack types: {', '.join(k for k, v in stats.attack_types.most_common(3))}",
                        "impact": f"{stats.total:,} total events analyzed",
                        "risk_score": risk,
                    }
                ],
            },
            "security_trends": {
                "alert_volume_trend": trend_data[-30:] if len(trend_data) > 30 else trend_data,
                "severity_distribution": {str(k): v for k, v in stats.severity.most_common(15)},
                "attack_type_distribution": dict(stats.attack_types.most_common(10)),
                "mitre_tactics": dict(stats.mitre_tactics.most_common(10)),
                "mttr_trend": [{"date": "current", "mttr_hours": sla.get("mttr_hours", 0)}],
            },
            "critical_incidents": [
                {
                    "incident_id": f"inc-{report_id[:8]}",
                    "title": f"Campaign: {cid[:16]} — {stats.attack_types.most_common(1)[0][0] if stats.attack_types else 'unknown'} activity",
                    "severity": max(stats.severity.keys()) if stats.severity else 0,
                    "status": "active",
                    "attack_type": stats.attack_types.most_common(1)[0][0] if stats.attack_types else "unknown",
                    "affected_assets": [ip for ip, _ in stats.asset_alert_counts.most_common(5)],
                }
                for cid in list(stats.campaign_ids)[:5]
            ],
            "ai_insights": insights,
        }

    async def generate_soc_operations_report(self, period_start: datetime, period_end: datetime) -> dict:
        """SOC Operations Report for SOC Managers."""
        report_id = self._report_id()
        stats = await self.aggregator.pipeline_summary()
        sla = await self.aggregator.sla_compliance()
        thehive = await self.aggregator.thehive_summary()
        analyst_detail = await self.aggregator.analyst_detail()

        verdicts = dict(stats.verdicts)
        tp = verdicts.get("true_positive", 0)
        fp = verdicts.get("false_positive", 0)
        fn = verdicts.get("benign", 0) or 1
        f1 = self.calculator.compute_f1_score(tp, fp, fn)

        critical = sum(v for k, v in stats.severity.items() if k >= 10)
        high = sum(v for k, v in stats.severity.items() if 7 <= k < 10)

        tier1 = stats.escalations.get("none", stats.total)
        tier2 = stats.escalations.get("tier2", 0)
        tier3 = stats.escalations.get("incident", 0)

        soc_stats = {
            "analyst_activity": dict(stats.analyst_activity),
            "suppression_rate": round(stats.suppressed / max(stats.total, 1) * 100, 1),
            "false_positive_rate": round(fp / max(stats.total, 1) * 100, 1),
            "sla_breach_rate": sla.get("breach_rate", 0),
        }
        recommendations = await self.ai_engine.generate_soc_insights(soc_stats)

        return {
            "report_id": report_id,
            "report_type": "soc_operations",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
                "label": f"Last {self._period_days(period_start, period_end)}",
            },
            "alert_overview": {
                "total_alerts": stats.total,
                "daily_average": round(stats.total / max(self._period_days(period_start, period_end).replace("d", ""), "1"), 0),
                "critical": critical,
                "high": high,
                "severity_distribution": {str(k): v for k, v in stats.severity.most_common(15)},
                "attack_type_distribution": dict(stats.attack_types.most_common(10)),
            },
            "analyst_performance": {
                "total_resolved": sum(stats.analyst_activity.values()),
                "by_analyst": analyst_detail,
                "avg_triage_time_min": sla.get("avg_triage_time_min", 0),
                "sla_breach_rate_pct": sla.get("breach_rate", 0),
            },
            "escalation_analysis": {
                "tier_1_load": tier1,
                "tier_2_load": tier2,
                "tier_3_load": tier3,
                "escalation_rate_pct": round((tier2 + tier3) / max(stats.total, 1) * 100, 1),
                "escalation_levels": dict(stats.escalations.most_common()),
            },
            "detection_effectiveness": {
                "false_positive_rate": round(fp / max(stats.total, 1) * 100, 1),
                "true_positive_rate": round(tp / max(stats.total, 1) * 100, 1),
                "noise_rate": round(stats.noise_count / max(stats.total, 1) * 100, 1),
                "suppression_rate": round(stats.suppressed / max(stats.total, 1) * 100, 1),
                "f1_score": f1,
            },
            "noise_reduction": {
                "total_suppressed": stats.suppressed,
                "total_noise": stats.noise_count,
                "analyst_verdicts": dict(stats.verdicts.most_common()),
            },
            "automation_performance": {
                "playbook_executions": sum(stats.playbook_outcomes.values()),
                "actions_by_type": dict(stats.playbook_outcomes.most_common()),
            },
            "case_metrics": thehive,
            "workload_analysis": {
                "busiest_hour": stats.hourly_counts.most_common(1)[0][0] if stats.hourly_counts else "N/A",
                "top_analysts": dict(stats.analyst_activity.most_common(5)),
            },
            "recommendations": recommendations,
        }

    async def generate_incident_report(self, incident_id: str) -> dict:
        """Incident Intelligence Report for responders."""
        report_id = self._report_id()
        stats = await self.aggregator.pipeline_summary()

        event_data = {"event_id": incident_id}
        latest = self.aggregator._latest_ndjson()
        if latest:
            for event in self.aggregator._iter_ndjson(latest, 200000):
                if event.get("event_id") == incident_id:
                    event_data = event
                    break

        return {
            "report_id": report_id,
            "report_type": "incident_intelligence",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "incident_id": incident_id,
            "incident_summary": {
                "title": f"Incident: {event_data.get('attack_type', 'unknown')} — {event_data.get('src_ip', 'unknown')}",
                "severity": event_data.get("alert_severity", 0),
                "status": "analyzed",
                "discovery_method": f"Pipeline detection — {event_data.get('dataset_source', 'unknown')}",
                "attack_type": event_data.get("attack_type", "unknown"),
                "campaign_id": event_data.get("campaign_id", ""),
            },
            "ioc_analysis": {
                "ip_iocs": [event_data.get("src_ip", "")] if event_data.get("src_ip") else [],
                "domain_iocs": [event_data.get("ioc_domain", "")] if event_data.get("ioc_domain") else [],
                "hash_iocs": [event_data.get("ioc_hash", "")] if event_data.get("ioc_hash") else [],
                "vt_score": event_data.get("enrichment_vt_score", 0),
                "abuse_score": event_data.get("enrichment_abuse_score", 0),
                "epss_score": event_data.get("enrichment_epss_score", 0),
            },
            "mitre_mapping": [
                {
                    "tactic": event_data.get("mitre_tactic", "unknown"),
                    "technique_id": event_data.get("mitre_technique_id", ""),
                    "technique_name": event_data.get("mitre_technique_name", ""),
                }
            ] if event_data.get("mitre_tactic") else [],
            "impact_assessment": {
                "affected_assets": [{"ip": event_data.get("src_ip", ""), "criticality": event_data.get("asset_criticality", "unknown")}],
                "host_role": event_data.get("host_role", "unknown"),
                "department": event_data.get("department", "unknown"),
            },
            "containment_actions": [
                {"action": event_data.get("playbook_action", "N/A"), "automated": True},
                {"action": event_data.get("recommended_action", "N/A"), "automated": False},
            ],
            "lessons_learned": [
                "Review detection coverage for this attack type",
                "Validate enrichment data quality for this IOC source",
            ],
        }

    async def generate_threat_intel_report(self, period_start: datetime, period_end: datetime) -> dict:
        """Threat Intelligence Report for threat hunters."""
        report_id = self._report_id()
        stats = await self.aggregator.pipeline_summary()

        return {
            "report_id": report_id,
            "report_type": "threat_intelligence",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
            "ioc_overview": {
                "total_unique_iocs": len(stats.ioc_ips) + len(stats.ioc_domains) + len(stats.ioc_hashes) + len(stats.ioc_urls),
                "by_type": {
                    "ip": len(stats.ioc_ips),
                    "domain": len(stats.ioc_domains),
                    "hash": len(stats.ioc_hashes),
                    "url": len(stats.ioc_urls),
                },
                "top_sources": ["virustotal", "abuseipdb", "misp", "otx"],
            },
            "active_campaigns": [
                {
                    "campaign_id": cid,
                    "events": count,
                }
                for cid, count in Counter(list(stats.campaign_ids)).most_common(10)
            ] if stats.campaign_ids else [],
            "ioc_trends": [],
            "recommended_actions": [
                "Review top IOC hits and update firewall rules",
                "Validate MISP event synchronization",
                "Check threat feed API key status and rate limits",
            ],
        }

    async def generate_hygiene_report(self, period_start: datetime, period_end: datetime) -> dict:
        """IT Hygiene Report for security engineering."""
        report_id = self._report_id()
        stats = await self.aggregator.pipeline_summary()

        latest = self.aggregator._latest_ndjson()
        raw_events = []
        if latest:
            for event in self.aggregator._iter_ndjson(latest, 5000):
                raw_events.append(event)

        hygiene = self.calculator.compute_hygiene_score(raw_events)

        asset_risk = [
            {
                "hostname": ip,
                "risk_score": round(cnt / max(stats.asset_alert_counts.most_common(1)[0][1] if stats.asset_alert_counts else 1, 1) * 100, 1),
                "total_alerts": cnt,
                "department": "unknown",
            }
            for ip, cnt in stats.asset_alert_counts.most_common(20)
        ]

        concentration = self.calculator.compute_risk_concentration(asset_risk, 5)

        return {
            "report_id": report_id,
            "report_type": "it_hygiene",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
            "hygiene_score": hygiene,
            "vulnerability_exposure": {
                "total_vulnerable_assets": len(stats.asset_ips),
                "top_assets": [ip for ip, _ in stats.asset_alert_counts.most_common(10)],
            },
            "asset_risk_ranking": concentration,
            "remediation_recommendations": [
                {
                    "priority": "critical",
                    "action": f"Investigate top asset: {concentration[0].get('hostname', 'unknown')} — {concentration[0].get('pct_of_total', 0)}% of risk" if concentration else "No critical assets identified",
                    "risk_reduction_pct": concentration[0].get("pct_of_total", 0) if concentration else 0,
                }
            ] if concentration else [],
        }

    async def generate_shift_handover(self, shift_start: datetime, shift_end: datetime) -> dict:
        """Shift Handover Report for SOC analysts."""
        report_id = self._report_id()
        stats = await self.aggregator.pipeline_summary()

        period_events = stats.total
        critical = sum(v for k, v in stats.severity.items() if k >= 10)
        high = sum(v for k, v in stats.severity.items() if 7 <= k < 10)

        shift_data = {
            "new_incidents": {
                "total": period_events,
                "critical": critical,
                "high": high,
                "by_type": dict(stats.attack_types.most_common(5)),
            },
            "resolved_incidents": {
                "total": sum(stats.analyst_activity.values()),
                "false_positive": stats.verdicts.get("false_positive", 0),
                "true_positive": stats.true_positives,
                "noise": stats.noise_count,
                "by_analyst": dict(stats.analyst_activity.most_common()),
            },
            "open_incidents": {
                "total": period_events - sum(stats.analyst_activity.values()),
                "critical": critical,
                "high": high,
            },
            "escalations": {
                "tier_2": stats.escalations.get("tier2", 0),
                "tier_3": stats.escalations.get("incident", 0),
            },
            "threat_intel_hits": {
                "total": len(stats.ioc_ips) + len(stats.ioc_domains),
                "malicious": stats.true_positives,
            },
            "playbook_executions": {
                "total": sum(stats.playbook_outcomes.values()),
                "automated_actions": stats.playbook_outcomes.get("no_action_taken", 0),
            },
        }

        shift_summary = await self.ai_engine.generate_shift_summary(shift_data)

        return {
            "report_id": report_id,
            "report_type": "shift_handover",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "shift": {
                "start": shift_start.isoformat(),
                "end": shift_end.isoformat(),
            },
            **shift_data,
            "analyst_notes": [],
            "shift_summary": shift_summary,
        }

    async def generate(
        self, report_type: str, period_start: datetime, period_end: datetime, incident_id: str = ""
    ) -> dict:
        """Unified dispatch to the appropriate report generator."""
        generators = {
            "executive": self.generate_executive_report,
            "soc_operations": self.generate_soc_operations_report,
            "incident": lambda ps, pe: self.generate_incident_report(incident_id or "unknown"),
            "threat_intel": self.generate_threat_intel_report,
            "hygiene": self.generate_hygiene_report,
            "shift_handover": self.generate_shift_handover,
        }
        gen = generators.get(report_type)
        if not gen:
            raise ValueError(f"Unknown report type: {report_type}")
        return await gen(period_start, period_end)

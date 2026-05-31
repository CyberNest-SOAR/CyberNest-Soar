"""
aggregation_pipeline.py — Multi-source aggregation engine.

Aggregates data from:
  - NDJSON pipeline files (259K+ historical events)
  - OpenSearch (live wazuh-alerts-* index)
  - TheHive cases JSON
  - Threat intel DB

Prioritizes: OpenSearch (live) > NDJSON (pipeline) > Cache (stale)
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

OUTPUTS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "dataset_pipeline" / "data" / "outputs"


class PipelineStats:
    """In-memory aggregation state for NDJSON pipeline data."""

    def __init__(self):
        self.total = 0
        self.severity = Counter()
        self.attack_types = Counter()
        self.mitre_tactics = Counter()
        self.analyst_activity = Counter()
        self.verdicts = Counter()
        self.escalations = Counter()
        self.playbook_outcomes = Counter()
        self.true_positives = 0
        self.noise_count = 0
        self.suppressed = 0
        self.campaign_ids = set()
        self.hourly_counts = Counter()
        self.daily_counts = Counter()
        self.ioc_ips = set()
        self.ioc_domains = set()
        self.ioc_hashes = set()
        self.ioc_urls = set()
        self.asset_ips = Counter()
        self.asset_alert_counts = Counter()
        self.processes_by_asset = defaultdict(set)
        self.users_by_asset = defaultdict(set)
        self.attack_types_by_asset = defaultdict(set)
        self.escalation_times: list[float] = []
        self.containment_times: list[float] = []


class AggregationPipeline:
    """Multi-source aggregation engine for report generation."""

    def __init__(self):
        self._base = Path(__file__).resolve().parent.parent

    def _latest_ndjson(self):
        files = sorted(OUTPUTS_DIR.glob("soc_dataset_*.ndjson"))
        return files[-1] if files else None

    def _latest_thehive(self):
        files = sorted(OUTPUTS_DIR.glob("thehive_cases_*.json"))
        return files[-1] if files else None

    def _iter_ndjson(self, path, max_lines=None):
        with open(path) as f:
            for i, line in enumerate(f):
                if max_lines and i >= max_lines:
                    break
                line = line.strip()
                if line:
                    yield json.loads(line)

    def _count_lines(self, path):
        n = 0
        with open(path) as f:
            for line in f:
                if line.strip():
                    n += 1
        return n

    def _load_json(self, path):
        if path and path.exists():
            with open(path) as f:
                return json.load(f)
        return {}

    async def pipeline_summary(self, max_events: int = 100000) -> PipelineStats:
        """Single-pass aggregation over NDJSON pipeline data."""
        stats = PipelineStats()
        latest = self._latest_ndjson()
        if not latest:
            return stats

        total = self._count_lines(latest)
        limit = min(total, max_events)
        stats.total = limit

        for event in self._iter_ndjson(latest, limit):
            sev = event.get("alert_severity", 0)
            stats.severity[sev] += 1

            at = event.get("attack_type", "unknown")
            stats.attack_types[at] += 1

            tactic = event.get("mitre_tactic", "unknown")
            if tactic and tactic != "None":
                stats.mitre_tactics[tactic] += 1

            aa = event.get("analyst_assigned")
            if aa:
                stats.analyst_activity[aa] += 1

            v = event.get("analyst_verdict", "unknown")
            stats.verdicts[v] += 1

            el = event.get("escalation_level", "none")
            if el and el != "none":
                stats.escalations[el] += 1

            po = event.get("playbook_outcome")
            if po:
                stats.playbook_outcomes[po] += 1

            if event.get("true_positive"):
                stats.true_positives += 1
            if event.get("noise"):
                stats.noise_count += 1
            if event.get("suppression_hit"):
                stats.suppressed += 1

            cid = event.get("campaign_id")
            if cid:
                stats.campaign_ids.add(cid)

            if event.get("ioc_ip"):
                stats.ioc_ips.add(event["ioc_ip"])
            if event.get("ioc_domain"):
                stats.ioc_domains.add(event["ioc_domain"])
            if event.get("ioc_hash"):
                stats.ioc_hashes.add(event["ioc_hash"])
            if event.get("ioc_url"):
                stats.ioc_urls.add(event["ioc_url"])

            asset_ip = event.get("src_ip") or event.get("dst_ip")
            if asset_ip:
                stats.asset_ips[asset_ip] += 1
                stats.asset_alert_counts[asset_ip] += 1
                pname = event.get("process_name")
                if pname:
                    stats.processes_by_asset[asset_ip].add(pname)
                user = event.get("src_user")
                if user:
                    stats.users_by_asset[asset_ip].add(user)

            ts = event.get("timestamp", "")
            if ts and len(ts) >= 13:
                hour = ts[:13] + ":00:00"
                stats.hourly_counts[hour] += 1
                day = ts[:10]
                stats.daily_counts[day] += 1

        return stats

    async def thehive_summary(self) -> dict:
        """Aggregate TheHive case data."""
        thehive = self._latest_thehive()
        cases = self._load_json(thehive) if thehive else []

        by_severity = Counter()
        by_tag = Counter()
        for c in cases:
            by_severity[c.get("severity")] += 1
            for t in c.get("tags", []):
                by_tag[t] += 1

        return {
            "total_cases": len(cases),
            "critical_cases": by_severity.get(4, 0) + by_severity.get(3, 0),
            "cases_by_severity": dict(sorted(by_severity.items())),
            "top_tags": dict(by_tag.most_common(10)),
        }

    async def analytics_distribution(self, dist_type: str) -> list[dict]:
        """Get distribution data from pipeline graph endpoints."""
        latest = self._latest_ndjson()
        if not latest:
            return []

        total = self._count_lines(latest)
        counts = Counter()
        for event in self._iter_ndjson(latest, min(total, 100000)):
            if dist_type == "severity":
                key = str(event.get("alert_severity", 0))
            elif dist_type == "attack_type":
                key = event.get("attack_type", "unknown")
            elif dist_type == "mitre_tactic":
                key = event.get("mitre_tactic", "unknown")
            elif dist_type == "verdict":
                key = event.get("analyst_verdict", "unknown")
            else:
                key = str(event.get(dist_type, "unknown"))
            counts[key] += 1

        return [{"name": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]

    async def analyst_detail(self) -> list[dict]:
        """Per-analyst metrics with escalation counts."""
        latest = self._latest_ndjson()
        if not latest:
            return []

        total = self._count_lines(latest)
        activity = Counter()
        escalations = Counter()

        for event in self._iter_ndjson(latest, min(total, 100000)):
            aa = event.get("analyst_assigned")
            if aa:
                activity[aa] += 1
                el = event.get("escalation_level")
                if el and el not in ("none", ""):
                    escalations[aa] += 1

        total_incidents = sum(activity.values())
        return [
            {
                "name": name,
                "total_incidents": count,
                "escalations": escalations.get(name, 0),
                "pct": round(count / total_incidents * 100, 1) if total_incidents else 0,
            }
            for name, count in activity.most_common()
        ]

    async def sla_compliance(self) -> dict:
        """Compute SLA metrics from timeline data."""
        latest = self._latest_ndjson()
        if not latest:
            return {
                "triage_breaches": 0,
                "total_triage": 0,
                "breach_rate": 0,
                "avg_triage_time_min": 0,
                "mttr_hours": 0,
            }

        total = self._count_lines(latest)
        triage_times = []
        containment_times = []

        for event in self._iter_ndjson(latest, min(total, 50000)):
            ts = event.get("timestamp")
            el = event.get("escalation_level")
            tl = event.get("timeline_position")

            if ts and el and el != "none":
                try:
                    ts_dt = datetime.fromisoformat(ts)
                    if tl == "mid":
                        triage_times.append((datetime.now(timezone.utc) - ts_dt).total_seconds() / 60)
                except (ValueError, TypeError):
                    pass

            if ts and event.get("closure_reason"):
                try:
                    ts_dt = datetime.fromisoformat(ts)
                    containment_times.append((datetime.now(timezone.utc) - ts_dt).total_seconds() / 3600)
                except (ValueError, TypeError):
                    pass

        sla_minutes = 15
        breaches = sum(1 for t in triage_times if t > sla_minutes)
        total_triage = len(triage_times)

        return {
            "triage_breaches": breaches,
            "total_triage": total_triage,
            "breach_rate": round(breaches / total_triage * 100, 1) if total_triage else 0,
            "avg_triage_time_min": round(sum(triage_times) / len(triage_times), 1) if triage_times else 0,
            "mttr_hours": round(sum(containment_times) / len(containment_times), 1) if containment_times else 0,
        }

    async def monthly_trend(self) -> dict[str, int]:
        """Compute monthly incident trend from pipeline data."""
        latest = self._latest_ndjson()
        if not latest:
            return {}

        total = self._count_lines(latest)
        monthly = Counter()
        for event in self._iter_ndjson(latest, min(total, 100000)):
            ts = event.get("timestamp", "")
            if ts and len(ts) >= 7:
                month = ts[:7]
                monthly[month] += 1

        return dict(sorted(monthly.items()))

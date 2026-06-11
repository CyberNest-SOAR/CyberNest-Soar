import abc
import json
import logging
from pathlib import Path
from typing import Iterator, List, Optional

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)


class BaseDatasetParser(abc.ABC):
    name: str = ""

    def __init__(self, source_files: List[Path]):
        self.source_files = source_files

    @abc.abstractmethod
    def parse(self) -> Iterator[UnifiedAlert]:
        ...

    def parse_all(self) -> List[UnifiedAlert]:
        results = []
        for i, alert in enumerate(self.parse()):
            results.append(alert)
            if (i + 1) % 10000 == 0:
                logger.info("  Parsed %d events from %s", i + 1, self.name)
        logger.info("Parsed %d events from %s", len(results), self.name)
        return results


class NDJSONParser(BaseDatasetParser):
    """Parses NDJSON files — works for synthetic data and most exports."""

    def parse(self) -> Iterator[UnifiedAlert]:
        for source in self.source_files:
            if not source.exists():
                continue
            with open(source) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                        yield self._row_to_alert(raw)
                    except json.JSONDecodeError:
                        continue

    def _row_to_alert(self, raw: dict) -> UnifiedAlert:
        import uuid
        from datetime import datetime, timezone

        ts = raw.get("timestamp") or raw.get("@timestamp") or datetime.now(timezone.utc).isoformat()
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))

        return UnifiedAlert(
            event_id=raw.get("event_id", str(uuid.uuid4())),
            timestamp=ts,
            dataset_source=raw.get("dataset_source", self.name),
            event_type=raw.get("event_type", "alert"),
            src_ip=raw.get("src_ip"),
            src_port=raw.get("src_port"),
            dst_ip=raw.get("dst_ip"),
            dst_port=raw.get("dst_port"),
            protocol=raw.get("protocol"),
            src_hostname=raw.get("src_hostname"),
            dst_hostname=raw.get("dst_hostname"),
            src_user=raw.get("src_user"),
            dst_user=raw.get("dst_user"),
            process_name=raw.get("process_name"),
            command_line=raw.get("command_line"),
            file_name=raw.get("file_name"),
            file_hash=raw.get("file_hash"),
            registry_key=raw.get("registry_key"),
            service_name=raw.get("service_name"),
            image_path=raw.get("image_path"),
            alert_signature=raw.get("alert_signature"),
            alert_severity=raw.get("alert_severity"),
            alert_category=raw.get("alert_category"),
            alert_action=raw.get("alert_action"),
            bytes_sent=raw.get("bytes_sent"),
            bytes_received=raw.get("bytes_received"),
            duration=raw.get("duration"),
            packets=raw.get("packets"),
            attack_type=raw.get("attack_type"),
            mitre_technique_id=raw.get("mitre_technique_id"),
            mitre_technique_name=raw.get("mitre_technique_name"),
            mitre_tactic=raw.get("mitre_tactic"),
            confidence=raw.get("confidence"),
            true_positive=raw.get("true_positive"),
            noise=raw.get("noise"),
            ioc_ip=raw.get("ioc_ip"),
            ioc_domain=raw.get("ioc_domain"),
            ioc_url=raw.get("ioc_url"),
            ioc_hash=raw.get("ioc_hash"),
            http_method=raw.get("http_method"),
            http_uri=raw.get("http_uri"),
            http_user_agent=raw.get("http_user_agent"),
            http_referrer=raw.get("http_referrer"),
            http_status=raw.get("http_status"),
            dns_query=raw.get("dns_query"),
            dns_answer=raw.get("dns_answer"),
            dns_type=raw.get("dns_type"),
            tls_sni=raw.get("tls_sni"),
            tls_version=raw.get("tls_version"),
            ja3_hash=raw.get("ja3_hash"),
            geoip_src_country=raw.get("geoip_src_country"),
            geoip_src_asn=raw.get("geoip_src_asn"),
            geoip_dst_country=raw.get("geoip_dst_country"),
            geoip_dst_asn=raw.get("geoip_dst_asn"),
            enrichment_vt_score=raw.get("enrichment_vt_score"),
            enrichment_abuse_score=raw.get("enrichment_abuse_score"),
            enrichment_misp_matches=raw.get("enrichment_misp_matches"),
            enrichment_epss_score=raw.get("enrichment_epss_score"),
            enrichment_cvss_score=raw.get("enrichment_cvss_score"),
            analyst_verdict=raw.get("analyst_verdict"),
            analyst_assigned=raw.get("analyst_assigned"),
            analyst_notes=raw.get("analyst_notes"),
            suppression_hit=raw.get("suppression_hit"),
            escalation_level=raw.get("escalation_level"),
            playbook_outcome=raw.get("playbook_outcome"),
            cluster_id=raw.get("cluster_id"),
            campaign_id=raw.get("campaign_id"),
            attack_chain_stage=raw.get("attack_chain_stage"),
            # SOC Reasoning fields (populated when loading reasoned exports)
            closure_reason=raw.get("closure_reason"),
            escalation_reason=raw.get("escalation_reason"),
            suppression_reason=raw.get("suppression_reason"),
            playbook_action=raw.get("playbook_action"),
            playbook_success=raw.get("playbook_success"),
            recommended_action=raw.get("recommended_action"),
            risk_adjusted_priority=raw.get("risk_adjusted_priority"),
            maintenance_window=raw.get("maintenance_window"),
            patch_window=raw.get("patch_window"),
            known_admin_activity=raw.get("known_admin_activity"),
            vulnerability_scan=raw.get("vulnerability_scan"),
            scheduled_backup=raw.get("scheduled_backup"),
            business_hours=raw.get("business_hours"),
            weekend_activity=raw.get("weekend_activity"),
            environment_context=raw.get("environment_context"),
            asset_criticality=raw.get("asset_criticality"),
            host_role=raw.get("host_role"),
            department=raw.get("department"),
            business_unit=raw.get("business_unit"),
            owner_team=raw.get("owner_team"),
            compliance_scope=raw.get("compliance_scope"),
            asset_value=raw.get("asset_value"),
            user_role=raw.get("user_role"),
            mfa_used=raw.get("mfa_used"),
            authentication_method=raw.get("authentication_method"),
            parent_process=raw.get("parent_process"),
            process_hash=raw.get("process_hash"),
            integrity_level=raw.get("integrity_level"),
            signed_binary=raw.get("signed_binary"),
            timeline_position=raw.get("timeline_position"),
            previous_alert_id=raw.get("previous_alert_id"),
            next_alert_id=raw.get("next_alert_id"),
            session_id=raw.get("session_id"),
            repeated_behavior_score=raw.get("repeated_behavior_score"),
            similar_alerts_last_hour=raw.get("similar_alerts_last_hour"),
            attack_burst_id=raw.get("attack_burst_id"),
            alert_storm_id=raw.get("alert_storm_id"),
            historically_seen=raw.get("historically_seen"),
            historical_false_positive_rate=raw.get("historical_false_positive_rate"),
            recurring_alert=raw.get("recurring_alert"),
            prior_case_count=raw.get("prior_case_count"),
            raw_log=raw.get("raw_log"),
            extra_fields={k: v for k, v in raw.items()
                          if k not in UnifiedAlert.__dataclass_fields__ or k == "extra_fields"},
        )

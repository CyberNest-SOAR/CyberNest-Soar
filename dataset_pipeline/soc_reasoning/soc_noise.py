import logging
import random
import uuid
from datetime import timedelta
from typing import Dict, List, Optional

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)

_SCCM_HOSTS = ["sccm-01.corp.local", "sccm-02.corp.local"]
_KNOWN_ADMIN_HOSTS = ["jumpbox-01", "jumpbox-02", "bastion.prod"]
_SCANNER_IPS = ["10.0.0.200", "10.0.0.201", "172.16.0.200", "192.168.1.200"]
_SCANNER_HOSTS = ["nessus-scanner-01", "qualys-scanner-01", "rapid7-nexpose-01"]
_BACKUP_HOSTS = ["backup-server-01", "veeam-bkp-01", "netbackup-01"]


def inject_enterprise_noise(alerts: List[UnifiedAlert],
                            seed: Optional[int] = None) -> List[UnifiedAlert]:
    if not alerts:
        return alerts
    rng = random.Random(seed)
    extra_noise = []

    # Track per-signature counters for alert storm injection
    sig_counters: Dict[str, int] = {}

    for alert in alerts:
        sig = alert.alert_signature or alert.attack_type or "unknown"
        sig_counters[sig] = sig_counters.get(sig, 0) + 1

    def _noise_hash(rng):
        return f"SHA256-{rng.randint(0, 0xFFFFFFFFFFFFFFFF):016x}{rng.randint(0, 0xFFFFFFFFFFFFFFFF):016x}"

    # Inject SCCM deployment noise
    sccm_count = max(5, int(len(alerts) * 0.03))
    for i in range(sccm_count):
        ts = rng.choice(alerts).timestamp + timedelta(seconds=rng.randint(-300, 300))
        extra_noise.append(UnifiedAlert(
            event_id=f"sccm-noise-{uuid.uuid4().hex[:8]}",
            timestamp=ts,
            dataset_source="synthetic.sccm",
            event_type="alert",
            src_ip="10.0.0.50",
            dst_ip=rng.choice(["10.0.0.10", "10.0.0.100", "192.168.1.10", "192.168.1.100"]),
            dst_port=445,
            protocol="TCP",
            alert_signature="SCCM Policy Request — Software Deployment",
            alert_severity=3,
            alert_category="benign",
            attack_type="benign",
            mitre_technique_id="T9999",
            true_positive=False,
            noise=True,
            confidence=0.99,
            known_admin_activity=True,
            maintenance_window=True,
            src_user="sccm_svc",
            user_role="service_account",
            process_name="ccmexec.exe",
            parent_process="svchost.exe",
            command_line="-policy:Deployment",
            process_hash=_noise_hash(rng),
            host_role="sccm_server",
            asset_criticality="high",
            department="IT",
            analyst_verdict="false_positive" if rng.random() < 0.9 else "benign",
            analyst_assigned=rng.choice(["jdoe", "asmith", "mwilson"]),
            analyst_notes="SCCM deployment during maintenance window — expected behavior.",
            suppression_hit=True,
            suppression_reason="Known SCCM activity during approved change window.",
            closure_reason="Confirmed SCCM deployment. No action needed.",
            playbook_action="No action needed",
            playbook_outcome="no_action_taken",
            environment_context="Scheduled maintenance window — SCCM software deployment.",
        ))

    # Inject vulnerability scanner noise
    scan_count = max(8, int(len(alerts) * 0.04))
    for i in range(scan_count):
        ts = rng.choice(alerts).timestamp + timedelta(seconds=rng.randint(-600, 600))
        scanner_ip = rng.choice(_SCANNER_IPS)
        target_ip = rng.choice(["10.0.0.1", "10.0.0.10", "172.16.0.1", "192.168.1.1"])
        extra_noise.append(UnifiedAlert(
            event_id=f"scan-noise-{uuid.uuid4().hex[:8]}",
            timestamp=ts,
            dataset_source="synthetic.scanner",
            event_type="alert",
            src_ip=scanner_ip,
            dst_ip=target_ip,
            src_port=rng.randint(40000, 65000),
            dst_port=rng.choice([22, 80, 443, 445, 3306, 3389, 8080]),
            protocol="TCP",
            alert_signature=rng.choice([
                "Nessus Scan Detected — Plugin ID 12345",
                "Qualys Agent Activity — Port Enumeration",
                "Rapid7 Nexpose — Service Discovery",
                "Network Scan — Unusual Port Sweep",
                "Vulnerability Assessment — SSL/TLS Version Detection",
            ]),
            alert_severity=4,
            alert_category="scanning",
            attack_type="scanning",
            mitre_technique_id="T1046",
            true_positive=False,
            noise=True,
            confidence=0.95,
            vulnerability_scan=True,
            business_hours=True,
            known_admin_activity=True,
            src_user="nessus_svc",
            user_role="service_account",
            process_name="nessusd",
            parent_process="systemd",
            process_hash=_noise_hash(rng),
            host_role="security_scanner",
            asset_criticality="medium",
            department="Security",
            analyst_verdict="false_positive",
            analyst_assigned=rng.choice(["klee", "tpark", "sgarcia"]),
            analyst_notes="Quarterly vulnerability scan — authorized activity. Correlate with Qualys schedule.",
            suppression_hit=True,
            suppression_reason="Authorized vulnerability scan window.",
            closure_reason="Authorized security assessment. Rule updated for scan IP whitelist.",
            environment_context="Quarterly compliance scan in progress.",
        ))

    # Inject backup traffic noise
    backup_count = max(5, int(len(alerts) * 0.02))
    for i in range(backup_count):
        ts = rng.choice(alerts).timestamp + timedelta(seconds=rng.randint(-1800, 1800))
        extra_noise.append(UnifiedAlert(
            event_id=f"backup-noise-{uuid.uuid4().hex[:8]}",
            timestamp=ts,
            dataset_source="synthetic.backup",
            event_type="alert",
            src_ip="10.0.0.30",
            dst_ip=rng.choice(["10.0.0.31", "10.0.0.32", "10.0.0.33"]),
            dst_port=445,
            protocol="TCP",
            alert_signature=rng.choice([
                "Veeam Backup — Large SMB Transfer",
                "Backup Agent — Database Dump Detected",
                "VSS Snapshot — Volume Shadow Copy Activity",
                "Rsync Transfer — Large Data Movement",
            ]),
            alert_severity=3,
            alert_category="benign",
            attack_type="benign",
            mitre_technique_id="T9999",
            true_positive=False,
            noise=True,
            confidence=0.98,
            scheduled_backup=True,
            known_admin_activity=True,
            src_user="backup_svc",
            user_role="service_account",
            process_name=rng.choice(["veeamagent.exe", "rsync", "sqlservr.exe", "cobian_backup.exe"]),
            parent_process="services.exe",
            process_hash=_noise_hash(rng),
            host_role="backup_server",
            asset_criticality="high",
            department="IT",
            analyst_verdict="benign",
            analyst_notes="Scheduled nightly backup — expected large data transfer.",
            suppression_hit=rng.random() < 0.7,
            closure_reason="Backup window — expected activity.",
        ))

    # Inject SIEM duplicate storms (alert storm simulation)
    storm_count = max(3, int(len(alerts) * 0.015))
    for i in range(storm_count):
        base_alert = rng.choice(alerts)
        storm_size = rng.randint(3, 8)
        for j in range(storm_size):
            dup = UnifiedAlert(
                event_id=f"storm-dup-{uuid.uuid4().hex[:8]}",
                timestamp=base_alert.timestamp + timedelta(seconds=rng.randint(1, 30) * j),
                dataset_source=base_alert.dataset_source,
                event_type=base_alert.event_type,
                src_ip=base_alert.src_ip,
                dst_ip=base_alert.dst_ip,
                src_port=base_alert.src_port,
                dst_port=base_alert.dst_port,
                protocol=base_alert.protocol,
                alert_signature=base_alert.alert_signature,
                alert_severity=base_alert.alert_severity,
                alert_category=base_alert.alert_category,
                attack_type=base_alert.attack_type or "benign",
                mitre_technique_id=base_alert.mitre_technique_id,
                true_positive=False,
                noise=True,
                confidence=0.5,
            process_hash=base_alert.process_hash or _noise_hash(rng),
            suppression_hit=True,
            suppression_reason=f"Duplicate storm — {storm_size} identical alerts in {storm_size * 30}s",
            extra_fields={"duplicate_of": base_alert.event_id, "storm": True},
                analyst_verdict="false_positive",
            )
            extra_noise.append(dup)

    alerts.extend(extra_noise)
    rng.shuffle(alerts)

    # Inject SOC workflow inconsistencies
    _inject_workflow_inconsistencies(alerts, rng)

    logger.info("Injected %d enterprise-noise alerts (SCCM, scanners, backups, storms)",
                len(extra_noise))
    return alerts


def _inject_workflow_inconsistencies(alerts: List[UnifiedAlert], rng: random.Random):
    # Conflicting analyst decisions (different analysts, different verdicts on same signature)
    sig_groups: Dict[str, List[UnifiedAlert]] = {}
    for a in alerts:
        sig = (a.alert_signature or a.attack_type or "unknown")
        sig_groups.setdefault(sig, []).append(a)

    for sig, group in sig_groups.items():
        if len(group) < 3 or rng.random() > 0.15:
            continue
        # Pick two alerts in same group, give them conflicting verdicts
        a1, a2 = rng.sample(group, 2)
        a1.analyst_verdict = "true_positive"
        a1.analyst_assigned = rng.choice(["jdoe", "asmith"])
        a1.escalation_level = "tier2"
        a2.analyst_verdict = "false_positive"
        a2.analyst_assigned = rng.choice(["mwilson", "klee"])
        a2.escalation_level = "none"
        a1.extra_fields["conflicting_verdict"] = f"{a2.event_id}:{a2.analyst_verdict}"
        a2.extra_fields["conflicting_verdict"] = f"{a1.event_id}:{a1.analyst_verdict}"

    # Partial investigations — 8% of alerts have analyst_assigned but no verdict
    for alert in alerts:
        if rng.random() < 0.08 and alert.analyst_assigned:
            alert.analyst_verdict = None
            alert.analyst_notes = "Assigned but not yet reviewed — pending queue."
            alert.extra_fields["partial_investigation"] = True

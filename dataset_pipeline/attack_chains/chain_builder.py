import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)

_CHAIN_DEFINITIONS = [
    {
        "name": "phishing_to_exfil",
        "stages": [
            ("phishing", "T1566", "Initial Access", 1),
            ("malware", "T1204", "Execution", 2),
            ("privilege_escalation", "T1059", "Execution", 3),
            ("lateral_movement", "T1021", "Lateral Movement", 4),
            ("credential_dumping", "T1003", "Credential Access", 5),
            ("exfiltration", "T1048", "Exfiltration", 6),
        ],
    },
    {
        "name": "web_exploit_to_ransomware",
        "stages": [
            ("web_attack", "T1190", "Initial Access", 1),
            ("malware", "T1204", "Execution", 2),
            ("privilege_escalation", "T1548", "Privilege Escalation", 3),
            ("persistence", "T1547", "Persistence", 4),
            ("lateral_movement", "T1021", "Lateral Movement", 5),
            ("exfiltration", "T1048", "Exfiltration", 6),
        ],
    },
    {
        "name": "brute_force_to_compromise",
        "stages": [
            ("brute_force", "T1110", "Credential Access", 1),
            ("lateral_movement", "T1021", "Lateral Movement", 2),
            ("malware", "T1204", "Execution", 3),
            ("exfiltration", "T1048", "Exfiltration", 4),
        ],
    },
]


def build_attack_chains(alerts: List[UnifiedAlert],
                        chain_count: int = 10,
                        seed: Optional[int] = None) -> List[UnifiedAlert]:
    rng = random.Random(seed)
    malicious = [a for a in alerts if a.true_positive]
    if len(malicious) < chain_count * 3:
        logger.warning("Not enough malicious alerts for %d chains (%d available)",
                       chain_count, len(malicious))
        return alerts

    chain_alerts = []
    used_indices = set()

    for chain_idx in range(chain_count):
        definition = rng.choice(_CHAIN_DEFINITIONS)
        base_time = datetime.now(timezone.utc) - timedelta(days=rng.randint(1, 30))
        src_ip = rng.choice(["198.51.100.7", "185.220.101.42", "203.0.113.5",
                             "45.33.32.156", "104.16.0.1"])
        dst_ip = rng.choice(["10.0.0.1", "10.0.0.10", "10.0.0.50",
                             "172.16.0.10", "192.168.1.100"])
        campaign_id = f"chain-cmp-{uuid.uuid4().hex[:8]}"

        for stage_idx, (atk, mitre_id, tactic, stage_num) in enumerate(definition["stages"]):
            ts = base_time + timedelta(
                hours=rng.randint(0, 48 * stage_idx),
                minutes=rng.randint(0, 59),
            )

            sev = {
                1: rng.choice([5, 6, 7]),
                2: rng.choice([6, 7, 8]),
                3: rng.choice([7, 8, 9]),
                4: rng.choice([8, 9, 10]),
                5: rng.choice([9, 10, 12]),
                6: rng.choice([10, 12, 14]),
            }.get(stage_num, 7)

            alert = UnifiedAlert(
                event_id=f"chain-{chain_idx}-stage-{stage_num}-{uuid.uuid4().hex[:6]}",
                timestamp=ts,
                dataset_source="attack_chain",
                event_type="alert",
                src_ip=src_ip if stage_num % 2 == 1 else dst_ip,
                dst_ip=dst_ip if stage_num % 2 == 1 else src_ip,
                src_port=rng.choice([22, 443, 8080, 3389, 445]),
                dst_port=rng.choice([80, 443, 22, 445, 3389, 8080]),
                protocol="TCP",
                alert_signature=f"Attack Chain Stage {stage_num}: {tactic}",
                alert_severity=sev,
                alert_category=atk,
                attack_type=atk,
                mitre_technique_id=mitre_id,
                mitre_technique_name=_mitre_name_from_id(mitre_id),
                mitre_tactic=tactic,
                true_positive=True,
                noise=False,
                confidence=round(0.7 + rng.random() * 0.25, 4),
                campaign_id=campaign_id,
                cluster_id=f"chain-{chain_idx}",
                attack_chain_stage=stage_num,
                extra_fields={"chain_name": definition["name"], "chain_stage_total": len(definition["stages"])},
            )
            chain_alerts.append(alert)

    alerts.extend(chain_alerts)
    logger.info("Built %d attack chains (%d stages total)", chain_count, len(chain_alerts))
    return alerts


def _mitre_name_from_id(technique_id: str) -> str:
    names = {
        "T1566": "Phishing", "T1204": "User Execution",
        "T1059": "Command and Scripting Interpreter",
        "T1021": "Remote Services", "T1003": "OS Credential Dumping",
        "T1048": "Exfiltration Over Alternative Protocol",
        "T1190": "Exploit Public-Facing Application",
        "T1548": "Abuse Elevation Control Mechanism",
        "T1547": "Boot or Logon Autostart Execution",
        "T1110": "Brute Force",
    }
    return names.get(technique_id, "Unknown")

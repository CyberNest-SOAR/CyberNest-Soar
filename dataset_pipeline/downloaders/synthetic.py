"""
Generates realistic synthetic network/log data when real downloads fail or
when REAL_DOWNLOADS_ENABLED=false.
"""
import json
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

_PUBLIC_IPS = [
    "8.8.8.8", "8.8.4.4", "1.1.1.1", "185.220.101.42",
    "198.51.100.7", "203.0.113.5", "45.33.32.156",
    "104.16.0.1", "151.101.1.1", "192.0.2.1",
]

_PRIVATE_IPS = [
    "10.0.0.1", "10.0.0.10", "10.0.0.50", "10.0.0.100",
    "172.16.0.1", "172.16.0.10", "172.16.0.50",
    "192.168.1.1", "192.168.1.10", "192.168.1.100",
    "192.168.50.1", "192.168.50.100",
]

_PORT_TABLE = {22: "SSH", 80: "HTTP", 443: "HTTPS", 53: "DNS", 25: "SMTP",
               3306: "MySQL", 3389: "RDP", 445: "SMB", 1433: "MSSQL", 8080: "HTTP-ALT"}

_ATTACK_TYPES = ["benign", "brute_force", "malware", "phishing", "ddos",
                 "lateral_movement", "privilege_escalation", "exfiltration",
                 "scanning", "web_attack"]

_MITRE_MAP = {
    "brute_force": ("T1110", "Brute Force", "Credential Access"),
    "malware": ("T1204", "User Execution", "Execution"),
    "phishing": ("T1566", "Phishing", "Initial Access"),
    "ddos": ("T1498", "Network Denial of Service", "Impact"),
    "lateral_movement": ("T1021", "Remote Services", "Lateral Movement"),
    "privilege_escalation": ("T1059", "Command and Scripting Interpreter", "Execution"),
    "exfiltration": ("T1048", "Exfiltration Over Alternative Protocol", "Exfiltration"),
    "scanning": ("T1046", "Network Service Scanning", "Discovery"),
    "web_attack": ("T1190", "Exploit Public-Facing Application", "Initial Access"),
    "benign": ("T9999", "Benign", "None"),
}


def generate_synthetic_dataset(
    name: str,
    target_count: int,
    output_dir: Path,
    start_time: Optional[datetime] = None,
    malicious_ratio: float = 0.35,
) -> Path:
    start = start_time or datetime.now(timezone.utc) - timedelta(days=30)
    base_ts = start.timestamp()
    rng = random.Random(hash(name))
    output = []
    malware_count = int(target_count * malicious_ratio)
    benign_count = target_count - malware_count

    # Benign events
    for i in range(benign_count):
        src = rng.choice(_PRIVATE_IPS)
        dst = rng.choice(_PUBLIC_IPS + _PRIVATE_IPS)
        ts = base_ts + rng.random() * 30 * 86400
        port = rng.choice(list(_PORT_TABLE.keys()))
        proto = _PORT_TABLE[port]
        output.append({
            "event_id": f"syn-{name}-{i:06d}",
            "timestamp": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
            "dataset_source": f"synthetic.{name}",
            "event_type": "flow",
            "src_ip": src,
            "src_port": rng.randint(1024, 65535),
            "dst_ip": dst,
            "dst_port": port,
            "protocol": "TCP" if port != 53 else "UDP",
            "alert_signature": f"Benign {proto} traffic",
            "alert_severity": rng.choice([0, 1, 2]),
            "alert_category": "normal",
            "attack_type": "benign",
            "mitre_technique_id": "T9999",
            "true_positive": False,
            "noise": rng.random() < 0.15,
            "bytes_sent": rng.randint(100, 50000),
            "bytes_received": rng.randint(200, 200000),
            "duration": round(rng.random() * 120, 3),
        })

    # Malicious events
    for i in range(malware_count):
        atk = rng.choices(
            ["brute_force", "malware", "phishing", "ddos", "lateral_movement",
             "privilege_escalation", "exfiltration", "scanning", "web_attack"],
            weights=[15, 15, 10, 10, 10, 8, 7, 15, 10]
        )[0]
        src = rng.choice(_PUBLIC_IPS + _PRIVATE_IPS)
        dst = rng.choice(_PRIVATE_IPS)
        ts = base_ts + rng.random() * 30 * 86400
        mitre = _MITRE_MAP.get(atk, ("T9999", "Unknown", "Other"))
        sev = rng.choices([4, 5, 6, 7, 8, 9, 10, 12, 14], weights=[5, 10, 10, 15, 15, 10, 10, 5, 3])[0]
        output.append({
            "event_id": f"syn-{name}-mal-{i:06d}",
            "timestamp": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
            "dataset_source": f"synthetic.{name}",
            "event_type": "alert",
            "src_ip": src,
            "src_port": rng.randint(1024, 65535),
            "dst_ip": dst,
            "dst_port": rng.choice([22, 80, 443, 445, 3389, 8080]),
            "protocol": "TCP",
            "alert_signature": f"{atk.replace('_', ' ').title()} detected",
            "alert_severity": sev,
            "alert_category": atk,
            "attack_type": atk,
            "mitre_technique_id": mitre[0],
            "mitre_technique_name": mitre[1],
            "mitre_tactic": mitre[2],
            "true_positive": rng.random() < 0.85,
            "noise": rng.random() < 0.08,
            "bytes_sent": rng.randint(50, 15000),
            "bytes_received": rng.randint(100, 50000),
            "duration": round(rng.random() * 60, 3),
            "confidence": round(rng.random() * 0.4 + 0.5, 4),
        })

    # Shuffle to interleave malicious and benign
    rng.shuffle(output)

    dest = output_dir / f"{name}_synthetic.ndjson"
    with open(dest, "w") as f:
        for event in output:
            f.write(json.dumps(event) + "\n")
    logger.info("Generated %d synthetic events for %s -> %s", len(output), name, dest)
    return dest


def generate_fallback_for_missing(name: str, output_dir: Path) -> List[Path]:
    counts = {
        "cicids2017": 50000,
        "cicids2018": 50000,
        "ctu13": 20000,
        "unsw_nb15": 30000,
        "ton_iot": 25000,
        "lanl_auth": 50000,
        "cert_insider": 30000,
        "sysmon": 20000,
    }
    count = counts.get(name, 10000)
    p = generate_synthetic_dataset(name, count, output_dir)
    return [p]

"""
simulation_engine/config.py — Shared configuration loader.

Loads attack_profiles.yaml and provides typed access to all settings.
"""

import os
import yaml
import random
from typing import Dict, List, Any
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "config" / "attack_profiles.yaml"
_CONFIG: Dict[str, Any] = {}


def load_config(path: str = None) -> Dict[str, Any]:
    global _CONFIG
    p = Path(path) if path else _CONFIG_PATH
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")
    with open(p) as f:
        _CONFIG = yaml.safe_load(f)
    return _CONFIG


def get_config() -> Dict[str, Any]:
    if not _CONFIG:
        load_config()
    return _CONFIG


def get_attack_distribution() -> Dict[str, int]:
    raw = get_config().get("attack_distribution", {})
    total = sum(raw.values())
    if total == 0:
        return {}
    return {k: round(v / total * 100, 1) for k, v in raw.items()}


def get_ioc_pool(pool: str) -> List[Any]:
    pools = get_config().get("ioc_pools", {})
    return pools.get(pool, [])


def pick_random_ip(public: bool = True) -> str:
    pool = "public_ips" if public else "private_ips"
    ips = get_ioc_pool(pool)
    return random.choice(ips) if ips else "127.0.0.1"


def pick_random_port() -> int:
    ports = get_ioc_pool("ports")
    return random.choice(ports) if ports else 80


def pick_random_domain() -> str:
    domains = get_ioc_pool("domains")
    return random.choice(domains) if domains else "example.com"


def pick_random_hostname() -> str:
    hosts = get_ioc_pool("hostnames")
    return random.choice(hosts) if hosts else "unknown-host"


def pick_random_hash(hash_type: str = "sha256") -> str:
    pool = get_ioc_pool("hashes")
    if isinstance(pool, dict):
        return random.choice(pool.get(hash_type, ["a" * 64]))
    return "a" * 64


def get_mitre(attack_type: str) -> Dict[str, str]:
    mappings = get_config().get("mitre_mappings", {})
    return mappings.get(attack_type, {
        "technique_id": "T9999",
        "technique_name": "Unknown",
        "tactic": "None",
    })


def get_simulation_setting(key: str, default=None):
    sim = get_config().get("simulation", {})
    return sim.get(key, default)


def get_telemetry_setting(service: str, key: str, default=None):
    tel = get_config().get("telemetry", {})
    svc = tel.get(service, {})
    return svc.get(key, default)


def get_seed() -> int:
    return get_simulation_setting("seed", 42)


def get_total_events() -> int:
    return get_simulation_setting("total_events", 1000)


def get_campaign_id() -> str:
    cid = get_simulation_setting("campaign_id", "")
    if not cid:
        import uuid
        cid = str(uuid.uuid4())[:8]
    return cid


def set_campaign_id(cid: str):
    _CONFIG.setdefault("simulation", {})["campaign_id"] = cid

"""
generators/base.py — Abstract base class for all attack generators.

Each generator produces a list of ``RawEvent`` dicts with consistent
metadata (timestamps, MITRE ATT&CK, severity, labels).  Telemetry
formatters later convert these into tool-specific formats.
"""

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from config import (
    get_mitre,
    pick_random_ip,
    pick_random_port,
    pick_random_hostname,
    get_seed,
    get_simulation_setting,
)


class RawEvent:
    """Structured internal representation of a single generated event."""

    __slots__ = (
        "event_id", "campaign_id", "attack_type", "subtype",
        "timestamp", "severity", "confidence", "true_positive", "noise",
        "src_ip", "dst_ip", "src_port", "dst_port", "protocol",
        "hostname", "domain", "uri", "user_agent",
        "mitre_technique_id", "mitre_technique_name", "mitre_tactic",
        "process_name", "process_pid", "parent_process",
        "file_hash_md5", "file_hash_sha1", "file_hash_sha256",
        "username", "command_line", "iocs", "raw_payload",
        "description", "tool_target",
    )

    def __init__(self, **kwargs):
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot))
        self.event_id = self.event_id or str(uuid.uuid4())
        self.timestamp = self.timestamp or datetime.now(timezone.utc)
        self.severity = self.severity or 5
        self.confidence = self.confidence or 0.5
        self.true_positive = self.true_positive if self.true_positive is not None else True
        self.noise = self.noise if self.noise is not None else False
        self.protocol = self.protocol or "TCP"
        self.iocs = self.iocs or {}

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}

    def set_mitre(self, attack_type: str):
        m = get_mitre(attack_type)
        self.mitre_technique_id = m.get("technique_id")
        self.mitre_technique_name = m.get("technique_name")
        self.mitre_tactic = m.get("tactic")


class BaseGenerator:
    """Base class for all attack generators.

    Subclasses must implement ``generate(count: int) -> List[RawEvent]``.
    """

    attack_type: str = "benign"
    noise_probability: float = 0.0

    def __init__(self, campaign_id: str = "", seed: Optional[int] = None):
        self.campaign_id = campaign_id or str(uuid.uuid4())[:8]
        self.seed = seed or get_seed()
        self._rng = random.Random(self.seed)
        self._event_counter = 0

    def make_event(self, **overrides) -> RawEvent:
        self._event_counter += 1
        kwargs = dict(
            event_id=f"sim-{self.campaign_id}-{self.attack_type}-{self._event_counter:06d}",
            campaign_id=self.campaign_id,
            attack_type=self.attack_type,
            timestamp=datetime.now(timezone.utc),
            hostname=pick_random_hostname(),
        )
        kwargs.update(overrides)
        ev = RawEvent(**kwargs)
        ev.set_mitre(self.attack_type)
        ev.noise = self._rng.random() < self.noise_probability
        return ev

    def generate(self, count: int) -> List[RawEvent]:
        raise NotImplementedError

    def inject_noise(self, events: List[RawEvent]) -> List[RawEvent]:
        """Add duplicate and background-noise events to simulate SOC fatigue."""
        noisy = list(events)
        for ev in list(events):
            if self._rng.random() < 0.1:
                dup = RawEvent(**ev.to_dict())
                dup.event_id = ev.event_id + "-dup"
                dup.noise = True
                dup.true_positive = False
                dup.severity = max(1, dup.severity - 2)
                noisy.append(dup)
        return noisy

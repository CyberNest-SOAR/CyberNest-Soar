"""DDoS / volumetric attack simulator — SYN flood, HTTP flood, DNS amplification."""

import random
from datetime import datetime, timedelta, timezone
from typing import List

from generators.base import BaseGenerator, RawEvent
from config import pick_random_ip, pick_random_port


class DDoSSimulator(BaseGenerator):
    attack_type = "ddos"
    noise_probability = 0.02

    def generate(self, count: int) -> List[RawEvent]:
        events = []
        for _ in range(count):
            subtype = self._rng.choice(["syn_flood", "http_flood", "dns_amplification", "slowloris"])
            ts = datetime.now(timezone.utc) - timedelta(seconds=self._rng.randint(0, 7200))
            src = pick_random_ip(public=True)
            dst = pick_random_ip(public=False)
            packet_count = self._rng.randint(500, 50000)
            port_map = {"syn_flood": 80, "http_flood": 80, "dns_amplification": 53, "slowloris": 443}
            dst_port = port_map[subtype]
            ev = self.make_event(
                subtype=subtype,
                timestamp=ts,
                src_ip=src,
                dst_ip=dst,
                src_port=10000 + self._rng.randint(1, 50000),
                dst_port=dst_port,
                protocol="TCP" if subtype != "dns_amplification" else "UDP",
                description=f"{subtype.upper()} — {packet_count} packets in {self._rng.randint(10, 300)}s",
                severity=self._rng.choice([10, 12, 14]),
                confidence=self._rng.uniform(0.85, 0.99),
                true_positive=True,
                tool_target="suricata",
            )
            events.append(ev)
        return events

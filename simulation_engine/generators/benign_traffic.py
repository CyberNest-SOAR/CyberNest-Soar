"""Benign / background traffic generator — web browsing, DNS, updates, backups."""

import random
from datetime import datetime, timedelta, timezone
from typing import List

from generators.base import BaseGenerator, RawEvent
from config import pick_random_ip, pick_random_port, pick_random_domain, get_ioc_pool


class BenignTrafficGenerator(BaseGenerator):
    attack_type = "benign"
    noise_probability = 0.3

    def generate(self, count: int) -> List[RawEvent]:
        events = []
        user_agents = get_ioc_pool("user_agents")
        for _ in range(count):
            subtype = self._rng.choice(["web", "dns", "update", "backup", "email", "auth"])
            ts = datetime.now(timezone.utc) - timedelta(
                seconds=self._rng.randint(0, 86400)
            )
            src = pick_random_ip(public=False)
            dst = pick_random_ip(public=True) if subtype == "dns" else (
                pick_random_ip(public=False) if subtype in ("backup", "update") else pick_random_ip(public=True)
            )
            ev = self.make_event(
                subtype=subtype,
                timestamp=ts,
                src_ip=src,
                dst_ip=dst,
                src_port=50000 + self._rng.randint(1, 15000),
                dst_port=53 if subtype == "dns" else 443 if subtype == "web" else 80,
                protocol="UDP" if subtype == "dns" else "TCP",
                domain=pick_random_domain() if subtype in ("web", "dns") else "",
                uri=f"/{self._rng.choice(['index.html', 'login', 'api/v1/status', 'assets/main.css', 'images/logo.png'])}",
                user_agent=self._rng.choice(user_agents),
                description=f"Benign {subtype} traffic",
                severity=self._rng.randint(1, 3),
                confidence=0.99,
                true_positive=False,
                noise=self._rng.random() < 0.4,
                tool_target="zeek",
            )
            events.append(ev)
        return events

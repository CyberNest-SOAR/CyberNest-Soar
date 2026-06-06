"""Brute force / credential attack simulator — SSH, RDP, web login attempts."""

import random
from datetime import datetime, timedelta, timezone
from typing import List

from generators.base import BaseGenerator, RawEvent
from config import pick_random_ip, pick_random_port


class BruteForceSimulator(BaseGenerator):
    attack_type = "brute_force"
    noise_probability = 0.05

    def generate(self, count: int) -> List[RawEvent]:
        events = []
        for _ in range(count):
            subtype = self._rng.choice(["ssh_bf", "rdp_bf", "web_login_bf", "mysql_bf"])
            ts = datetime.now(timezone.utc) - timedelta(seconds=self._rng.randint(0, 21600))
            src = pick_random_ip(public=True)
            dst = pick_random_ip(public=False)
            port_map = {"ssh_bf": 22, "rdp_bf": 3389, "web_login_bf": 443, "mysql_bf": 3306}
            dst_port = port_map[subtype]
            usernames = ["admin", "root", "administrator", "user", "test", "oracle", "postgres"]
            passwords = ["password123", "admin", "123456", "root", "letmein", "P@ssw0rd"]
            attempts = self._rng.randint(5, 50)
            ev = self.make_event(
                subtype=subtype,
                timestamp=ts,
                src_ip=src,
                dst_ip=dst,
                src_port=40000 + self._rng.randint(1, 9999),
                dst_port=dst_port,
                protocol="TCP",
                username=self._rng.choice(usernames),
                command_line=f"ssh {self._rng.choice(usernames)}@{dst}",
                description=f"{subtype.upper()} attack — {attempts} failed attempts",
                severity=self._rng.choice([8, 10, 12]),
                confidence=self._rng.uniform(0.8, 0.98),
                true_positive=True,
                tool_target="suricata",
            )
            events.append(ev)
        return events

"""Phishing simulation — credential harvest pages, spear-phish emails, malicious attachments."""

import random
from datetime import datetime, timedelta, timezone
from typing import List

from generators.base import BaseGenerator, RawEvent
from config import pick_random_ip, pick_random_domain, pick_random_hash


class PhishingSimulator(BaseGenerator):
    attack_type = "phishing"
    noise_probability = 0.05

    def generate(self, count: int) -> List[RawEvent]:
        events = []
        domains = ["paypal-secure.fake", "bank-login.fake", "office365-verify.fake", "dropbox-auth.fake"]
        uris = ["/login", "/verify", "/account/update", "/auth/signin", "/credential-recovery"]
        for _ in range(count):
            subtype = self._rng.choice(["credential_harvest", "spear_phish", "malicious_attachment", "clone_phish"])
            ts = datetime.now(timezone.utc) - timedelta(seconds=self._rng.randint(0, 43200))
            src = pick_random_ip(public=True)
            dst = pick_random_ip(public=False)
            domain = self._rng.choice(domains)
            ev = self.make_event(
                subtype=subtype,
                timestamp=ts,
                src_ip=src,
                dst_ip=dst,
                src_port=50000 + self._rng.randint(1, 9999),
                dst_port=443,
                protocol="TCP",
                domain=domain,
                uri=self._rng.choice(uris),
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                file_hash_md5=pick_random_hash("md5"),
                file_hash_sha256=pick_random_hash("sha256"),
                username=self._rng.choice(["victim@company.com", "user@corp.local", "admin@org.com"]),
                description=f"Phishing detected — {subtype} targeting {domain}",
                severity=self._rng.choice([8, 10, 12]),
                confidence=self._rng.uniform(0.75, 0.95),
                true_positive=True,
                tool_target="suricata",
            )
            events.append(ev)
        return events

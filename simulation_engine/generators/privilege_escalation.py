"""Privilege escalation simulator — UAC bypass, token theft, sudo abuse, DLL hijack."""

import random
from datetime import datetime, timedelta, timezone
from typing import List

from generators.base import BaseGenerator, RawEvent
from config import pick_random_ip, pick_random_hostname, pick_random_hash


class PrivilegeEscalationGenerator(BaseGenerator):
    attack_type = "privilege_escalation"
    noise_probability = 0.05

    def generate(self, count: int) -> List[RawEvent]:
        events = []
        for _ in range(count):
            subtype = self._rng.choice([
                "uac_bypass", "token_theft", "sudo_abuse", "dll_hijack",
                "setuid_exploit", "scheduled_task",
            ])
            ts = datetime.now(timezone.utc) - timedelta(seconds=self._rng.randint(0, 7200))
            host = pick_random_hostname()
            ev = self.make_event(
                subtype=subtype,
                timestamp=ts,
                src_ip=pick_random_ip(public=False),
                dst_ip=pick_random_ip(public=False),
                hostname=host,
                process_name=self._rng.choice([
                    "cmd.exe", "powershell.exe", "bash", "/usr/bin/sudo",
                    "rundll32.exe", "schtasks.exe",
                ]),
                parent_process=self._rng.choice(["explorer.exe", "services.exe", "init"]),
                username=self._rng.choice(["NT AUTHORITY\\SYSTEM", "root", "admin"]),
                command_line=self._rng.choice([
                    "reg add HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                    "sudo -u root /bin/bash -c 'echo exploit'",
                    "schtasks /create /tn Updater /tr calc.exe /sc daily",
                    "rundll32.exe javascript:\\\"\\..\\mshtml,RunHTMLApplication",
                ]),
                file_hash_md5=pick_random_hash("md5"),
                file_hash_sha256=pick_random_hash("sha256"),
                description=f"Privilege escalation detected — {subtype} on {host}",
                severity=self._rng.choice([10, 12, 14]),
                confidence=self._rng.uniform(0.75, 0.95),
                true_positive=True,
                tool_target="wazuh",
            )
            events.append(ev)
        return events

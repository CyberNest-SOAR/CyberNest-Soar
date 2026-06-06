"""Lateral movement simulator — SMB/WMI/PsExec/RDP-based movement between hosts."""

import random
from datetime import datetime, timedelta, timezone
from typing import List

from generators.base import BaseGenerator, RawEvent
from config import pick_random_ip, pick_random_port, pick_random_hostname


class LateralMovementGenerator(BaseGenerator):
    attack_type = "lateral_movement"
    noise_probability = 0.05

    def generate(self, count: int) -> List[RawEvent]:
        events = []
        for _ in range(count):
            subtype = self._rng.choice(["smb_wmi", "psexec", "rdp_movement", "ssh_movement", "winrm"])
            ts = datetime.now(timezone.utc) - timedelta(seconds=self._rng.randint(0, 14400))
            src = pick_random_ip(public=False)
            dst = pick_random_ip(public=False)
            port_map = {"smb_wmi": 445, "psexec": 445, "rdp_movement": 3389, "ssh_movement": 22, "winrm": 5985}
            dst_port = port_map[subtype]
            src_host = pick_random_hostname()
            dst_host = pick_random_hostname()
            ev = self.make_event(
                subtype=subtype,
                timestamp=ts,
                src_ip=src,
                dst_ip=dst,
                src_port=50000 + self._rng.randint(1, 9999),
                dst_port=dst_port,
                protocol="TCP",
                hostname=src_host,
                process_name=self._rng.choice(["wmiprvse.exe", "PsExec.exe", "svchost.exe", "ssh.exe"]),
                parent_process="services.exe",
                username=f"svc_{self._rng.choice(['backup', 'deploy', 'monitor', 'sql'])}",
                command_line=f"wmic /node:{dst} process call create cmd.exe",
                description=f"Lateral movement via {subtype} from {src_host} to {dst_host}",
                severity=self._rng.choice([10, 12]),
                confidence=self._rng.uniform(0.7, 0.9),
                true_positive=True,
                tool_target="wazuh",
            )
            events.append(ev)
        return events

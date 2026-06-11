import logging
import random
from datetime import time, timezone, timedelta
from typing import List, Optional

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)

_MAINTENANCE_WINDOWS = [
    (time(1, 0), time(5, 0)),   # 1-5 AM daily
    (time(22, 0), time(23, 59)), # 10 PM - midnight
]
_PATCH_TUESDAYS = {2, 3, 4}  # Tue-Thu

_DEPARTMENTS = {
    "10.0.0.": ("Engineering", "R&D"),
    "10.0.1.": ("Finance", "Accounting"),
    "10.0.2.": ("HR", "PeopleOps"),
    "10.0.3.": ("Legal", "Legal"),
    "10.0.4.": ("Marketing", "Growth"),
    "10.0.5.": ("IT", "Infrastructure"),
    "10.0.6.": ("Security", "SOC"),
    "10.0.7.": ("Sales", "Revenue"),
    "10.0.8.": ("Executives", "Leadership"),
    "10.0.9.": ("DevOps", "Engineering"),
    "172.16.0.": ("IT", "Infrastructure"),
    "172.16.1.": ("Security", "SOC"),
    "172.16.2.": ("Lab", "R&D"),
    "192.168.1.": ("Engineering", "R&D"),
    "192.168.50.": ("Sales", "Revenue"),
    "default": ("General", "Operations"),
}

_ENVIRONMENT_CONTEXTS = [
    "Scheduled maintenance window — change control CAB-2024-0892",
    "Patch Tuesday deployment — approved change window",
    "Annual security assessment — authorized penetration test",
    "Datacenter migration in progress — increased network activity expected",
    "Cloud provider changeover — temporary increase in authentication errors",
    "Quarterly disaster recovery exercise",
    "Merger/acquisition integration — new domains and IPs being onboarded",
    "New office deployment — increased VPN connections",
    "Scheduled vulnerability scan — Qualys agent active",
    "Security tool deployment — EDR rollout to 500 endpoints",
    "No known environmental factors",
    "Standard business operations",
]


def add_environmental_context(alerts: List[UnifiedAlert],
                              seed: Optional[int] = None) -> List[UnifiedAlert]:
    rng = random.Random(seed)
    for alert in alerts:
        ts = alert.timestamp
        hour = ts.hour
        minute = ts.minute
        weekday = ts.weekday()  # 0=Monday
        is_weekend = weekday >= 5
        is_business_hours = 8 <= hour < 18 and not is_weekend

        alert.weekend_activity = is_weekend
        alert.business_hours = is_business_hours

        # Maintenance windows (1-5 AM daily, or 10 PM-midnight)
        alert.maintenance_window = any(
            start <= time(hour, minute) <= end
            for start, end in _MAINTENANCE_WINDOWS
        )

        # Patch windows (Tuesday-Thursday overnight)
        alert.patch_window = (
            weekday in _PATCH_TUESDAYS
            and 1 <= hour <= 4
        )

        # Known admin activity — more likely during maintenance windows
        if alert.maintenance_window:
            alert.known_admin_activity = rng.random() < 0.85
        elif not is_business_hours and not is_weekend:
            alert.known_admin_activity = rng.random() < 0.30
        else:
            alert.known_admin_activity = rng.random() < 0.10

        # Vulnerability scans — simulate Qualys/Nessus scan bursts
        alert.vulnerability_scan = (
            rng.random() < 0.08 and
            is_business_hours and
            hour not in (12, 13)  # not during lunch
        )

        # Scheduled backups — typically overnight
        alert.scheduled_backup = (
            22 <= hour or hour <= 3
        ) and rng.random() < 0.25

        # Environment context string
        if alert.maintenance_window and alert.known_admin_activity:
            alert.environment_context = rng.choice([
                "Scheduled maintenance window — change control CAB-2024-0892",
                "Planned infrastructure update — authorized work",
                "Approved after-hours maintenance activity",
            ])
        elif alert.patch_window:
            alert.environment_context = "Patch Tuesday deployment — approved change window"
        elif alert.vulnerability_scan:
            alert.environment_context = rng.choice([
                "Scheduled vulnerability scan — Qualys agent active",
                "Annual security assessment — authorized penetration test",
                "Quarterly compliance scan in progress",
            ])
        else:
            alert.environment_context = rng.choice(_ENVIRONMENT_CONTEXTS)

    return alerts

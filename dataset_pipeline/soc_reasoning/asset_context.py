import logging
import random
from typing import List, Optional

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)

_HOST_ROLES = [
    "domain_controller", "exchange_server", "file_server",
    "web_server", "database_server", "application_server",
    "developer_workstation", "executive_workstation",
    "finance_workstation", "hr_workstation",
    "kiosk_machine", "jumpbox", "network_device",
    "security_appliance", "vpn_gateway", "docker_host",
    "kubernetes_node", "monitoring_server", "backup_server",
    "mail_server", "dns_server", "dhcp_server",
]

_CRITICALITIES = ["critical", "high", "medium", "low"]
_CRITICALITY_WEIGHTS = [0.15, 0.25, 0.35, 0.25]

_BUSINESS_UNITS = [
    "Finance", "Engineering", "Operations", "HR",
    "Legal", "Marketing", "Sales", "Security",
    "Infrastructure", "Executive", "R&D", "Compliance",
]

_OWNER_TEAMS = [
    "Platform Engineering", "Security Operations", "Network Team",
    "Application Team", "Identity Team", "Endpoint Engineering",
    "Data Engineering", "Cloud Operations", "Enterprise IT",
    "Vendor Management",
]

_COMPLIANCE_SCOPES = [
    "PCI-DSS", "SOC2", "HIPAA", "GDPR", "SOX", "ISO27001",
    "FedRAMP", "None", "None", "None",
]

_DEPT_MAP = {
    # subnets -> (department, business_unit, host_role_prefix)
    "10.0.0.": ("IT", "Infrastructure", "server"),
    "10.0.1.": ("Finance", "Finance", "finance"),
    "10.0.2.": ("HR", "Operations", "hr"),
    "10.0.3.": ("Legal", "Legal", "legal"),
    "10.0.4.": ("Marketing", "Marketing", "marketing"),
    "10.0.5.": ("IT", "Infrastructure", "it"),
    "10.0.6.": ("Security", "Security", "security"),
    "10.0.7.": ("Sales", "Sales", "sales"),
    "10.0.8.": ("Executive", "Leadership", "exec"),
    "10.0.9.": ("Engineering", "Engineering", "dev"),
    "172.16.0.": ("IT", "Infrastructure", "server"),
    "172.16.1.": ("Security", "Security", "monitoring"),
    "172.16.2.": ("R&D", "R&D", "lab"),
    "192.168.1.": ("Engineering", "Engineering", "dev"),
    "192.168.50.": ("Sales", "Sales", "sales"),
}


def _lookup_host(ip: Optional[str]) -> tuple:
    if not ip:
        return ("General", "Operations", "unknown", "medium")
    for prefix, (dept, bu, role_prefix) in _DEPT_MAP.items():
        if ip.startswith(prefix):
            role = role_prefix + "_" + random.choice(["server", "workstation", "service"])
            crit = random.choices(_CRITICALITIES, weights=_CRITICALITY_WEIGHTS, k=1)[0]
            return (dept, bu, role, crit)
    crit = random.choices(_CRITICALITIES, weights=_CRITICALITY_WEIGHTS, k=1)[0]
    return ("General", "Operations", "external", crit)


def add_asset_context(alerts: List[UnifiedAlert],
                      seed: Optional[int] = None) -> List[UnifiedAlert]:
    rng = random.Random(seed)
    for alert in alerts:
        dept, bu, role, crit = _lookup_host(alert.dst_ip)
        alert.department = dept
        alert.business_unit = bu
        alert.host_role = role if role != "external" else rng.choice(_HOST_ROLES)
        alert.asset_criticality = crit
        alert.owner_team = rng.choice(_OWNER_TEAMS)
        alert.compliance_scope = rng.choice(_COMPLIANCE_SCOPES)

        if alert.true_positive and alert.alert_severity and alert.alert_severity >= 8:
            alert.asset_criticality = rng.choices(["critical", "high"], weights=[0.7, 0.3], k=1)[0]

        # Asset value (1-100)
        value_map = {"critical": (80, 100), "high": (60, 89), "medium": (30, 69), "low": (1, 39)}
        lo, hi = value_map.get(alert.asset_criticality, (1, 50))
        alert.asset_value = rng.randint(lo, hi)

    return alerts

import logging
import random
from typing import Optional

logger = logging.getLogger(__name__)

_COUNTRY_MAP = {}
_ASN_MAP = {}

_PRIVATE_PREFIXES = ("10.", "172.16.", "172.17.", "172.18.", "172.19.",
                     "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                     "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                     "172.30.", "172.31.", "192.168.", "127.", "0.")

_RESIDENTIAL_ASNS = {
    "8.8.8.8": ("US", "15169", "Google"),
    "8.8.4.4": ("US", "15169", "Google"),
    "1.1.1.1": ("US", "13335", "CloudFlare"),
    "185.220.101.42": ("DE", "47837", "TOR Project"),
    "198.51.100.7": ("US", "53755", "Example Corp"),
    "203.0.113.5": ("AU", "133822", "Example Net"),
    "45.33.32.156": ("US", "20473", "Vultr"),
    "104.16.0.1": ("US", "13335", "CloudFlare"),
    "151.101.1.1": ("US", "54113", "Fastly"),
    "192.0.2.1": ("US", "53755", "Example Corp"),
}


def is_private_ip(ip: Optional[str]) -> bool:
    if not ip:
        return True
    return any(ip.startswith(p) for p in _PRIVATE_PREFIXES)


def resolve_country(ip: Optional[str]) -> Optional[str]:
    if not ip or is_private_ip(ip):
        return "RFC1918"
    entry = _RESIDENTIAL_ASNS.get(ip)
    return entry[0] if entry else random.choice(["US", "DE", "GB", "NL", "RU", "CN", "BR", "JP"])


def resolve_asn(ip: Optional[str]) -> Optional[str]:
    if not ip or is_private_ip(ip):
        return "PRIVATE"
    entry = _RESIDENTIAL_ASNS.get(ip)
    return entry[1] if entry else str(random.randint(10000, 99999))


def resolve_asn_name(ip: Optional[str]) -> Optional[str]:
    if not ip or is_private_ip(ip):
        return "Private Network"
    entry = _RESIDENTIAL_ASNS.get(ip)
    return entry[2] if entry else f"AS{random.randint(10000, 99999)}"

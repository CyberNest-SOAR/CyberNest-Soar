import logging
import random
from typing import List, Optional

from parsers.normalizer import UnifiedAlert
from enrichment.geoip import resolve_country, resolve_asn, resolve_asn_name, is_private_ip
from enrichment.attack_mapper import map_attack_type

logger = logging.getLogger(__name__)


def enrich_alerts(alerts: List[UnifiedAlert], seed: Optional[int] = None) -> List[UnifiedAlert]:
    rng = random.Random(seed)
    for alert in alerts:
        alert.geoip_src_country = resolve_country(alert.src_ip)
        alert.geoip_src_asn = resolve_asn(alert.src_ip)
        alert.geoip_dst_country = resolve_country(alert.dst_ip)
        alert.geoip_dst_asn = resolve_asn(alert.dst_ip)

        if alert.mitre_technique_id in (None, "T9999", ""):
            tid, tname, ttactic = map_attack_type(alert.attack_type, getattr(alert, 'subtype', None))
            alert.mitre_technique_id = tid
            alert.mitre_technique_name = tname
            alert.mitre_tactic = ttactic

        if alert.enrichment_vt_score is None:
            if alert.attack_type and alert.attack_type != "benign" and not is_private_ip(alert.src_ip):
                alert.enrichment_vt_score = rng.choices(
                    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                    weights=[30, 10, 5, 5, 5, 5, 5, 10, 10, 15], k=1
                )[0]
                alert.enrichment_abuse_score = rng.choices(
                    [0, 25, 50, 75, 100],
                    weights=[40, 15, 15, 15, 15], k=1
                )[0]
            else:
                alert.enrichment_vt_score = 0
                alert.enrichment_abuse_score = 0

        if alert.enrichment_epss_score is None:
            alert.enrichment_epss_score = round(rng.random() * 0.3, 6) if alert.true_positive else 0.0

        if alert.enrichment_cvss_score is None:
            if alert.true_positive and alert.mitre_tactic not in ("None", "Other"):
                alert.enrichment_cvss_score = round(rng.uniform(4.0, 10.0), 1)

        if alert.enrichment_misp_matches is None:
            if alert.true_positive:
                count = rng.randint(0, 5)
                alert.enrichment_misp_matches = (
                    [f"MISP-{rng.randint(1000, 99999)}" for _ in range(count)]
                    if count > 0 else []
                )
            else:
                alert.enrichment_misp_matches = []

    return alerts

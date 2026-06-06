import logging
import uuid
import random
from datetime import timedelta, timezone
from typing import Dict, List, Optional

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)


def cluster_alerts(alerts: List[UnifiedAlert],
                   time_window_minutes: int = 60,
                   ip_cluster_distance: int = 5,
                   seed: Optional[int] = None) -> List[UnifiedAlert]:
    rng = random.Random(seed)
    clusters: Dict[str, str] = {}
    campaigns: Dict[str, str] = {}

    # Attack-type based clustering
    attack_groups: Dict[str, List[UnifiedAlert]] = {}
    for alert in alerts:
        atk = alert.attack_type or "unknown"
        attack_groups.setdefault(atk, []).append(alert)

    # Create clusters per attack type
    for atk, group in attack_groups.items():
        if not group:
            continue
        group.sort(key=lambda a: a.timestamp)
        cluster_id = None
        campaign_id = None
        last_ts = None

        for i, alert in enumerate(group):
            if cluster_id is None or (
                last_ts and (alert.timestamp - last_ts) > timedelta(minutes=time_window_minutes)
            ):
                cluster_id = f"cl-{uuid.uuid4().hex[:8]}"
                campaign_id = f"cmp-{uuid.uuid4().hex[:8]}"

            alert.cluster_id = cluster_id
            alert.campaign_id = campaign_id
            last_ts = alert.timestamp

    # IP-based cross-type correlation
    ip_events: Dict[str, List[UnifiedAlert]] = {}
    for alert in alerts:
        for ip in [alert.src_ip, alert.dst_ip]:
            if ip:
                ip_events.setdefault(ip, []).append(alert)

    # Merge clusters that share IPs within time proximity
    for ip, events in ip_events.items():
        if len(events) < ip_cluster_distance:
            continue
        cluster_ids = set(e.cluster_id for e in events if e.cluster_id)
        if len(cluster_ids) < 2:
            continue
        # Merge: assign the most common campaign_id to all
        from collections import Counter
        campaign_counts = Counter(e.campaign_id for e in events if e.campaign_id)
        if campaign_counts:
            dominant_campaign = campaign_counts.most_common(1)[0][0]
            master_cluster = f"cl-merged-{uuid.uuid4().hex[:8]}"
            for e in events:
                e.cluster_id = master_cluster
                e.campaign_id = dominant_campaign

    # Simulate alert fatigue: mark 5% of clusters as noisy
    seen_clusters = set(a.cluster_id for a in alerts if a.cluster_id)
    noisy_clusters = set(rng.sample(list(seen_clusters), max(1, int(len(seen_clusters) * 0.05))))
    for alert in alerts:
        if alert.cluster_id in noisy_clusters:
            alert.noise = True
            alert.true_positive = False
            alert.analyst_verdict = "false_positive"

    return alerts

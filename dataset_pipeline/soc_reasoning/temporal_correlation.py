import logging
import random
import uuid
from collections import deque
from datetime import timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)


@dataclass
class _SlidingWindow:
    """Fast per-attack-type sliding window counter for last N seconds."""
    window_seconds: float
    entries: deque = None

    def __post_init__(self):
        self.entries = deque()

    def add(self, timestamp, attack_type: str) -> int:
        cutoff = timestamp - timedelta(seconds=self.window_seconds)
        # Trim expired from left
        while self.entries and self.entries[0][0] < cutoff:
            self.entries.popleft()
        self.entries.append((timestamp, attack_type))
        # Count matching type
        return sum(1 for _, t in self.entries if t == attack_type)


def add_temporal_correlation(alerts: List[UnifiedAlert],
                             seed: Optional[int] = None) -> List[UnifiedAlert]:
    if not alerts:
        return alerts
    rng = random.Random(seed)
    sorted_alerts = sorted(alerts, key=lambda a: a.timestamp)

    # O(1) session lookups: src:dst -> latest session_id
    session_map: Dict[Tuple[str, str], str] = {}
    burst_counters: Dict[str, int] = {}
    active_storms: Dict[str, int] = {}
    storm_count = 0

    # Sliding window for last-hour similarity (O(n) total)
    hour_window = _SlidingWindow(3600.0)
    # 5-minute window for storm detection
    storm_window = _SlidingWindow(300.0)

    total = len(sorted_alerts)

    for i, alert in enumerate(sorted_alerts):
        pct = i / total if total > 1 else 0
        if pct < 0.2:
            alert.timeline_position = "early"
        elif pct < 0.5:
            alert.timeline_position = "mid"
        elif pct < 0.8:
            alert.timeline_position = "late"
        else:
            alert.timeline_position = "end"

        # Previous / next alert IDs
        if i > 0:
            alert.previous_alert_id = sorted_alerts[i - 1].event_id
        if i < total - 1:
            alert.next_alert_id = sorted_alerts[i + 1].event_id

        # O(1) session tracking
        sess_key = (alert.src_ip or "?", alert.dst_ip or "?")
        if sess_key in session_map and rng.random() < 0.7:
            alert.session_id = session_map[sess_key]
        else:
            alert.session_id = f"sess-{uuid.uuid4().hex[:8]}"
            session_map[sess_key] = alert.session_id

        # O(n) sliding window for similar alerts in last hour
        alert.similar_alerts_last_hour = hour_window.add(alert.timestamp, alert.attack_type or "")

        # Repeated behavior score
        sig_key = alert.alert_signature or alert.attack_type or "unknown"
        burst_counters[sig_key] = burst_counters.get(sig_key, 0) + 1
        alert.repeated_behavior_score = min(10, burst_counters[sig_key])

        # Attack bursts — rapid succession of same signature
        if alert.repeated_behavior_score >= 5 and alert.similar_alerts_last_hour >= 3:
            alert.attack_burst_id = f"burst-{sig_key}-{uuid.uuid4().hex[:6]}"
        elif alert.repeated_behavior_score >= 3:
            alert.attack_burst_id = f"miniburst-{sig_key}-{uuid.uuid4().hex[:6]}"

        # Alert storms via 5-min sliding window
        storm_similar = storm_window.add(alert.timestamp, sig_key)
        raw_count = burst_counters.get(sig_key, 0)
        if storm_similar >= 10 and raw_count >= 15:
            storm_key = f"storm-{sig_key}"
            if storm_key not in active_storms:
                storm_count += 1
                storm_id = f"storm-{storm_count:04d}"
                active_storms[storm_key] = storm_count
            else:
                storm_id = f"storm-{active_storms[storm_key]:04d}"
            alert.alert_storm_id = storm_id

    # Noise injection: 5% timeline gaps
    for alert in sorted_alerts:
        if rng.random() < 0.05:
            alert.extra_fields["timeline_gap"] = True
            alert.extra_fields["missing_previous"] = rng.random() < 0.5

    return sorted_alerts

import json
import os
import time
from typing import Any, Dict, List

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


EVE_LOG_PATH = os.getenv(
    "SURICATA_EVE_LOG_PATH",
    "/var/log/suricata/eve.json",
)

WAZUH_INDEXER_URL = os.getenv("WAZUH_INDEXER_URL", "https://localhost:9200")
WAZUH_INDEXER_USER = os.getenv("WAZUH_INDEXER_USER", "admin")
WAZUH_INDEXER_PASSWORD = os.getenv("WAZUH_INDEXER_PASSWORD", "SecretPassword")

SENSOR_EVENTS_INDEX = os.getenv(
    "SURICATA_EVENTS_INDEX", "cybernest-suricata-events"
)
ACTION_RULE_GROUP = os.getenv("SURICATA_ACTION_RULE_GROUP", "suricata-response")


class WazuhIndexerAPI:
    def __init__(
        self,
        url: str = WAZUH_INDEXER_URL,
        username: str = WAZUH_INDEXER_USER,
        password: str = WAZUH_INDEXER_PASSWORD,
    ) -> None:
        self.url = url.rstrip("/")
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {"Content-Type": "application/json"}

    def index_event(self, index: str, body: Dict[str, Any]) -> None:
        endpoint = f"{self.url}/{index}/_doc"
        resp = requests.post(
            endpoint,
            auth=self.auth,
            headers=self.headers,
            json=body,
            verify=False,
        )
        resp.raise_for_status()

    def search_actions_for_sensor(
        self,
        sensor_id: str,
        since_epoch_ms: int,
        size: int = 10,
    ) -> List[Dict[str, Any]]:
        search_url = f"{self.url}/wazuh-alerts-*/_search"
        body = {
            "size": size,
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "timestamp": {
                                    "gte": since_epoch_ms,
                                    "format": "epoch_millis",
                                }
                            }
                        },
                        {
                            "term": {
                                "rule.groups": ACTION_RULE_GROUP,
                            }
                        },
                        {
                            "term": {
                                "data.sensor.id": sensor_id,
                            }
                        },
                    ]
                }
            },
        }
        resp = requests.post(
            search_url,
            auth=self.auth,
            headers=self.headers,
            json=body,
            verify=False,
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", {}).get("hits", [])
        return [h.get("_source", {}) for h in hits]


def read_eve_events(log_path: str) -> List[Dict[str, Any]]:
    """Read Suricata eve.json logs (one JSON per line)."""
    events: List[Dict[str, Any]] = []
    if not os.path.exists(log_path):
        return events

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def normalize_suricata_event(ev: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Suricata event into generic sensor event."""
    sensor_event: Dict[str, Any] = {
        "sensor_type": "suricata",
        "sensor_id": ev.get("in_iface", "suricata1"),
        "timestamp": ev.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ")),
        "event_type": ev.get("event_type"),
        "src_ip": ev.get("src_ip"),
        "src_port": ev.get("src_port"),
        "dest_ip": ev.get("dest_ip"),
        "dest_port": ev.get("dest_port"),
        "proto": ev.get("proto"),
        "raw": ev,
    }
    return sensor_event


def push_suricata_events_to_wazuh_indexer(
    indexer: WazuhIndexerAPI,
    log_path: str = EVE_LOG_PATH,
) -> List[Dict[str, Any]]:
    events = read_eve_events(log_path)

    normalized_events: List[Dict[str, Any]] = []
    for ev in events:
        doc = normalize_suricata_event(ev)
        indexer.index_event(SENSOR_EVENTS_INDEX, doc)
        normalized_events.append(doc)

    return normalized_events


def fetch_and_handle_actions(
    indexer: WazuhIndexerAPI,
    sensor_id: str,
    since_epoch_ms: int,
) -> None:
    actions = indexer.search_actions_for_sensor(
        sensor_id=sensor_id,
        since_epoch_ms=since_epoch_ms,
    )
    for action in actions:
        # For now we only print the intended action.
        # Extend this to, for example, update Suricata rules,
        # change BPF filters, or notify orchestrators.
        print("[SURICATA][ACTION]", json.dumps(action, indent=2))


def main() -> None:
    indexer = WazuhIndexerAPI()

    pushed_events = push_suricata_events_to_wazuh_indexer(
        indexer=indexer,
        log_path=EVE_LOG_PATH,
    )
    print(f"Pushed {len(pushed_events)} Suricata events to index '{SENSOR_EVENTS_INDEX}'")

    sensor_id = os.getenv("SURICATA_SENSOR_ID", "suricata1")
    since_ms = int(time.time() * 1000) - int(
        os.getenv("SURICATA_ACTION_LOOKBACK_MS", "300000")
    )

    fetch_and_handle_actions(indexer=indexer, sensor_id=sensor_id, since_epoch_ms=since_ms)


if __name__ == "__main__":
    main()


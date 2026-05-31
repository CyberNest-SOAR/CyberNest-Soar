import json
import os
import time
from typing import Any, Dict, List, Optional

import requests
import urllib3
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# === Environment / configuration ===
ARKIME_URL = os.getenv("ARKIME_URL", "http://localhost:8005")
ARKIME_USER = os.getenv("ARKIME_USER", "admin")
ARKIME_PASS = os.getenv("ARKIME_PASS", "admin")

WAZUH_API_URL = os.getenv("WAZUH_API_URL", "https://localhost:55000")
WAZUH_API_USER = os.getenv("WAZUH_API_USER", "wazuh-wui")
WAZUH_API_PASSWORD = os.getenv("WAZUH_API_PASSWORD", "MyS3cr37P450r.*-")

WAZUH_INDEXER_URL = os.getenv("WAZUH_INDEXER_URL", "https://localhost:9200")
WAZUH_INDEXER_USER = os.getenv("WAZUH_INDEXER_USER", "admin")
WAZUH_INDEXER_PASSWORD = os.getenv("WAZUH_INDEXER_PASSWORD", "SecretPassword")

# Index where we will push raw Arkime events for correlation/visibility
SENSOR_EVENTS_INDEX = os.getenv(
    "ARKIME_EVENTS_INDEX", "cybernest-arkime-events"
)

# Rule / query selector for "action" alerts in Wazuh
ACTION_RULE_GROUP = os.getenv("ARKIME_ACTION_RULE_GROUP", "arkime-response")


def make_session() -> requests.Session:
    """Create a requests session with retries."""
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


class WazuhAPI:
    """Small wrapper around Wazuh REST API for authentication."""

    def __init__(
        self,
        url: str = WAZUH_API_URL,
        username: str = WAZUH_API_USER,
        password: str = WAZUH_API_PASSWORD,
    ) -> None:
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.headers: Dict[str, str] = {"Content-Type": "application/json"}
        self.token: Optional[str] = None
        self._get_token()

    def _get_token(self) -> None:
        token_url = f"{self.url}/security/user/authenticate"
        resp = requests.post(
            token_url,
            auth=HTTPBasicAuth(self.username, self.password),
            headers=self.headers,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["data"]["token"]
        self.headers["Authorization"] = f"Bearer {self.token}"


class WazuhIndexerAPI:
    """Thin client for querying and indexing into Wazuh Indexer (OpenSearch)."""

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
        """Fetch 'action' alerts from Wazuh for this sensor.

        This assumes you have Wazuh rules that add something like:
          - rule.groups contains ACTION_RULE_GROUP (e.g. 'arkime-response')
          - data.sensor.id == sensor_id (or similar)

        Adjust the query to match your actual mapping.
        """
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


def get_arkime_sessions(last_seconds: int = 300) -> Dict[str, Any]:
    """Fetch Arkime sessions in the last N seconds."""
    now = int(time.time())
    start = now - last_seconds
    resp = requests.get(
        f"{ARKIME_URL}/api/sessions.json",
        params={"startTime": start, "endTime": now},
        auth=(ARKIME_USER, ARKIME_PASS),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def normalize_arkime_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Arkime session into a generic event document."""
    return {
        "sensor_type": "arkime",
        "sensor_id": raw_event.get("id", "unknown"),
        "timestamp": raw_event.get("fp", int(time.time())),
        "raw": raw_event,
    }


def push_arkime_events_to_wazuh_indexer(
    indexer: WazuhIndexerAPI,
    last_seconds: int = 300,
) -> List[Dict[str, Any]]:
    sessions = get_arkime_sessions(last_seconds=last_seconds)
    events = sessions.get("data", []) or sessions.get("sessions", [])

    normalized_events: List[Dict[str, Any]] = []
    for ev in events:
        doc = normalize_arkime_event(ev)
        indexer.index_event(SENSOR_EVENTS_INDEX, doc)
        normalized_events.append(doc)

    return normalized_events


def fetch_and_handle_actions(
    indexer: WazuhIndexerAPI,
    sensor_id: str,
    since_epoch_ms: int,
) -> None:
    """Poll Wazuh Indexer for action alerts targeting this Arkime sensor."""
    actions = indexer.search_actions_for_sensor(
        sensor_id=sensor_id,
        since_epoch_ms=since_epoch_ms,
    )
    for action in actions:
        # At this stage we only print the intended action.
        # Extend this to call Arkime APIs for session tagging,
        # export, PCAP download, etc.
        print("[ARKIME][ACTION]", json.dumps(action, indent=2))


def main() -> None:
    indexer = WazuhIndexerAPI()

    # 1) Push latest Arkime events into a dedicated index
    pushed_events = push_arkime_events_to_wazuh_indexer(
        indexer=indexer,
        last_seconds=int(os.getenv("ARKIME_PULL_WINDOW", "300")),
    )
    print(f"Pushed {len(pushed_events)} Arkime events to index '{SENSOR_EVENTS_INDEX}'")

    # 2) Poll for actions from Wazuh that target this Arkime sensor
    # Here we simply use a generic sensor_id; adapt as needed
    sensor_id = os.getenv("ARKIME_SENSOR_ID", "arkime-main")
    since_ms = int(time.time() * 1000) - int(
        os.getenv("ARKIME_ACTION_LOOKBACK_MS", "300000")
    )

    fetch_and_handle_actions(indexer=indexer, sensor_id=sensor_id, since_epoch_ms=since_ms)


if __name__ == "__main__":
    main()

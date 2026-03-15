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
VELO_URL = os.getenv("VELO_URL", "https://localhost:8000")
VELO_USERNAME = os.getenv("VELO_USERNAME", "admin")
VELO_PASSWORD = os.getenv("VELO_PASSWORD", "admin")

WAZUH_API_URL = os.getenv("WAZUH_API_URL", "https://localhost:55000")
WAZUH_API_USER = os.getenv("WAZUH_API_USER", "wazuh-wui")
WAZUH_API_PASSWORD = os.getenv("WAZUH_API_PASSWORD", "MyS3cr37P450r.*-")

WAZUH_INDEXER_URL = os.getenv("WAZUH_INDEXER_URL", "https://localhost:9200")
WAZUH_INDEXER_USER = os.getenv("WAZUH_INDEXER_USER", "admin")
WAZUH_INDEXER_PASSWORD = os.getenv("WAZUH_INDEXER_PASSWORD", "SecretPassword")

SENSOR_EVENTS_INDEX = os.getenv(
    "VELO_EVENTS_INDEX", "cybernest-velociraptor-events"
)

ACTION_RULE_GROUP = os.getenv("VELO_ACTION_RULE_GROUP", "velociraptor-response")


def make_session() -> requests.Session:
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


def velo_login(session: requests.Session) -> None:
    resp = session.post(
        f"{VELO_URL}/api/v1/login",
        json={"username": VELO_USERNAME, "password": VELO_PASSWORD},
        verify=False,
        timeout=10,
    )
    resp.raise_for_status()
    token = resp.json().get("token")
    if not token:
        raise RuntimeError("Velociraptor login succeeded but token missing.")
    session.headers.update({"Authorization": f"Bearer {token}"})


def get_velo_clients(session: requests.Session) -> Dict[str, Any]:
    resp = session.get(
        f"{VELO_URL}/api/v1/clients",
        verify=False,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def normalize_velo_client(client: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sensor_type": "velociraptor",
        "sensor_id": client.get("id", "unknown"),
        "timestamp": int(time.time()),
        "raw": client,
    }


def push_velo_events_to_wazuh_indexer(
    indexer: WazuhIndexerAPI,
    session: requests.Session,
) -> List[Dict[str, Any]]:
    clients = get_velo_clients(session)
    items = clients.get("items", [])

    normalized_events: List[Dict[str, Any]] = []
    for client in items:
        doc = normalize_velo_client(client)
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
        # At this stage we only print the intended action.
        # Extend this to call Velociraptor APIs for collection,
        # live response, process killing, etc.
        print("[VELO][ACTION]", json.dumps(action, indent=2))


def main() -> None:
    session = make_session()
    velo_login(session)

    indexer = WazuhIndexerAPI()

    pushed_events = push_velo_events_to_wazuh_indexer(indexer=indexer, session=session)
    print(f"Pushed {len(pushed_events)} Velociraptor events to index '{SENSOR_EVENTS_INDEX}'")

    sensor_id = os.getenv("VELO_SENSOR_ID", "velociraptor-main")
    since_ms = int(time.time() * 1000) - int(
        os.getenv("VELO_ACTION_LOOKBACK_MS", "300000")
    )

    fetch_and_handle_actions(indexer=indexer, sensor_id=sensor_id, since_epoch_ms=since_ms)


if __name__ == "__main__":
    main()

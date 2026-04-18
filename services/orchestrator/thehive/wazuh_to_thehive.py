import json
import os
import time
from typing import Any, Dict, List, Optional

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ===== Configuration (override via environment variables) =====

# Wazuh Indexer (OpenSearch) where wazuh-alerts-* indices live
WAZUH_INDEXER_URL = os.getenv("WAZUH_INDEXER_URL", "https://localhost:9200")
WAZUH_INDEXER_USER = os.getenv("WAZUH_INDEXER_USER", "admin")
WAZUH_INDEXER_PASSWORD = os.getenv("WAZUH_INDEXER_PASSWORD", "SecretPassword")

# TheHive URL and API key
THEHIVE_URL = os.getenv("THEHIVE_URL", "http://localhost:9000")
THEHIVE_API_KEY = os.getenv("THEHIVE_API_KEY", "changeme")

# How far back to look for Wazuh alerts (in seconds)
LOOKBACK_SECONDS = int(os.getenv("WAZUH_TO_THEHIVE_LOOKBACK_SECONDS", "300"))

# Optional filter by rule group (e.g. only send alerts that are part of a group)
FILTER_RULE_GROUP: Optional[str] = os.getenv("WAZUH_TO_THEHIVE_RULE_GROUP") or None

# Maximum number of alerts to pull in a single run
MAX_ALERTS = int(os.getenv("WAZUH_TO_THEHIVE_MAX_ALERTS", "50"))


class WazuhIndexerAPI:
    """Thin client to search Wazuh alerts via the indexer API."""

    def __init__(
        self,
        url: str = WAZUH_INDEXER_URL,
        username: str = WAZUH_INDEXER_USER,
        password: str = WAZUH_INDEXER_PASSWORD,
    ) -> None:
        self.url = url.rstrip("/")
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {"Content-Type": "application/json"}

    def search_alerts(
        self,
        since_epoch_ms: int,
        size: int = MAX_ALERTS,
        rule_group: Optional[str] = FILTER_RULE_GROUP,
    ) -> List[Dict[str, Any]]:
        """Search wazuh-alerts-* index for recent alerts."""
        search_url = f"{self.url}/wazuh-alerts-*/_search"

        must_clauses: List[Dict[str, Any]] = [
            {
                "range": {
                    "timestamp": {
                        "gte": since_epoch_ms,
                        "format": "epoch_millis",
                    }
                }
            }
        ]

        if rule_group:
            must_clauses.append({"term": {"rule.groups": rule_group}})

        body = {
            "size": size,
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {"bool": {"must": must_clauses}},
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


class TheHiveClient:
    """Simple client for TheHive v4/v5 `POST /api/v1/alert`."""

    def __init__(self, url: str = THEHIVE_URL, api_key: str = THEHIVE_API_KEY) -> None:
        self.url = url.rstrip("/")
        self.session = requests.Session()
        # TheHive 4 uses X-Api-Key header; this still works with 5
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Api-Key": api_key,
            }
        )

    def create_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = f"{self.url}/api/v1/alert"
        resp = self.session.post(
            endpoint,
            data=json.dumps(alert),
            verify=False,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


def map_wazuh_to_thehive_alert(wazuh_alert: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a single Wazuh alert document into TheHive alert format."""
    rule = wazuh_alert.get("rule", {})
    agent = wazuh_alert.get("agent", {})
    src_ip = wazuh_alert.get("srcip") or wazuh_alert.get("src_ip")
    dst_ip = wazuh_alert.get("dstip") or wazuh_alert.get("dest_ip")

    rule_id = str(rule.get("id", "unknown"))
    rule_desc = rule.get("description", f"Wazuh rule {rule_id}")
    level = int(wazuh_alert.get("level", rule.get("level", 1)))

    # TheHive severity is usually 1–3; map Wazuh 1–15 to 1–3
    if level >= 10:
        severity = 3
    elif level >= 5:
        severity = 2
    else:
        severity = 1

    agent_id = agent.get("id", "unknown")
    agent_name = agent.get("name", agent_id)

    # Unique reference based on rule id + agent id + timestamp
    timestamp = wazuh_alert.get("timestamp") or time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
    )
    source_ref = f"wazuh-{rule_id}-{agent_id}-{timestamp}"

    tags: List[str] = []
    if rule.get("groups"):
        tags.extend([f"group:{g}" for g in rule["groups"]])
    if src_ip:
        tags.append(f"src:{src_ip}")
    if dst_ip:
        tags.append(f"dst:{dst_ip}")
    tags.append(f"agent:{agent_name}")
    tags.append(f"rule_id:{rule_id}")

    alert: Dict[str, Any] = {
        "type": "external",
        "source": "wazuh",
        "sourceRef": source_ref,
        "title": rule_desc,
        "description": json.dumps(wazuh_alert, indent=2),
        "severity": severity,
        "tags": tags,
        # Optionally, you can specify a caseTemplate if you use them:
        # "caseTemplate": "Wazuh-Default",
    }

    return alert


def sync_wazuh_alerts_to_thehive() -> None:
    """Fetch recent Wazuh alerts and push them as TheHive alerts."""
    indexer = WazuhIndexerAPI()
    thehive = TheHiveClient()

    since_ms = int(time.time() * 1000) - LOOKBACK_SECONDS * 1000

    wazuh_alerts = indexer.search_alerts(
        since_epoch_ms=since_ms,
        size=MAX_ALERTS,
        rule_group=FILTER_RULE_GROUP,
    )
    print(f"Fetched {len(wazuh_alerts)} Wazuh alerts from indexer.")

    for wa in wazuh_alerts:
        try:
            alert = map_wazuh_to_thehive_alert(wa)
            created = thehive.create_alert(alert)
            print(
                f"Created TheHive alert id={created.get('id')} "
                f"title={created.get('title')!r}"
            )
        except Exception as exc:
            print("Failed to create TheHive alert:", repr(exc))


def main() -> None:
    sync_wazuh_alerts_to_thehive()


if __name__ == "__main__":
    main()

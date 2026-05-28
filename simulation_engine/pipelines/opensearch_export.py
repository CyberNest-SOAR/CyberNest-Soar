"""OpenSearch export pipeline — bulk-index events into OpenSearch indices."""

import asyncio
import json
import logging
from typing import Dict, Any, List

from config import get_telemetry_setting
from generators.base import RawEvent

logger = logging.getLogger(__name__)

try:
    from opensearchpy import OpenSearch, RequestsHttpConnection, helpers
    from requests.auth import HTTPBasicAuth
    HAS_OPENSEARCH = True
except ImportError:
    HAS_OPENSEARCH = False


def _get_client():
    if not HAS_OPENSEARCH:
        raise ImportError("opensearch-py not installed. Install with: pip install opensearch-py")
    host = get_telemetry_setting("opensearch", "host", "https://localhost:9200")
    user = get_telemetry_setting("opensearch", "user", "admin")
    password = get_telemetry_setting("opensearch", "password", "SecretPassword")
    verify = host.startswith("https+")
    use_ssl = "https" in host
    client = OpenSearch(
        hosts=[host.replace("https+", "https")],
        http_auth=(user, password),
        use_ssl=use_ssl,
        verify_certs=False,
        connection_class=RequestsHttpConnection,
    )
    return client


def ensure_index_template(client: OpenSearch):
    """Create index template for simulation events with proper mapping."""
    template = {
        "index_patterns": ["simulation-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "5s",
            },
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "attack_type": {"type": "keyword"},
                    "subtype": {"type": "keyword"},
                    "campaign_id": {"type": "keyword"},
                    "mitre_technique_id": {"type": "keyword"},
                    "mitre_tactic": {"type": "keyword"},
                    "true_positive": {"type": "boolean"},
                    "noise": {"type": "boolean"},
                    "severity": {"type": "integer"},
                    "simulation": {"type": "object"},
                }
            },
        },
    }
    try:
        client.indices.put_index_template(name="simulation-template", body=template)
        logger.info("Index template 'simulation-template' created/updated")
    except Exception as e:
        logger.warning("Index template creation failed: %s", e)


async def export_to_opensearch(events: List[Dict[str, Any]], index_prefix: str = "simulation-") -> int:
    """Export formatted events to OpenSearch in bulk."""
    def _sync_export():
        client = _get_client()
        ensure_index_template(client)
        campaign = events[0].get("simulation", {}).get("campaign_id", "unknown") if events else "unknown"
        index_name = f"{index_prefix}{campaign}"

        docs = []
        for ev in events:
            doc = {
                "_index": index_name,
                "_source": ev,
            }
            docs.append(doc)

        success, errors = helpers.bulk(client, docs, raise_on_error=False)
        if errors:
            logger.warning("%d errors during bulk indexing", len(errors))
        logger.info("Indexed %d events to %s", success, index_name)
        return success

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_export)


def format_opensearch_bulk_ndjson(events: List[Dict[str, Any]]) -> str:
    """Format events as OpenSearch bulk API NDJSON (for file-based ingestion)."""
    lines = []
    for ev in events:
        action = {"index": {"_index": f"simulation-{ev.get('simulation', {}).get('campaign_id', 'unknown')}"}}
        lines.append(json.dumps(action))
        lines.append(json.dumps(ev))
    return "\n".join(lines)

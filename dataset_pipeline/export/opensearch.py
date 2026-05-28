import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    from opensearchpy import OpenSearch, helpers
    HAS_OPENSEARCH = True
except ImportError:
    HAS_OPENSEARCH = False

from config.settings import OPENSEARCH_HOST, OPENSEARCH_USER, OPENSEARCH_PASSWORD, OPENSEARCH_INDEX
from parsers.normalizer import UnifiedAlert


def get_client():
    if not HAS_OPENSEARCH:
        raise ImportError("opensearch-py not installed. Run: pip install opensearch-py")
    return OpenSearch(
        hosts=[OPENSEARCH_HOST],
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False,
    )


def ensure_index_template(client=None):
    close = False
    if client is None:
        client = get_client()
        close = True
    try:
        template = {
            "index_patterns": [f"{OPENSEARCH_INDEX}-*"],
            "template": {
                "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "event_id": {"type": "keyword"},
                        "dataset_source": {"type": "keyword"},
                        "event_type": {"type": "keyword"},
                        "src_ip": {"type": "ip"},
                        "dst_ip": {"type": "ip"},
                        "src_port": {"type": "integer"},
                        "dst_port": {"type": "integer"},
                        "protocol": {"type": "keyword"},
                        "alert_signature": {"type": "text"},
                        "alert_severity": {"type": "integer"},
                        "alert_category": {"type": "keyword"},
                        "attack_type": {"type": "keyword"},
                        "mitre_technique_id": {"type": "keyword"},
                        "mitre_tactic": {"type": "keyword"},
                        "true_positive": {"type": "boolean"},
                        "noise": {"type": "boolean"},
                        "confidence": {"type": "float"},
                        "analyst_verdict": {"type": "keyword"},
                        "escalation_level": {"type": "keyword"},
                        "playbook_outcome": {"type": "keyword"},
                        "campaign_id": {"type": "keyword"},
                        "cluster_id": {"type": "keyword"},
                        "attack_chain_stage": {"type": "integer"},
                        "suppression_hit": {"type": "boolean"},
                        "geoip_src_country": {"type": "keyword"},
                        "geoip_dst_country": {"type": "keyword"},
                        "extra_fields": {"type": "object", "enabled": False},
                    }
                },
            },
        }
        client.indices.put_index_template(name=f"{OPENSEARCH_INDEX}-template", body=template)
        logger.info("Index template %s created", OPENSEARCH_INDEX)
    except Exception as e:
        logger.warning("Template creation failed: %s", e)
    finally:
        if close:
            client.close()


def bulk_index(alerts: List[UnifiedAlert], index_name: str = None) -> Dict[str, Any]:
    from datetime import datetime, timezone
    if not HAS_OPENSEARCH:
        logger.warning("opensearch-py not available — skipping OpenSearch export")
        return {"error": "opensearch-py not installed"}
    idx = index_name or f"{OPENSEARCH_INDEX}-{datetime.now(timezone.utc).strftime('%Y.%m.%d')}"

    client = get_client()
    ensure_index_template(client)

    success = 0
    errors = 0
    batch = []
    for alert in alerts:
        doc = alert.to_elasticsearch_doc()
        batch.append({"_index": idx, "_id": alert.event_id, "_source": doc})
        if len(batch) >= 500:
            s, e = _flush(client, batch)
            success += s
            errors += e
            batch = []

    if batch:
        s, e = _flush(client, batch)
        success += s
        errors += e

    client.close()
    logger.info("Indexed %d docs to %s (%d errors)", success, idx, errors)
    return {"index": idx, "success": success, "errors": errors}


def _flush(client, batch):
    from opensearchpy import helpers
    try:
        success, errors = helpers.bulk(client, batch, raise_on_error=False, stats_only=True)
        return success, len(errors) if isinstance(errors, list) else errors
    except Exception as e:
        logger.error("Bulk flush failed: %s", e)
        return 0, len(batch)

from collectors.opensearch_client import search, get_alert_by_id
from schemas.models import UnifiedAlert
from utils.normalizer import normalize_wazuh

def get_alerts():
    query = {
        "size": 10,
        "query": {"match_all": {}}
    }
    return search("wazuh-alerts-*", query)

def get_alert_by_event_id(event_id: str):
    raw = get_alert_by_id(event_id)
    return normalize_wazuh(raw)

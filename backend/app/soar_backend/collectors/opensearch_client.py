from opensearchpy import OpenSearch
from core.config import settings

client = OpenSearch(
    hosts=[{"host": settings.OS_HOST, "port": settings.OS_PORT}],
    http_auth=(settings.OS_USER, settings.OS_PASS),
    use_ssl=False
)

def search(index, query):
    return client.search(index=index, body=query)


def get_alert_by_id(event_id: str):
    return client.get(index="wazuh-alerts-*", id=event_id)
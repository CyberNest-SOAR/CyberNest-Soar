import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Container names
ZEEK_CONTAINER = "zeek"
SURICATA_CONTAINER = "suricata"
WAZUH_MANAGER = "single-node-wazuh.manager-1"
WAZUH_AGENT = "single-node-wazuh.agent-1"
WAZUH_INDEXER = "single-node-wazuh.indexer-1"
SURICATA_FILEBEAT = "suricata-filebeat"
ZEEK_FILEBEAT = "zeek-filebeat"

# Log paths (on host filesystem)
ZEEK_LOG_DIR = os.path.join(PROJECT_ROOT, "sensors", "ndr", "zeek", "logs")
SURICATA_LOG_DIR = os.path.join(PROJECT_ROOT, "sensors", "ndr", "suricata", "suricata-setup", "suricata", "logs")
SURICATA_EVE_PATH = os.path.join(SURICATA_LOG_DIR, "eve.json")

# Container-internal log paths
ZEEK_CONTAINER_LOG_DIR = "/opt/zeek/logs/current"
SURICATA_CONTAINER_LOG_DIR = "/var/log/suricata"

# OpenSearch / Elasticsearch
OPENSEARCH_URL = "https://localhost:9200"
OPENSEARCH_AUTH = ("admin", "SecretPassword")

# Wazuh API
WAZUH_API_URL = "https://localhost:55000"
WAZUH_API_AUTH = ("wazuh-wui", "MyS3cr37P450r.*-")

# Alert index pattern
ALERT_INDEX = "wazuh-alerts-*"
FILEBEAT_INDEX = "filebeat-7.10.2-*"

# Network interface (detect first active non-loopback interface)
def get_active_interface():
    try:
        import subprocess
        result = subprocess.run(
            ["ip", "-br", "link"],
            capture_output=True, text=True
        )
        for line in result.stdout.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "UP":
                if parts[0] != "lo":
                    return parts[0]
    except:
        pass
    return "wlan0"

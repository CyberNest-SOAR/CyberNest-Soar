import json
import os

def create_utf8_log(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data) + '\n')

if __name__ == "__main__":
    path = "siem/wazuh/single-node/scratch/suricata_utf8.json"
    data = {
        "timestamp": "2026-05-16T03:10:00.000000+0000",
        "event_type": "alert",
        "alert": {
            "action": "allowed",
            "gid": 1,
            "signature_id": 2000001,
            "rev": 1,
            "signature": "DDoS_UTF8_SUCCESS",
            "category": "Network-Attack",
            "severity": 1
        }
    }
    create_utf8_log(path, data)
    print(f"Created UTF-8 log: {path}")

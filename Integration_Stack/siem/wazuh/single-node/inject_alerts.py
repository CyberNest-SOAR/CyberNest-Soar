import json
import time

log_file = "/var/log/suricata/eve.json"

alerts = [
    {
        "timestamp": "2026-05-06T03:55:00.000000+0000",
        "flow_id": 999999999999901,
        "in_iface": "eth0",
        "event_type": "alert",
        "src_ip": "192.168.1.100",
        "src_port": 54321,
        "dest_ip": "10.0.0.1",
        "dest_port": 80,
        "proto": "TCP",
        "alert": {
            "action": "allowed",
            "gid": 1,
            "signature_id": 2000003,
            "rev": 1,
            "signature": "DDoS - HTTP GET Flood",
            "category": "attempted-dos",
            "severity": 2
        },
        "flow": {
            "pkts_toserver": 200,
            "pkts_toclient": 200,
            "bytes_toserver": 10000,
            "bytes_toclient": 10000,
            "start": "2026-05-06T03:55:00.000000+0000"
        }
    },
    {
        "timestamp": "2026-05-06T03:55:01.000000+0000",
        "flow_id": 999999999999902,
        "in_iface": "eth0",
        "event_type": "alert",
        "src_ip": "8.8.8.8",
        "src_port": 53,
        "dest_ip": "192.168.1.50",
        "dest_port": 80,
        "proto": "TCP",
        "alert": {
            "action": "allowed",
            "gid": 1,
            "signature_id": 1000001,
            "rev": 1,
            "signature": "PHISHING Attempt - Suspicious Login Page",
            "category": "web-application-attack",
            "severity": 1
        },
        "flow": {
            "pkts_toserver": 10,
            "pkts_toclient": 10,
            "bytes_toserver": 1500,
            "bytes_toclient": 1500,
            "start": "2026-05-06T03:55:01.000000+0000"
        }
    }
]

with open(log_file, "a") as f:
    for alert in alerts:
        f.write(json.dumps(alert) + "\n")
        
print("Successfully injected test alerts into eve.json")

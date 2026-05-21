import json
import subprocess
import time
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_config import ZEEK_LOG_DIR, SURICATA_EVE_PATH

def inject_host(path, data):
    log_str = json.dumps(data)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a') as f:
        f.write(log_str + '\n')

if __name__ == "__main__":
    print("--- Testing Rules for All Tools ---")

    print("[+] Injecting Zeek Logs...")
    inject_host(os.path.join(ZEEK_LOG_DIR, "conn.log"), {
        "ts": time.time(), "uid": "ZEEK_HTTP_TEST", "id.orig_h": "10.0.0.1",
        "id.orig_p": 12345, "id.resp_h": "8.8.8.8", "id.resp_p": 80,
        "proto": "tcp", "service": "http", "duration": 0.5, "conn_state": "SF"
    })
    inject_host(os.path.join(ZEEK_LOG_DIR, "conn.log"), {
        "ts": time.time(), "uid": "ZEEK_TCP_TEST", "id.orig_h": "10.0.0.2",
        "id.orig_p": 54321, "id.resp_h": "1.1.1.1", "id.resp_p": 443,
        "proto": "tcp", "service": "other", "conn_state": "S0"
    })

    print("[+] Injecting Suricata Alerts...")
    inject_host(SURICATA_EVE_PATH, {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000000+0000"), "event_type": "alert",
        "alert": {"signature": "PHISHING Attempt - Suspicious Login Page", "severity": 1, "signature_id": 1000001}
    })
    inject_host(SURICATA_EVE_PATH, {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000000+0000"), "event_type": "alert",
        "alert": {"signature": "Brute Force Attempt - SSH", "severity": 2, "signature_id": 3000001}
    })
    inject_host(SURICATA_EVE_PATH, {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000000+0000"), "event_type": "alert",
        "alert": {"signature": "DDoS Attack Detected - Rate Limit Exceeded", "severity": 1, "signature_id": 2000001}
    })

    print("[+] Injecting Velociraptor Alert...")
    velo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sensors", "ndr", "velociraptor")
    os.makedirs(velo_dir, exist_ok=True)
    inject_host(os.path.join(velo_dir, "events.json"), {
        "log_type": "velociraptor", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "message": "VELOCIRAPTOR_ALERT: Potential Ransomware Activity Detected", "client_id": "C.1001"
    })

    print("\n[!] All logs injected. Check Wazuh Dashboard / OpenSearch in 10 seconds.")

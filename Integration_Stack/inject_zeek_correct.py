import os, sys
import json
import time
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_config import ZEEK_LOG_DIR

def inject_zeek(log_type, payload, filename):
    path = os.path.join(ZEEK_LOG_DIR, filename)
    with open(path, 'a') as f:
        f.write(json.dumps(payload) + '\n')
    print(f"[+] Injected Zeek Log ({log_type}) into {filename}")

if __name__ == "__main__":
    print("--- Injecting Zeek Logs directly into sensor logs ---")

    ts_iso = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

    http_payload = {
        "ts": ts_iso,
        "uid": "CHk4T23Z0jJ8P6y65l",
        "id.orig_h": "192.168.1.10",
        "id.orig_p": 54321,
        "id.resp_h": "93.184.216.34",
        "id.resp_p": 80,
        "proto": "tcp",
        "service": "http",
        "duration": 0.5,
        "method": "GET",
        "host": "example.com",
        "uri": "/test-zeek-http-alert"
    }
    inject_zeek("HTTP Traffic", http_payload, "http.log")

    conn_payload = {
        "ts": ts_iso,
        "uid": "CHk4T23Z0jJ8P6y652",
        "id.orig_h": "192.168.1.20",
        "id.orig_p": 4444,
        "id.resp_h": "8.8.8.8",
        "id.resp_p": 53,
        "proto": "tcp",
        "service": "dns",
        "duration": 0.01,
        "conn_state": "SF"
    }
    inject_zeek("TCP Connection", conn_payload, "conn.log")

    print("\n[!] Injection complete. Check Wazuh Dashboard / OpenSearch.")

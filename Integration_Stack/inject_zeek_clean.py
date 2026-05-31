import os, sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_config import ZEEK_LOG_DIR

def inject_zeek_json(log_type, payload, filename="http.log"):
    path = os.path.join(ZEEK_LOG_DIR, filename)
    with open(path, 'a') as f:
        f.write(json.dumps(payload) + '\n')
    print(f"[+] Injected Zeek Log ({log_type}) into {filename}")

if __name__ == "__main__":
    print("--- Testing Zeek Custom Rules (Clean File) ---")

    ts = time.time()

    http_payload = {
        "ts": ts,
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
    inject_zeek_json("HTTP Traffic", http_payload, "http.log")

    conn_payload = {
        "ts": ts,
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
    inject_zeek_json("TCP Connection", conn_payload, "conn.log")

    print("\n[!] Injection complete. Check Wazuh Dashboard / OpenSearch.")

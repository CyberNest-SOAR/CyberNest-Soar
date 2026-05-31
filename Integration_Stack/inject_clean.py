import os, sys
import json
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_config import ZEEK_LOG_DIR

def overwrite_zeek_log(payloads, filename):
    path = os.path.join(ZEEK_LOG_DIR, filename)
    with open(path, 'w') as f:
        for payload in payloads:
            f.write(json.dumps(payload) + '\n')
    print(f"[+] Re-created {filename} with {len(payloads)} clean JSON lines.")

if __name__ == "__main__":
    print("--- Truncating and Injecting clean ISO 8601 logs into Zeek logs ---")

    ts_iso = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

    http_payloads = [
        {
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
    ]

    conn_payloads = [
        {
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
    ]

    overwrite_zeek_log(http_payloads, "http.log")
    overwrite_zeek_log(conn_payloads, "conn.log")
    print("\n[!] Done. Check Wazuh Dashboard / OpenSearch.")

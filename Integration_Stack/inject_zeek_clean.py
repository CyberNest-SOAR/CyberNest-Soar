import os
import json
import time

def inject_zeek_json(log_type, payload):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zeek", "zeek1", "logs", "zeek_json.log")
    with open(path, 'a') as f:
        f.write(json.dumps(payload) + '\n')
    print(f"[+] Injected Zeek Log ({log_type}) into zeek_json.log")

if __name__ == "__main__":
    print("--- Testing Zeek Custom Rules (Clean File) ---")
    
    ts = time.time()
    
    # 1. Zeek HTTP Rule (100001)
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
    inject_zeek_json("HTTP Traffic", http_payload)
    
    # 2. Zeek TCP Connection Rule (100002)
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
    inject_zeek_json("TCP Connection", conn_payload)
    
    print("\n[!] Injection complete. Check Wazuh Dashboard now.")

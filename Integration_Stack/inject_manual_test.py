import os, sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_config import ZEEK_LOG_DIR

def inject_zeek():
    log = {
        "ts": time.time(),
        "uid": "TEST_ZEEK_BEFORE_LINUX",
        "id.orig_h": "192.168.1.10",
        "id.orig_p": 54321,
        "id.resp_h": "93.184.216.34",
        "id.resp_p": 80,
        "proto": "tcp",
        "service": "http",
        "duration": 0.5,
        "orig_bytes": 512,
        "resp_bytes": 2048,
        "conn_state": "SF"
    }
    path = os.path.join(ZEEK_LOG_DIR, "conn.log")
    with open(path, 'a') as f:
        f.write(json.dumps(log) + '\n')
    print("[+] Injected Perfect Zeek Log into conn.log")

if __name__ == "__main__":
    inject_zeek()

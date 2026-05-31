import json
import time
import socket

def inject_udp():
    log = {
        "ts": time.time(),
        "uid": "ZEEK_TEST_LINUX_MIGRATION",
        "id.orig_h": "100.100.100.100",
        "id.orig_p": 54321,
        "id.resp_h": "200.200.200.200",
        "id.resp_p": 80,
        "proto": "tcp",
        "service": "http",
        "duration": 0.5,
        "method": "GET",
        "host": "BEFORE_LINUX",
        "uri": "/TEST_MIGRATION"
    }
    log_str = json.dumps(log)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(log_str.encode("utf-8"), ("127.0.0.1", 514))
    sock.close()
    
    print("[+] Injected Zeek Log via UDP directly to Manager")

if __name__ == "__main__":
    inject_udp()

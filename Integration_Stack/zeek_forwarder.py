import subprocess
import socket
import time
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_config import WAZUH_MANAGER

WAZUH_HOST = "127.0.0.1"
WAZUH_PORT = 514
ZEEK_CONTAINER = "zeek"
LOG_PATH = "/opt/zeek/logs/current/conn.log"

def get_line_count():
    r = subprocess.run(
        ["docker", "exec", ZEEK_CONTAINER, "wc", "-l", LOG_PATH],
        capture_output=True, text=True
    )
    try:
        return int(r.stdout.strip().split()[0])
    except:
        return 0

def get_lines_from(start_line):
    r = subprocess.run(
        ["docker", "exec", ZEEK_CONTAINER,
         "sh", "-c", f"sed -n '{start_line},$p' {LOG_PATH}"],
        capture_output=True, text=True
    )
    return [l.strip() for l in r.stdout.splitlines() if l.strip().startswith("{")]

def send_udp(line):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(line.encode("utf-8"), (WAZUH_HOST, WAZUH_PORT))
        sock.close()
        return True
    except Exception as e:
        print(f"  [ERR] {e}")
        return False

def run():
    print("=" * 55)
    print("  Zeek -> Wazuh Direct UDP Forwarder")
    print(f"  UDP target: {WAZUH_HOST}:{WAZUH_PORT}")
    print(f"  Watching: {ZEEK_CONTAINER}:{LOG_PATH}")
    print("  Press Ctrl+C to stop")
    print("=" * 55)

    last_count = get_line_count()
    print(f"  [*] File has {last_count} lines. Watching for new...\n")

    sent = 0
    while True:
        current_count = get_line_count()
        if current_count > last_count:
            new_lines = get_lines_from(last_count + 1)
            for line in new_lines:
                if send_udp(line):
                    sent += 1
                    uid = "?"
                    try:
                        import json
                        uid = json.loads(line).get("uid", "?")
                    except:
                        pass
                    print(f"  [+] #{sent} uid={uid} -> {WAZUH_HOST}:{WAZUH_PORT}")
            last_count = current_count
        time.sleep(2)

if __name__ == "__main__":
    run()

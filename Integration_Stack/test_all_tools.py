import socket
import subprocess
import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_config import WAZUH_MANAGER, ZEEK_CONTAINER, SURICATA_CONTAINER

GREEN = "\033[92m"
RED   = "\033[91m"
BLUE  = "\033[94m"
RESET = "\033[0m"
BOLD  = "\033[1m"

def ok(msg):  print(f"{GREEN}[OK]{RESET}  {msg}")
def fail(msg): print(f"{RED}[FAIL]{RESET} {msg}")
def info(msg): print(f"{BLUE}[INFO]{RESET} {msg}")
def header(msg): print(f"\n{BOLD}{'='*55}{RESET}\n{BOLD}  {msg}{RESET}\n{'='*55}")


def generate_tcp_traffic():
    header("STEP 1: Generate TCP Traffic (Zeek + Suricata will detect it)")
    sent = 0
    ports = [80, 443, 22, 8080]
    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            try:
                s.connect(("127.0.0.1", port))
                s.send(b"GET /test-alert HTTP/1.0\r\nHost: paypal-secure.fake\r\n\r\n")
            except:
                pass
            s.close()
            sent += 1
            info(f"  TCP packet -> 127.0.0.1:{port}")
        except Exception as e:
            info(f"  Port {port}: {e}")
        time.sleep(0.3)
    ok(f"Sent traffic to {sent} ports")
    time.sleep(2)

def check_zeek():
    header("STEP 2: Verify Zeek is logging connections")
    result = subprocess.run(
        ["docker", "exec", ZEEK_CONTAINER, "sh", "-c",
         "wc -l /opt/zeek/logs/current/conn.log 2>/dev/null || echo '0 conn.log not found'"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        count = result.stdout.strip().split()[0]
        ok(f"Zeek conn.log has {count} entries")
        return True
    else:
        fail(f"Zeek check failed: {result.stderr}")
        return False

def check_suricata():
    header("STEP 3: Verify Suricata is logging events")
    result = subprocess.run(
        ["docker", "exec", SURICATA_CONTAINER, "sh", "-c",
         "wc -l /var/log/suricata/eve.json 2>/dev/null || echo '0'"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        count = result.stdout.strip().split()[0]
        ok(f"Suricata eve.json has {count} events")

    result2 = subprocess.run(
        ["docker", "exec", SURICATA_CONTAINER, "sh", "-c",
         'grep -c "event_type.*alert" /var/log/suricata/eve.json 2>/dev/null || echo 0'],
        capture_output=True, text=True
    )
    alert_count = result2.stdout.strip()
    if alert_count and int(alert_count) > 0:
        ok(f"Suricata has {alert_count} ALERT events (rules matched!)")
    else:
        info("Suricata has 0 alert events - rules need matching traffic")
    return True

def check_wazuh():
    header("STEP 4: Verify Wazuh is receiving & alerting")
    result = subprocess.run(
        ["docker", "exec", WAZUH_MANAGER, "sh", "-c",
         'grep -c "wazuh.agent" /var/ossec/logs/alerts/alerts.json 2>/dev/null || echo 0'],
        capture_output=True, text=True
    )
    wazuh_alerts = result.stdout.strip()
    if wazuh_alerts and int(wazuh_alerts) > 0:
        ok(f"Wazuh has {wazuh_alerts} alerts from wazuh.agent")

    result2 = subprocess.run(
        ["docker", "exec", WAZUH_MANAGER, "sh", "-c",
         'grep "wazuh.agent" /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -1'],
        capture_output=True, text=True
    )
    if result2.stdout.strip():
        try:
            last = json.loads(result2.stdout.strip())
            rule = last.get("rule", {})
            agent = last.get("agent", {})
            ts = last.get("timestamp", "")
            info(f"  Latest: [{ts[:19]}] Rule {rule.get('id')} - {rule.get('description')}")
            info(f"  Agent: {agent.get('name')} | Level: {rule.get('level')}")
        except:
            info(f"  Latest: {result2.stdout.strip()[:200]}")
    else:
        fail("No agent alerts found in Wazuh alerts.json (check indexer directly)")

def check_velociraptor():
    header("STEP 5: Verify Velociraptor")
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Status}}", "single-node-velociraptor-1"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        status = result.stdout.strip()
        if status == "running":
            ok("Velociraptor container is running")
        else:
            info(f"Velociraptor status: {status}")
    else:
        info("Velociraptor container not found (may use different name)")
        result2 = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        v_names = [l for l in result2.stdout.strip().split('\n') if 'veloci' in l.lower()]
        if v_names:
            info(f"  Found Velociraptor-like containers: {v_names}")

def check_filebeat():
    header("STEP 6: Verify filebeat is shipping to OpenSearch")
    for fb in ["suricata-filebeat", "zeek-filebeat"]:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}", "--filter", f"name={fb}"],
            capture_output=True, text=True
        )
        if fb in result.stdout:
            ok(f"{fb} container is running")

def summary():
    header("ACCESS POINTS")
    print(f"""
  {BOLD}Wazuh Dashboard:{RESET}    https://localhost (admin/SecretPassword)
  {BOLD}OpenSearch API:{RESET}      https://localhost:9200
  {BOLD}Zeek logs:{RESET}          sensors/ndr/zeek/logs/
  {BOLD}Suricata logs:{RESET}      sensors/ndr/suricata/suricata-setup/suricata/logs/eve.json
""")

if __name__ == "__main__":
    print(f"\n{BOLD}Integration Test - All Tools{RESET}\n")
    generate_tcp_traffic()
    check_zeek()
    check_suricata()
    check_wazuh()
    check_velociraptor()
    check_filebeat()
    summary()

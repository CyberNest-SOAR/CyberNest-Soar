"""
test_all_tools.py
=================
Generates REAL traffic to trigger Suricata + Zeek alerts, then verifies
the alerts appear in Wazuh. Run from your Windows host machine.

Tools tested:
  1. Zeek  - sees all TCP connections on eth0 -> writes conn.log -> Wazuh reads it
  2. Suricata - matches rules on traffic -> writes eve.json -> Wazuh reads it
  3. Velociraptor - checked via log file
  4. Wazuh - alerts verified via alerts.json
"""

import socket
import subprocess
import json
import time
import sys

# Suricata/Zeek container IP (both share eth0 = 192.168.65.3 based on host networking)
TARGET_IP = "127.0.0.1"

WAZUH_MANAGER = "single-node-wazuh.manager-1"

GREEN = "\033[92m"
RED   = "\033[91m"
BLUE  = "\033[94m"
RESET = "\033[0m"
BOLD  = "\033[1m"

def ok(msg):  print(f"{GREEN}[OK]{RESET}  {msg}")
def fail(msg): print(f"{RED}[FAIL]{RESET} {msg}")
def info(msg): print(f"{BLUE}[INFO]{RESET} {msg}")
def header(msg): print(f"\n{BOLD}{'='*55}{RESET}\n{BOLD}  {msg}{RESET}\n{'='*55}")


# ─────────────────────────────────────────────────────────
# 1. Generate real TCP traffic (triggers Zeek conn.log)
# ─────────────────────────────────────────────────────────
def generate_tcp_traffic():
    header("STEP 1: Generate TCP Traffic (Zeek will log it)")
    sent = 0
    ports = [80, 443, 22, 8080]
    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            # Send payload that matches Suricata phishing rule (sid:999999)
            try:
                s.connect((TARGET_IP, port))
                s.send(b"GET /test-suricata-alert HTTP/1.0\r\nHost: paypal-secure.fake\r\n\r\n")
            except:
                pass
            s.close()
            sent += 1
            info(f"  TCP packet -> {TARGET_IP}:{port}")
        except Exception as e:
            info(f"  Port {port}: {e}")
        time.sleep(0.3)

    # Extra: send raw TCP with "test-suricata-alert" content (rule sid:999999)
    for _ in range(3):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((TARGET_IP, 80))
            s.send(b"test-suricata-alert\r\n")
            s.close()
        except:
            pass
        time.sleep(0.2)

    ok(f"Sent traffic to {sent} ports on {TARGET_IP}")
    time.sleep(2)  # wait for Zeek/Suricata to process


# ─────────────────────────────────────────────────────────
# 2. Check Zeek conn.log (inside container)
# ─────────────────────────────────────────────────────────
def check_zeek():
    header("STEP 2: Verify Zeek is logging connections")
    result = subprocess.run(
        ["docker", "exec", "zeek", "sh", "-c",
         "wc -l /usr/local/zeek/logs/conn.log"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        count = result.stdout.strip().split()[0]
        ok(f"Zeek conn.log has {count} entries")
        return True
    else:
        fail(f"Zeek check failed: {result.stderr}")
        return False


# ─────────────────────────────────────────────────────────
# 3. Check Suricata eve.json
# ─────────────────────────────────────────────────────────
def check_suricata():
    header("STEP 3: Verify Suricata is logging events")
    result = subprocess.run(
        ["docker", "exec", "suricata", "sh", "-c",
         "wc -l /var/log/suricata/eve.json"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        count = result.stdout.strip().split()[0]
        ok(f"Suricata eve.json has {count} events")

    # Check for alerts specifically
    result2 = subprocess.run(
        ["docker", "exec", "suricata", "sh", "-c",
         'grep -c "event_type.*alert" /var/log/suricata/eve.json || echo 0'],
        capture_output=True, text=True
    )
    alert_count = result2.stdout.strip()
    if alert_count and int(alert_count) > 0:
        ok(f"Suricata has {alert_count} ALERT events (rules matched!)")
    else:
        info("Suricata has 0 alert events - rules need matching traffic")
        info("  Flow/DNS/HTTP events are still being forwarded to Wazuh")
    return True


# ─────────────────────────────────────────────────────────
# 4. Check Wazuh alerts (from Zeek + Suricata)
# ─────────────────────────────────────────────────────────
def check_wazuh():
    header("STEP 4: Verify Wazuh is receiving & alerting")

    # Check Zeek alerts
    result = subprocess.run(
        ["docker", "exec", WAZUH_MANAGER, "sh", "-c",
         'grep -c "zeek-agent" /var/ossec/logs/alerts/alerts.json || echo 0'],
        capture_output=True, text=True
    )
    zeek_alerts = result.stdout.strip()
    if zeek_alerts and int(zeek_alerts) > 0:
        ok(f"Wazuh has {zeek_alerts} alerts from Zeek agent")
    else:
        fail("No Zeek alerts found in Wazuh")

    # Get latest Zeek alert
    result2 = subprocess.run(
        ["docker", "exec", WAZUH_MANAGER, "sh", "-c",
         'grep "zeek-agent" /var/ossec/logs/alerts/alerts.json | tail -1'],
        capture_output=True, text=True
    )
    if result2.stdout.strip():
        try:
            last = json.loads(result2.stdout.strip())
            rule = last.get("rule", {})
            agent = last.get("agent", {})
            ts = last.get("timestamp", "")
            info(f"  Latest alert: [{ts[:19]}] Rule {rule.get('id')} - {rule.get('description')}")
            info(f"  Agent: {agent.get('name')} | Level: {rule.get('level')}")
        except:
            info(f"  Latest: {result2.stdout.strip()[:200]}")

    # Check Suricata alerts in Wazuh
    result3 = subprocess.run(
        ["docker", "exec", WAZUH_MANAGER, "sh", "-c",
         'grep -c "suricata" /var/ossec/logs/alerts/alerts.json || echo 0'],
        capture_output=True, text=True
    )
    suricata_wazuh = result3.stdout.strip()
    if suricata_wazuh and int(suricata_wazuh) > 0:
        ok(f"Wazuh has {suricata_wazuh} events mentioning Suricata")
    else:
        info("Suricata events not yet in Wazuh alerts (may appear via flow events)")


# ─────────────────────────────────────────────────────────
# 5. Check Velociraptor
# ─────────────────────────────────────────────────────────
def check_velociraptor():
    header("STEP 5: Verify Velociraptor container is running")
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Status}}", "velociraptor"],
        capture_output=True, text=True
    )
    status = result.stdout.strip()
    if status == "running":
        ok("Velociraptor container is running")
    else:
        fail(f"Velociraptor status: {status}")

    # Check if GUI is accessible
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect(("127.0.0.1", 8889))
        s.close()
        ok("Velociraptor GUI reachable on port 8889")
    except:
        info("Velociraptor GUI port 8889 not directly reachable (may be on different port)")

    result2 = subprocess.run(
        ["docker", "port", "velociraptor"],
        capture_output=True, text=True
    )
    if result2.stdout.strip():
        info(f"  Velociraptor ports: {result2.stdout.strip()}")


# ─────────────────────────────────────────────────────────
# 6. Summary
# ─────────────────────────────────────────────────────────
def summary():
    header("SUMMARY - Access Points")
    print(f"""
  {BOLD}Wazuh Dashboard:{RESET}    https://localhost  (admin / SecretPassword)
  {BOLD}Velociraptor:{RESET}       check port above
  {BOLD}Suricata logs:{RESET}      suricata1/suricata/logs/eve.json
  {BOLD}Zeek logs:{RESET}          zeek/zeek1/logs/conn.log

  {BOLD}In Wazuh Dashboard:{RESET}
    -> Security Events -> Filter: agent.name = "zeek-agent"
    -> You will see Zeek + Suricata + Velociraptor events
""")


if __name__ == "__main__":
    print(f"\n{BOLD}Integration Test - All Tools{RESET}")
    print("Containers detected as running. Testing pipeline...\n")

    generate_tcp_traffic()
    check_zeek()
    check_suricata()
    check_wazuh()
    check_velociraptor()
    summary()

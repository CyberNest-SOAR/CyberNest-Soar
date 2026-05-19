import json
import subprocess
import time

def inject(container, path, data):
    log_str = json.dumps(data)
    result = subprocess.run(
        ["docker", "exec", container, "sh", "-c",
         f"echo '{log_str}' >> {path}"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  [OK] Injected into {container}:{path}")
    else:
        print(f"  [FAIL] {container}: {result.stderr.strip()}")

def check_wazuh_alerts(keyword, label):
    time.sleep(2)
    result = subprocess.run(
        ["docker", "exec", "single-node-wazuh.manager-1", "sh", "-c",
         f"grep -c '{keyword}' /var/ossec/logs/alerts/alerts.json || echo 0"],
        capture_output=True, text=True
    )
    count = result.stdout.strip()
    print(f"  [WAZUH] {label}: {count} alerts found")
    return int(count) if count.isdigit() else 0

if __name__ == "__main__":
    print("=" * 50)
    print("  Injecting Test Logs for All Tools")
    print("=" * 50)

    # ── 1. ZEEK ──────────────────────────────────────────
    print("\n[1] ZEEK - Injecting conn.log entry...")
    inject("zeek", "/usr/local/zeek/logs/conn.log", {
        "ts": float(int(time.time())),
        "uid": "TEST_ZEEK_MANUAL_001",
        "id.orig_h": "10.0.0.99",
        "id.orig_p": 5555,
        "id.resp_h": "8.8.8.8",
        "id.resp_p": 80,
        "proto": "tcp",
        "service": "http",
        "duration": 2.5,
        "orig_bytes": 512,
        "resp_bytes": 2048,
        "conn_state": "SF"
    })

    # ── 2. SURICATA ───────────────────────────────────────
    print("\n[2] SURICATA - Injecting eve.json alert...")
    inject("suricata", "/var/log/suricata/eve.json", {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000000+0000", time.gmtime()),
        "flow_id": 999999001,
        "event_type": "alert",
        "src_ip": "10.0.0.99",
        "src_port": 5555,
        "dest_ip": "1.1.1.1",
        "dest_port": 80,
        "proto": "TCP",
        "alert": {
            "action": "allowed",
            "gid": 1,
            "signature_id": 999999,
            "rev": 1,
            "signature": "TEST Suricata Alert Manual Inject",
            "category": "Attempted Information Leak",
            "severity": 2
        }
    })

    # ── 3. VELOCIRAPTOR ───────────────────────────────────
    print("\n[3] VELOCIRAPTOR - Injecting events.json...")
    inject("single-node-zeek-agent-1", "/var/log/velociraptor/events.json", {
        "log_type": "velociraptor",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "message": "VELOCIRAPTOR_TEST Manual forensic event",
        "client_id": "C.test001",
        "artifact": "Windows.System.Pslist",
        "level": "WARNING"
    })

    # ── 4. WAIT & CHECK WAZUH ─────────────────────────────
    print("\n[4] Waiting 10 seconds for Wazuh to process...")
    time.sleep(10)

    print("\n[5] Checking Wazuh Dashboard Alerts...")
    zeek_ok    = check_wazuh_alerts("TEST_ZEEK_MANUAL_001", "Zeek")
    suricata_ok = check_wazuh_alerts("999999001", "Suricata")
    velo_ok    = check_wazuh_alerts("VELOCIRAPTOR_TEST", "Velociraptor")

    print("\n" + "=" * 50)
    print("  RESULTS")
    print("=" * 50)
    print(f"  Zeek       -> {'VISIBLE in Wazuh' if zeek_ok else 'NOT in Wazuh yet'}")
    print(f"  Suricata   -> {'VISIBLE in Wazuh' if suricata_ok else 'NOT in Wazuh yet'}")
    print(f"  Velociraptor -> {'VISIBLE in Wazuh' if velo_ok else 'NOT in Wazuh yet'}")
    print()
    print("  Open Dashboard: https://localhost")
    print("  Security Events -> filter: agent.name = zeek-agent")
    print("=" * 50)

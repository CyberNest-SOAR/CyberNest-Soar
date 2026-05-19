import subprocess

def check(keyword, name):
    cmd = ["docker", "exec", "single-node-wazuh.manager-1", "sh", "-c", f"grep -c '{keyword}' /var/ossec/logs/alerts/alerts.json || echo 0"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    count = res.stdout.strip()
    print(f"{name}: {'FOUND' if count and count != '0' else 'NOT FOUND'} ({count} hits)")

print("--- Wazuh Alerts Verification ---")
check("ZEEK_HTTP_TEST", "Zeek HTTP Rule (100001)")
check("ZEEK_TCP_TEST", "Zeek TCP Rule (100002)")
check("PHISHING Attempt", "Suricata Phishing Rule (1000001)")
check("Brute Force Attempt - SSH", "Suricata Brute Force Rule (3000001)")
check("DDoS Attack Detected", "Suricata DDoS Rule (2000001)")
check("VELOCIRAPTOR_ALERT", "Velociraptor Rule (100003)")

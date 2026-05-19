import os
import json
import time

def inject_suricata_host(signature, sig_id, severity):
    log = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000000+0000", time.gmtime()),
        "event_type": "alert",
        "src_ip": "192.168.1.100",
        "src_port": 45678,
        "dest_ip": "192.168.1.5",
        "dest_port": 80,
        "proto": "TCP",
        "alert": {
            "action": "allowed",
            "gid": 1,
            "signature_id": sig_id,
            "rev": 1,
            "signature": signature,
            "category": "Attempted Administrator Privilege Gain",
            "severity": severity
        }
    }
    
    # Write directly to the host file which is mapped to the container
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "suricata1", "suricata", "logs", "eve.json")
    with open(path, 'a') as f:
        f.write(json.dumps(log) + '\n')
    print(f"[+] Injected Suricata Alert: {signature}")

if __name__ == "__main__":
    print("--- Testing Suricata Custom Rules (Host Write) ---")
    
    # 1. DDoS Alert
    inject_suricata_host("DDoS Attack Detected - Rate Limit Exceeded", 2000001, 1)
    
    # 2. Brute Force Alert
    inject_suricata_host("Brute Force Attempt - SSH", 3000001, 2)
    
    # 3. Phishing Alert
    inject_suricata_host("PHISHING Attempt - Suspicious Login Page", 1000001, 1)
    
    print("\n[!] Injection complete. Check Wazuh Dashboard now.")

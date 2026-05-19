import socket
import time
import urllib.request
import threading
import json
import os

print("==================================================")
print("      CONTAINER-BASED REAL TRAFFIC SIMULATOR")
print("==================================================")

def trigger_zeek():
    print("[*] 1. Generating Zeek Traffic...")
    try:
        req = urllib.request.Request("http://neverssl.com", headers={'User-Agent': 'Mozilla/5.0'})
        urllib.request.urlopen(req, timeout=3)
        print("   -> Successfully browsed http://neverssl.com")
    except Exception as e:
        print(f"   -> Failed browsing: {e}")

def trigger_phishing():
    print("[*] 2. Generating Suricata Phishing Traffic...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80)) # Public IP so packet leaves container
        payload = b"GET /login/secure/account/verify HTTP/1.1\r\nHost: paypal-secure.fake\r\n\r\n"
        s.send(payload)
        s.close()
        print("   -> Sent phishing HTTP request to 8.8.8.8")
    except Exception as e:
        pass

def trigger_bruteforce():
    print("[*] 3. Generating Suricata Brute Force Traffic...")
    # Send 15 rapid SYN connections to wazuh manager's SSH port
    for _ in range(15):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            s.connect(("172.18.0.6", 22)) 
            s.close()
        except:
            pass
    print("   -> Sent 15 rapid SSH connection attempts to 172.18.0.6:22")

def trigger_ddos():
    print("[*] 4. Generating Suricata DDoS Traffic...")
    def blast():
        for _ in range(30):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.1)
                s.connect(("8.8.8.8", 80))
                s.close()
            except:
                pass
    
    threads = []
    for _ in range(5):
        t = threading.Thread(target=blast)
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()
    print("   -> Sent 150 rapid connection attempts to simulate DDoS")

trigger_zeek()
time.sleep(1)
trigger_phishing()
time.sleep(1)
trigger_bruteforce()
time.sleep(1)
trigger_ddos()

print("\n[+] Container traffic generated! Please check Wazuh Dashboard.")

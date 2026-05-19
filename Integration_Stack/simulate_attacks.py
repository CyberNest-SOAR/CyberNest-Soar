import socket
import time
import urllib.request
import threading

TARGET_IP = "127.0.0.1"

def print_step(msg):
    print(f"\n[*] \033[93m{msg}\033[0m")

def test_zeek_http_and_conn():
    print_step("1. Generating Zeek Traffic (HTTP and Connection)...")
    try:
        # This will create a conn.log and http.log entry in Zeek
        urllib.request.urlopen(f"http://{TARGET_IP}:8080/zeek-test-real-traffic", timeout=2)
    except:
        pass
    print("   -> Sent HTTP request to port 8080.")

def test_suricata_bruteforce():
    print_step("2. Generating Suricata Brute Force (SSH Port 22)...")
    # Rule requires 5 connections in 60 seconds
    for i in range(6):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((TARGET_IP, 22))
            s.close()
        except:
            pass
        print(f"   -> SSH connection attempt {i+1}/6")
        time.sleep(0.1)

def test_suricata_ddos():
    print_step("3. Generating Suricata DDoS (Port 80 SYN Flood Simulation)...")
    # Rule requires 100 connections in 10 seconds
    def blast():
        for _ in range(25):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.1)
                s.connect((TARGET_IP, 80))
                s.close()
            except:
                pass
    
    threads = []
    for _ in range(5): # 5 threads * 25 requests = 125 requests
        t = threading.Thread(target=blast)
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()
    print("   -> Sent 125 rapid connection attempts to port 80.")

if __name__ == "__main__":
    print("="*50)
    print("      REAL TRAFFIC ATTACK SIMULATOR")
    print("="*50)
    
    test_zeek_http_and_conn()
    time.sleep(1)
    
    test_suricata_bruteforce()
    time.sleep(1)
    
    test_suricata_ddos()
    
    print("\n[+] All attacks simulated! Please check Wazuh Dashboard in 10-20 seconds.")
    print("    You should see alerts for:")
    print("    - Zeek: HTTP Analysis / Connection Trace")
    print("    - Suricata: Brute Force Attempt - SSH")
    print("    - Suricata: DDoS Attack Detected")

import socket
import time

def send_tcp(port, payload):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("127.0.0.1", port))
        s.send(payload)
        s.close()
        print(f"[+] Sent payload to port {port}")
    except Exception as e:
        print(f"[-] Port {port} closed, but traffic was generated: {e}")

if __name__ == "__main__":
    print("--- Simulating Real Network Traffic ---")
    
    # 1. Trigger Suricata Phishing Rule (login + verify)
    print("1. Simulating Phishing Access...")
    send_tcp(80, b"GET /admin/login?user=admin&verify=true HTTP/1.1\r\nHost: internal.site\r\n\r\n")
    
    # 2. Trigger Suricata Test Rule (test-suricata-alert)
    print("2. Simulating Test Alert Signature...")
    send_tcp(80, b"test-suricata-alert\n")
    
    # 3. Random Activity for Zeek
    print("3. Generating General Traffic for Zeek...")
    for p in [22, 443, 3306]:
        send_tcp(p, b"Hello Zeek!\n")
    
    print("Done! Check Wazuh Dashboard in 10-15 seconds.")

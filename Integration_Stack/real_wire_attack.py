import socket
import urllib.request
import ssl
import time
import subprocess

SURICATA_IP = "172.19.0.7"

print("==================================================")
print("      REAL WIRE-SNIFFED TRAFFIC GENERATOR         ")
print("==================================================")

# 1. GENERATE REAL SURICATA WIRE ALERT (UDP Phishing)
print("\n[*] 1. Sending real UDP Phishing packet to Suricata...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = b"paypal-secure-alert-test"
    sock.sendto(payload, (SURICATA_IP, 9999))
    sock.close()
    print("   -> Real UDP packet sent successfully to Suricata!")
except Exception as e:
    print(f"   -> Failed to send UDP packet: {e}")

# 2. GENERATE REAL ZEEK WIRE CONNECTION (TCP/HTTP Outbound via VM physical interface)
print("\n[*] 2. Creating real TCP/HTTP Connection to outbound internet (example.com) for Zeek...")
try:
    # Since Zeek is sniffing the host VM's main interface 'ens33',
    # we must generate outbound internet traffic to force the packets through 'ens33'.
    # This will generate a real TCP connection in 'conn.log' and a real HTTP connection in 'http.log'!
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(("example.com", 80))
    s.send(b"GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n")
    response = s.recv(128)
    s.close()
    print("   -> Outbound TCP/HTTP Session established with example.com over 'ens33' successfully!")
except Exception as e:
    print(f"   -> Failed to establish outbound TCP connection: {e}")

print("\n==================================================")
print("[+] Wire traffic generated successfully!")
print("[!] Open your Wazuh Dashboard and watch the real alerts flow!")
print("==================================================")

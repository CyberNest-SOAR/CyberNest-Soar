import socket
import urllib.request
import ssl
import time
import subprocess, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_config import get_active_interface

TARGET_IP = "127.0.0.1"
INTERFACE = get_active_interface()

print("==================================================")
print("      REAL WIRE-SNIFFED TRAFFIC GENERATOR         ")
print("==================================================")
print(f"  Active interface detected: {INTERFACE}")

print("\n[*] 1. Sending real UDP packet...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = b"paypal-secure-alert-test"
    sock.sendto(payload, (TARGET_IP, 9999))
    sock.close()
    print("   -> Real UDP packet sent successfully!")
except Exception as e:
    print(f"   -> Failed: {e}")

print("\n[*] 2. Creating real TCP/HTTP Connection to outbound internet...")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(("example.com", 80))
    s.send(b"GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n")
    response = s.recv(128)
    s.close()
    print("   -> Outbound TCP/HTTP Session established with example.com!")
except Exception as e:
    print(f"   -> Failed: {e}")

print("\n==================================================")
print("[+] Wire traffic generated!")
print(f"[!] Zeek/Suricata should capture this via interface: {INTERFACE}")
print("==================================================")

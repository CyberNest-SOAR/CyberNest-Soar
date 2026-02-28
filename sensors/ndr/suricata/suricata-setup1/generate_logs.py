#!/usr/bin/env python3
from scapy.all import *
import time

# ----------------------------
# CONFIGURATION
# ----------------------------
TARGET_IP = "127.0.0.1"  # Suricata sensor IP (localhost is fine)
TARGET_PORT_HTTP = 80
TARGET_PORT_SMTP = 25

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def is_ipv4(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
        return True
    except:
        return False

def is_ipv6(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
        return True
    except:
        return False

# ----------------------------
# 1. PACKET DECODING ANOMALIES
# ----------------------------
def generate_ipv4_small_packet():
    if not is_ipv4(TARGET_IP):
        return
    pkt = IP(dst=TARGET_IP)/Raw(b"A")  # SID 2200000: too small
    send(pkt)
    print("[+] Sent IPv4 too small packet (SID 2200000)")

def generate_wrong_ip_version():
    if not is_ipv4(TARGET_IP):
        return
    pkt = IP(dst=TARGET_IP)
    pkt.version = 6  # SID 2200011: wrong IP version
    send(pkt)
    print("[+] Sent wrong IP version packet (SID 2200011)")

def generate_ipv6_small_packet():
    if not is_ipv6(TARGET_IP):
        return
    pkt = IPv6(dst=TARGET_IP)/Raw(b"A")  # SID 2200012: too small
    send(pkt)
    print("[+] Sent IPv6 too small packet (SID 2200012)")

# ----------------------------
# 2. APPLICATION-LAYER ANOMALIES (via raw TCP packets)
# ----------------------------
def applayer_protocol_mismatch():
    """Send SMTP payload on HTTP port to trigger SID 2260000"""
    pkt = IP(dst=TARGET_IP)/TCP(dport=TARGET_PORT_HTTP, sport=12345, flags="PA")/Raw(b"EHLO test.com\r\n")
    send(pkt)
    print("[+] Triggered applayer_mismatch_protocol_both_directions (SID 2260000)")

def smtp_no_tls_after_starttls():
    """Craft SMTP STARTTLS anomaly to trigger SID 2260004"""
    # Send fake SMTP handshake + STARTTLS without encryption
    payload = b"EHLO test.com\r\nSTARTTLS\r\nDATA\r\n"
    pkt = IP(dst=TARGET_IP)/TCP(dport=TARGET_PORT_SMTP, sport=12346, flags="PA")/Raw(payload)
    send(pkt)
    print("[+] Triggered applayer_no_tls_after_starttls (SID 2260004)")

def applayer_unexpected_protocol():
    """Send HTTP payload on SMTP port to trigger SID 2260005"""
    pkt = IP(dst=TARGET_IP)/TCP(dport=TARGET_PORT_SMTP, sport=12347, flags="PA")/Raw(b"GET / HTTP/1.1\r\n\r\n")
    send(pkt)
    print("[+] Triggered applayer_unexpected_protocol (SID 2260005)")

def applayer_wrong_direction_first_data():
    """Send server-first payload on TCP to trigger SID 2260001"""
    pkt = IP(dst=TARGET_IP)/TCP(dport=TARGET_PORT_HTTP, sport=12348, flags="PA")/Raw(b"HTTP/1.1 200 OK\r\n\r\n")
    send(pkt)
    print("[+] Triggered applayer_wrong_direction_first_data (SID 2260001)")

def applayer_detect_protocol_only_one_direction():
    """Send only client request, no response, trigger SID 2260002"""
    pkt = IP(dst=TARGET_IP)/TCP(dport=TARGET_PORT_HTTP, sport=12349, flags="PA")/Raw(b"GET / HTTP/1.1\r\n\r\n")
    send(pkt)
    print("[+] Triggered applayer_detect_protocol_only_one_direction (SID 2260002)")

def applayer_proto_detection_skipped():
    """Send unknown protocol payload to trigger SID 2260003"""
    pkt = IP(dst=TARGET_IP)/TCP(dport=12350, sport=12350, flags="PA")/Raw(b"\x01\x02\x03\x04")
    send(pkt)
    print("[+] Triggered applayer_proto_detection_skipped (SID 2260003)")

# ----------------------------
# 3. MAIN
# ----------------------------
if __name__ == "__main__":
    print("[*] Generating packet decoding anomalies...")
    generate_ipv4_small_packet()
    time.sleep(0.2)
    generate_wrong_ip_version()
    time.sleep(0.2)
    generate_ipv6_small_packet()
    time.sleep(0.2)

    print("[*] Generating application-layer anomalies...")
    applayer_protocol_mismatch()
    time.sleep(0.2)
    smtp_no_tls_after_starttls()
    time.sleep(0.2)
    applayer_unexpected_protocol()
    time.sleep(0.2)
    applayer_wrong_direction_first_data()
    time.sleep(0.2)
    applayer_detect_protocol_only_one_direction()
    time.sleep(0.2)
    applayer_proto_detection_skipped()
    time.sleep(0.2)

    print("[*] Done. Check Suricata logs for triggered alerts.")

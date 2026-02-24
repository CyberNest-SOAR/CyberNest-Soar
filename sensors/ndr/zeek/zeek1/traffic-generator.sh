#!/bin/bash
set -e

echo "[*] Generating traffic for Zeek logs..."

# --- HTTP traffic (http.log) ---
echo "[*] HTTP traffic"
curl -s http://example.com >/dev/null

# --- HTTPS/SSL traffic (ssl.log) ---
echo "[*] HTTPS traffic"
curl -s https://example.com >/dev/null

# --- DNS traffic (dns.log) ---
echo "[*] DNS queries"
nslookup google.com >/dev/null
nslookup yahoo.com >/dev/null

# --- NTP traffic (ntp.log) ---
echo "[*] NTP traffic"
apt-get update -y >/dev/null
apt-get install -y ntpdate >/dev/null
ntpdate -q pool.ntp.org >/dev/null || true

# --- File downloads (files.log) ---
echo "[*] File downloads"
wget -q https://www.w3.org/TR/PNG/iso_8859-1.txt -O /tmp/testfile.txt

# --- Weird/malformed traffic (weird.log) ---
echo "[*] Generating malformed packets"
apt-get install -y hping3 >/dev/null
# TCP SYN flood (small, safe)
hping3 -S -p 80 -c 3 127.0.0.1 >/dev/null
# UDP flood
hping3 -2 -p 53 -c 3 127.0.0.1 >/dev/null

# --- DDoS/Brute force simulation (notice.log) ---
echo "[*] Simulating multiple connections (notice.log)"
for i in {1..5}; do
  curl -s http://localhost/login >/dev/null
done

echo "[*] Traffic generation complete!"

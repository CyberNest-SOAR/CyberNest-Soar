#!/bin/bash
TARGET_IP="172.20.10.3"

# Phishing
echo "[*] Sending phishing traffic..."
for payload in "user=admin&pass=123" "login=guest&pwd=letmein"; do
    curl -s -o /dev/null -X POST http://$TARGET_IP/login --data "$payload"
done

# SSH brute-force
echo "[*] Sending SSH brute-force traffic..."
for i in {1..5}; do
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 user@$TARGET_IP exit 2>/dev/null
done

# DDoS SYN flood
echo "[*] Sending DDoS-like traffic..."
for i in {1..20}; do
    sudo hping3 -S -p 80 -c 5 $TARGET_IP
    sudo hping3 -1 -c 5 $TARGET_IP
done

echo "[✔] Suspicious traffic simulation complete!"

#!/bin/bash
set -e

echo "[+] Detecting primary network interface..."
NIC=$(ip route get 8.8.8.8 | awk '{for(i=1;i<=NF;i++) if ($i=="dev") print $(i+1)}' | head -n1)
if [ -z "$NIC" ]; then
    echo "[!] Could not detect NIC automatically. Using 'eth0'"
    NIC="eth0"
fi
echo "[+] Detected NIC: $NIC"

echo "[+] Creating folders..."
mkdir -p suricata/config suricata/logs suricata/rules filebeat
for d in suricata/config suricata/logs suricata/rules filebeat; do
    if [ ! -f "$d/.gitkeep" ]; then
        touch "$d/.gitkeep"
    fi
done

echo "[+] Pulling public Suricata image from Docker Hub..."
docker pull jasonish/suricata:latest

echo "[+] Extracting default suricata.yaml..."
docker run --rm jasonish/suricata:latest cat /etc/suricata/suricata.yaml > suricata/config/suricata.yaml

echo "[+] Updating suricata.yaml with interface: $NIC"
sed -i "s/interface: .*/interface: $NIC/" suricata/config/suricata.yaml

# Export NIC as environment variable for docker-compose
export SURICATA_NIC=$NIC

echo "[+] Starting the full ELK + Suricata stack..."
docker compose up -d --build

echo "[+] Setup complete. All containers are running!"

#!/bin/bash
set -e

LOG_DIR="/opt/zeek/logs/current"
mkdir -p "$LOG_DIR"

# Auto detect interface
if [ -z "$ZEEK_INTERFACE" ]; then
    ZEEK_INTERFACE=$(ip route | awk '/default/ {print $5}' | head -n1)
fi

# Fallback if detection fails
if [ -z "$ZEEK_INTERFACE" ]; then
    ZEEK_INTERFACE="eth0"
fi

echo "[+] Using interface: $ZEEK_INTERFACE"
echo "[+] Logs directory: $LOG_DIR"

cd /opt/zeek/share/zeek/site

exec zeek -i "$ZEEK_INTERFACE" local.zeek

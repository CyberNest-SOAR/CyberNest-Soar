#!/bin/bash

set -e

echo "[+] Building Zeek container..."
docker-compose build

echo "[+] Starting Zeek..."
docker-compose up -d

echo "[+] Zeek started."
echo "[+] Logs: ./logs/current"

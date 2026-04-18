#!/bin/bash

set -e

########################################
# Install Zeek
########################################
# if command -v zeek >/dev/null 2>&1; then
#     echo "[+] Zeek is already installed"
# else
#     echo "[*] Installing Zeek..."
#     sudo apt install -y zeek
# fi

########################################
# Install Suricata
########################################
# if command -v suricata >/dev/null 2>&1; then
#     echo "[+] Suricata is already installed"
# else
#     echo "[*] Installing Suricata..."
#     sudo apt install -y suricata
# fi

########################################
# Enable and start Suricata
########################################
echo "[*] Enabling and starting Suricata service..."
sudo systemctl enable suricata 2>/dev/null || true
sudo systemctl restart suricata 2>/dev/null || true

########################################
# Enable and start Zeek (ZeekControl)
########################################
if [ -x /opt/zeek/bin/zeekctl ]; then
    echo "[*] Deploying Zeek via ZeekControl..."
	sudo /opt/zeek/bin/zeekctl deploy || echo "[!] zeekctl deploy returned non-zero"
else
    echo "[!] zeekctl not found. Check Zeek installation."
fi

########################################
# auditd (endpoint events)
########################################
echo "[*] Enabling auditd..."
sudo systemctl enable auditd 2>/dev/null || true
sudo systemctl restart auditd 2>/dev/null || true

########################################
# Show status
########################################
echo ""
echo "===== SERVICE STATUS ====="
sudo systemctl status suricata --no-pager 2>/dev/null | head -n 5 || true

echo ""
echo "===== ZEEK STATUS ====="
sudo /opt/zeek/bin/zeekctl status 2>/dev/null || echo "ZeekControl not running"

########################################
# Log locations
########################################
echo ""
echo "===== LOG LOCATIONS ====="

echo "[Zeek Logs]"
echo "  Current:   /opt/zeek/logs/current/"
echo "  Rotated:   /opt/zeek/logs/YYYY-MM-DD/"

echo ""
echo "[Suricata Logs]"
echo "  Main dir:  /var/log/suricata/"
echo "  eve.json:  /var/log/suricata/eve.json"
echo "  fast.log:  /var/log/suricata/fast.log"
echo "  stats.log: /var/log/suricata/stats.log"

echo ""
echo "[auditd]"
echo "  audit.log: /var/log/audit/audit.log"
echo "  Configure rules (example): sudo auditctl -w /etc/passwd -p rwa -k dlds_watch"

echo ""
echo "[*] Setup complete!"

#!/usr/bin/env python3
"""
migrate_to_linux.py
===================
Automated script to migrate the SOC/SIEM/SOAR integration project from Windows to Linux.
Runs on both Windows (before moving files) or Linux (after moving files).

Features:
  1. Backs up files before modifying (.bak)
  2. Converts hardcoded absolute Windows paths to robust, dynamic, cross-platform paths using `os.path`
  3. Inserts 'import os' where needed in Python scripts
  4. Changes Windows-specific target IPs (192.168.65.3) to 127.0.0.1 for Linux
  5. Auto-detects the active Linux network interface and updates zeek/zeek1/Dockerfile
"""

import os
import re
import shutil
import sys
import platform

# Color support for terminals
GREEN = "\033[92m"
RED   = "\033[91m"
BLUE  = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD  = "\033[1m"

def print_ok(msg):    print(f"{GREEN}[OK] {msg}{RESET}")
def print_info(msg):  print(f"{BLUE}[INFO] {msg}{RESET}")
def print_warn(msg):  print(f"{YELLOW}[WARN] {msg}{RESET}")
def print_error(msg): print(f"{RED}[ERROR] {msg}{RESET}")
def print_header(msg):
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  {msg}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

# Replacements structure: { filepath: [ (target_regex, replacement_str), ... ] }
REPLACEMENTS = {
    "siem/wazuh/single-node/docker-compose.yml": [
        (
            r"c:\Users\LOQ\OneDrive\Desktop\open_sources_integration\soar\velociraptor\velociraptor",
            "../../../soar/velociraptor/velociraptor"
        ),
        (
            r"c:/Users/LOQ/OneDrive/Desktop/open_sources_integration/soar/velociraptor/velociraptor",
            "../../../soar/velociraptor/velociraptor"
        )
    ],
    "real_attack_simulation.py": [
        (
            r'velo_path = r"C:\Users\LOQ\OneDrive\Desktop\open_sources_integration\soar\velociraptor\velociraptor\events.json"',
            'velo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "soar", "velociraptor", "velociraptor", "events.json")'
        ),
        (
            r'TARGET_IP = "192.168.65.3"',
            'TARGET_IP = "127.0.0.1"'
        )
    ],
    "test_all_tools.py": [
        (
            r'TARGET_IP = "192.168.65.3"',
            'TARGET_IP = "127.0.0.1"'
        )
    ],
    "inject_zeek_rules.py": [
        (
            r'path = rf"c:\Users\LOQ\OneDrive\Desktop\open_sources_integration\zeek\zeek1\logs\{filename}"',
            'path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zeek", "zeek1", "logs", filename)'
        ),
        (
            r'path = rf"c:\Users\LOQ\OneDrive\Desktop\open_sources_integration\zeek\zeek1\logs\current\{filename}"',
            'path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zeek", "zeek1", "logs", "current", filename)'
        )
    ],
    "inject_zeek_correct.py": [
        (
            r'path = r"c:\Users\LOQ\OneDrive\Desktop\open_sources_integration\zeek\zeek1\logs\wazuh_zeek.log"',
            'path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zeek", "zeek1", "logs", "wazuh_zeek.log")'
        )
    ],
    "inject_clean.py": [
        (
            r'path = r"c:\Users\LOQ\OneDrive\Desktop\open_sources_integration\zeek\zeek1\logs\wazuh_zeek.log"',
            'path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zeek", "zeek1", "logs", "wazuh_zeek.log")'
        )
    ],
    "inject_zeek_clean.py": [
        (
            r'path = r"c:\Users\LOQ\OneDrive\Desktop\open_sources_integration\zeek\zeek1\logs\zeek_json.log"',
            'path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zeek", "zeek1", "logs", "zeek_json.log")'
        )
    ],
    "inject_suricata_rules.py": [
        (
            r'path = r"c:\Users\LOQ\OneDrive\Desktop\open_sources_integration\suricata1\suricata\logs\eve.json"',
            'path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "suricata1", "suricata", "logs", "eve.json")'
        )
    ],
    "final_rules_test.py": [
        (
            r'path_velo = r"C:\Users\LOQ\OneDrive\Desktop\open_sources_integration\soar\velociraptor\velociraptor\events.json"',
            'path_velo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "soar", "velociraptor", "velociraptor", "events.json")'
        )
    ],
    "inject_manual_test.py": [
        (
            r'path = r"c:\Users\LOQ\OneDrive\Desktop\open_sources_integration\zeek\zeek1\logs\conn.log"',
            'path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zeek", "zeek1", "logs", "conn.log")'
        )
    ]
}

def detect_linux_interface():
    """Attempts to automatically find the default active network interface on Linux."""
    if platform.system().lower() != "linux":
        return None
    try:
        # Method 1: Read routing table
        with open("/proc/net/route") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "00000000":
                    return parts[0]
    except Exception:
        pass

    try:
        # Method 2: Check default gateway using ip route command
        import subprocess
        res = subprocess.run(["ip", "route", "get", "8.8.8.8"], capture_output=True, text=True)
        if res.returncode == 0:
            match = re.search(r"dev\s+(\S+)", res.stdout)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None

def process_file_replacements(filepath, rule_list):
    # Normalize path to match host OS
    normalized_path = os.path.normpath(filepath)
    if not os.path.exists(normalized_path):
        print_warn(f"File not found (skipped): {normalized_path}")
        return False

    # Create backup copy
    backup_path = normalized_path + ".bak"
    shutil.copy2(normalized_path, backup_path)

    with open(normalized_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    original_content = content
    changes_count = 0

    for target, replacement in rule_list:
        # Replace occurrences
        if target in content:
            content = content.replace(target, replacement)
            changes_count += 1
        else:
            # Fallback to regex-based replacement for case variations or backslash differences
            escaped_target = re.escape(target).replace(r'\\', r'[\/\\]')
            content, count = re.subn(escaped_target, replacement, content)
            changes_count += count

    # Automatically add "import os" to Python scripts if we injected os.path and it's missing
    if filepath.endswith(".py") and "os.path" in content and "import os" not in content:
        content = "import os\n" + content
        changes_count += 1

    if content != original_content:
        with open(normalized_path, "w", encoding="utf-8") as f:
            f.write(content)
        print_ok(f"Modified {normalized_path} ({changes_count} changes applied). Backup created.")
        return True
    else:
        # If no changes were needed, clean up backup
        if os.path.exists(backup_path):
            os.remove(backup_path)
        print_info(f"No changes required for {normalized_path}.")
        return False

def configure_zeek_interface():
    dockerfile_path = os.path.normpath("zeek/zeek1/Dockerfile")
    if not os.path.exists(dockerfile_path):
        print_error(f"Zeek Dockerfile not found at {dockerfile_path}")
        return

    # Backup Dockerfile
    backup_path = dockerfile_path + ".bak"
    shutil.copy2(dockerfile_path, backup_path)

    with open(dockerfile_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Detect or prompt for network interface
    sys_type = platform.system().lower()
    detected_iface = None
    if sys_type == "linux":
        detected_iface = detect_linux_interface()
        if detected_iface:
            print_ok(f"Detected active Linux network interface: {detected_iface}")
        else:
            print_warn("Could not auto-detect Linux active interface.")
    
    # Prompt user or use default/detected
    final_iface = None
    if sys_type == "linux" and detected_iface:
        final_iface = detected_iface
    else:
        # If running on Windows, ask the user or just default to ens33 as standard for VMs
        default_iface = "ens33"
        print_info(f"System is {platform.system()}. Running in non-interactive/default mode.")
        print_info(f"Defaulting Zeek sniffer network interface to: {BOLD}{default_iface}{RESET}")
        final_iface = default_iface

    # Replace ENTRYPOINT interface
    entrypoint_pattern = r'ENTRYPOINT\s*\[\s*"zeek"\s*,\s*"-i"\s*,\s*"[^"]+"\s*,\s*"local"\s*\]'
    new_entrypoint = f'ENTRYPOINT ["zeek", "-i", "{final_iface}", "local"]'
    
    new_content, count = re.subn(entrypoint_pattern, new_entrypoint, content)
    
    if count > 0:
        with open(dockerfile_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print_ok(f"Successfully configured Zeek sniffer interface to '{final_iface}' in {dockerfile_path}")
    else:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        print_warn(f"Could not find matching ENTRYPOINT to modify in {dockerfile_path}.")

def main():
    print_header("SOC/SIEM/SOAR Integration - Linux Migration Script")
    
    print_info("Starting workspace conversion...")
    modified_files = 0
    
    for filepath, rules in REPLACEMENTS.items():
        if process_file_replacements(filepath, rules):
            modified_files += 1

    print_info("Configuring Zeek sniffer network interface...")
    configure_zeek_interface()

    print_header("MIGRATION COMPLETED SUCCESSFULLY")
    print_ok(f"Completed processing. Modified files: {modified_files}")
    print_info("All modified files have backups ending in '.bak'")
    print_info("Ready to move the project to Linux!")
    print("\nNext steps on Linux:")
    print(f"  1. Run: {BOLD}sudo sysctl -w vm.max_map_count=262144{RESET} (for Wazuh Indexer)")
    print(f"  2. Run: {BOLD}chmod -R 777 soar/velociraptor/logs soar/velociraptor/data suricata1/suricata/logs zeek/zeek1/logs{RESET}")
    print(f"  3. Run: {BOLD}docker-compose -f siem/wazuh/single-node/generate-indexer-certs.yml up -d{RESET}")
    print(f"  4. Run: {BOLD}docker-compose -f siem/wazuh/single-node/docker-compose.yml up -d{RESET}")
    print(f"  5. Build and launch Zeek/Suricata/Velociraptor docker files.\n")

if __name__ == "__main__":
    main()

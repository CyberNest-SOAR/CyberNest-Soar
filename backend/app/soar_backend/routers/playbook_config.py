import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Body, HTTPException
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/playbook-config", tags=["Playbook Configuration"])

CONFIG_PATH = Path(__file__).resolve().parent.parent / "playbook_config.json"

DEFAULT_CONFIG = {
    "rules": [
        {
            "name": "critical_threat",
            "conditions": {
                "tags_contain": ["C2", "misp_hit"],
                "min_risk_score": 80,
                "min_severity": 12,
            },
            "action": "isolate_host",
            "confidence": 0.98,
            "automation_level": "full",
            "reason": "Critical threat detected: Automated host isolation triggered.",
        },
        {
            "name": "high_risk_activity",
            "conditions": {
                "tags_contain": ["malware", "brute_force"],
                "min_risk_score": 60,
                "min_severity": 8,
            },
            "action": "block_ip",
            "confidence": 0.85,
            "automation_level": "full",
            "reason": "High risk activity: Automated IP block initiated.",
        },
        {
            "name": "medium_risk_review",
            "conditions": {
                "min_risk_score": 40,
                "min_severity": 5,
            },
            "action": "create_case",
            "confidence": 0.70,
            "automation_level": "semi",
            "reason": "Potential threat: Incident case created for analyst review.",
        },
        {
            "name": "low_risk_log",
            "conditions": {},
            "action": "log_event",
            "confidence": 0.50,
            "automation_level": "manual",
            "reason": "Low risk event: Logged for reference.",
        },
    ],
    "default_action": "log_event",
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

def _load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    _save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG

def _save_config(config):
    config["updated_at"] = datetime.now(timezone.utc).isoformat()
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2, default=str)

@router.get("/")
async def get_playbook_config():
    return _load_config()

@router.put("/")
async def update_playbook_config(config: dict = Body(...)):
    _save_config(config)
    return {"message": "Playbook configuration updated", "config": _load_config()}

@router.post("/rules")
async def add_playbook_rule(
    name: str = Body(...),
    action: str = Body(...),
    confidence: float = Body(0.5),
    automation_level: str = Body("manual"),
    reason: str = Body(""),
    conditions: Optional[dict] = Body(None),
):
    cfg = _load_config()
    rules = cfg.setdefault("rules", [])
    for rule in rules:
        if rule.get("name") == name:
            raise HTTPException(status_code=400, detail=f"Rule '{name}' already exists")
    rules.append({
        "name": name,
        "conditions": conditions or {},
        "action": action,
        "confidence": confidence,
        "automation_level": automation_level,
        "reason": reason,
    })
    _save_config(cfg)
    return {"message": f"Rule '{name}' added", "rule": rules[-1]}

@router.delete("/rules/{rule_name}")
async def remove_playbook_rule(rule_name: str):
    cfg = _load_config()
    rules = cfg.get("rules", [])
    for i, rule in enumerate(rules):
        if rule.get("name") == rule_name:
            removed = rules.pop(i)
            _save_config(cfg)
            return {"message": f"Rule '{rule_name}' removed", "rule": removed}
    raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")

@router.get("/rules")
async def list_playbook_rules():
    cfg = _load_config()
    return {"rules": cfg.get("rules", []), "default_action": cfg.get("default_action", "log_event")}

@router.post("/evaluate")
async def evaluate_playbook(alert_data: dict = Body(...)):
    cfg = _load_config()
    rules = cfg.get("rules", [])

    severity = alert_data.get("severity", 0)
    risk_score = alert_data.get("risk_score", 0)
    tags = alert_data.get("tags", [])
    description = alert_data.get("description", "").lower()

    for rule in rules:
        cond = rule.get("conditions", {})
        min_risk = cond.get("min_risk_score", 0)
        min_sev = cond.get("min_severity", 0)
        required_tags = cond.get("tags_contain", [])

        if risk_score < min_risk:
            continue
        if severity < min_sev:
            continue
        if required_tags and not all(t in tags for t in required_tags):
            continue

        return {
            "matched_rule": rule["name"],
            "action": rule["action"],
            "confidence": rule["confidence"],
            "automation_level": rule["automation_level"],
            "reason": rule.get("reason", ""),
        }

    default = cfg.get("default_action", "log_event")
    return {
        "matched_rule": "default",
        "action": default,
        "confidence": 0.5,
        "automation_level": "manual",
        "reason": "Default action: No specific rules matched.",
    }

@router.post("/reset")
async def reset_playbook_config():
    _save_config(DEFAULT_CONFIG)
    return {"message": "Playbook configuration reset to defaults", "config": DEFAULT_CONFIG}

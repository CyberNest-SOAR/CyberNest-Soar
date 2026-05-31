import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/threat-intel", tags=["Threat Intelligence"])

TI_DB_PATH = Path(__file__).resolve().parent.parent / "threat_intel_db.json"

def _load_db():
    if TI_DB_PATH.exists():
        with open(TI_DB_PATH) as f:
            return json.load(f)
    return {"token_usage": {}, "services": {}, "intel_data": []}

def _save_db(data):
    TI_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TI_DB_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)

@router.get("/token-usage")
async def get_token_usage():
    db = _load_db()
    return db.get("token_usage", {})

@router.post("/token-usage")
async def update_token_usage(
    service: str = Body(...),
    tokens_used: int = Body(...),
    endpoint: str = Body("unknown"),
):
    db = _load_db()
    usage = db.setdefault("token_usage", {})
    service_key = service.lower().replace(" ", "_")
    if service_key not in usage:
        usage[service_key] = {"total_tokens": 0, "calls": 0, "endpoints": {}}
    usage[service_key]["total_tokens"] += tokens_used
    usage[service_key]["calls"] += 1
    ep_usage = usage[service_key]["endpoints"].setdefault(endpoint, {"tokens": 0, "calls": 0})
    ep_usage["tokens"] += tokens_used
    ep_usage["calls"] += 1
    usage[service_key]["last_updated"] = datetime.now(timezone.utc).isoformat()
    _save_db(db)
    return {
        "service": service,
        "total_tokens": usage[service_key]["total_tokens"],
        "total_calls": usage[service_key]["calls"],
    }

@router.get("/services")
async def list_threat_intel_services():
    db = _load_db()
    return db.get("services", {})

@router.post("/services")
async def add_threat_intel_service(
    name: str = Body(...),
    url: str = Body(...),
    api_key: Optional[str] = Body(None),
    enabled: bool = Body(True),
    description: str = Body(""),
):
    db = _load_db()
    services = db.setdefault("services", {})
    service_key = name.lower().replace(" ", "_")
    services[service_key] = {
        "name": name,
        "url": url,
        "api_key_configured": bool(api_key),
        "enabled": enabled,
        "description": description,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_db(db)
    return {"message": f"Threat intel service '{name}' added", "service": services[service_key]}

@router.delete("/services/{service_key}")
async def remove_threat_intel_service(service_key: str):
    db = _load_db()
    services = db.get("services", {})
    if service_key not in services:
        raise HTTPException(status_code=404, detail="Service not found")
    removed = services.pop(service_key)
    _save_db(db)
    return {"message": f"Service '{removed['name']}' removed"}

@router.get("/data")
async def get_threat_intel_data(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    ioc_type: Optional[str] = Query(None, description="Filter by IOC type (ip, domain, hash, url)"),
):
    db = _load_db()
    intel_data = db.get("intel_data", [])
    if ioc_type:
        intel_data = [d for d in intel_data if d.get("ioc_type", "").lower() == ioc_type.lower()]
    total = len(intel_data)
    page = intel_data[offset:offset + limit]
    return {"total": total, "offset": offset, "limit": limit, "intel_data": page}

@router.post("/data")
async def add_threat_intel_data(
    ioc: str = Body(...),
    ioc_type: str = Body(...),
    source: str = Body("manual"),
    threat_level: str = Body("unknown"),
    notes: str = Body(""),
):
    db = _load_db()
    intel_data = db.setdefault("intel_data", [])
    import uuid
    entry = {
        "id": str(uuid.uuid4()),
        "ioc": ioc,
        "ioc_type": ioc_type,
        "source": source,
        "threat_level": threat_level,
        "notes": notes,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    intel_data.append(entry)
    _save_db(db)
    return {"message": "IOC added", "entry": entry}

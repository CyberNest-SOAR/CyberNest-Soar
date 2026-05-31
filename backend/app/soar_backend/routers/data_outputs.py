import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-outputs", tags=["Data Outputs"])

OUTPUTS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "dataset_pipeline" / "data" / "outputs"

def _get_latest_ndjson():
    files = sorted(OUTPUTS_DIR.glob("soc_dataset_*.ndjson"))
    if not files:
        return None
    return files[-1]

def _get_latest_thehive():
    files = sorted(OUTPUTS_DIR.glob("thehive_cases_*.json"))
    if not files:
        return None
    return files[-1]

@router.get("/")
async def list_outputs():
    if not OUTPUTS_DIR.exists():
        raise HTTPException(status_code=404, detail="Outputs directory not found")
    files = []
    for f in OUTPUTS_DIR.iterdir():
        if f.is_file():
            files.append(f.name)
    subdirs = {}
    for d in OUTPUTS_DIR.iterdir():
        if d.is_dir():
            subdirs[d.name] = [sf.name for sf in d.iterdir() if sf.is_file()]
    latest_ndjson = _get_latest_ndjson()
    return {
        "outputs_dir": str(OUTPUTS_DIR),
        "files": sorted(files),
        "directories": subdirs,
        "latest_ndjson": latest_ndjson.name if latest_ndjson else None,
        "latest_ndjson_fields": 78,
    }

@router.get("/filebeat")
async def get_filebeat_logs(
    limit: int = Query(100, ge=1, le=11521),
    offset: int = Query(0, ge=0),
):
    logs_path = Path(__file__).resolve().parent.parent / "logs.json"
    if not logs_path.exists():
        raise HTTPException(status_code=404, detail="filebeat logs not found")
    with open(logs_path) as f:
        data = json.load(f)
    events = data.get("events", []) if isinstance(data, dict) else data
    if isinstance(events, list):
        total = len(events)
        page = events[offset:offset + limit]
        return {
            "campaign_id": data.get("campaign_id", "unknown") if isinstance(data, dict) else None,
            "total": total,
            "offset": offset,
            "limit": limit,
            "events": page,
        }
    return data

@router.get("/thehive-cases")
async def get_thehive_cases(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    latest = _get_latest_thehive()
    if not latest:
        raise HTTPException(status_code=404, detail="No TheHive case files found")
    with open(latest) as f:
        data = json.load(f)
    total = len(data) if isinstance(data, list) else 1
    page = data[offset:offset + limit] if isinstance(data, list) else [data]
    return {
        "source": latest.name,
        "total_cases": total,
        "offset": offset,
        "limit": limit,
        "cases": page,
    }

@router.get("/soc-events")
async def get_soc_events(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    severity_min: Optional[int] = Query(None, ge=0, le=15),
    attack_type: Optional[str] = Query(None),
    source_filter: Optional[str] = Query(None, description="dataset_source filter"),
):
    latest = _get_latest_ndjson()
    if not latest:
        raise HTTPException(status_code=404, detail="No SOC ndjson dataset found")

    total = 0
    matched = 0
    results = []
    with open(latest) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            event = json.loads(line)
            if severity_min is not None and (event.get("alert_severity") or 0) < severity_min:
                continue
            if attack_type and event.get("attack_type") != attack_type:
                continue
            if source_filter and event.get("dataset_source") != source_filter:
                continue
            if matched < offset:
                matched += 1
                continue
            if len(results) >= limit:
                continue
            results.append(event)
            matched += 1

    return {
        "source": latest.name,
        "total_events": total,
        "returned": len(results),
        "offset": offset,
        "limit": limit,
        "fields": list(results[0].keys()) if results else [],
        "events": results,
    }

@router.get("/soc-dataset")
async def get_soc_dataset():
    latest = _get_latest_ndjson()
    if not latest:
        complete_file = OUTPUTS_DIR / "soc_dataset_complete.json"
        if complete_file.exists():
            with open(complete_file) as f:
                data = json.load(f)
            return {"source": "soc_dataset_complete.json", "total_events": len(data) if isinstance(data, list) else 1, "events": data}
        raise HTTPException(status_code=404, detail="No SOC dataset found")
    return await get_soc_events(limit=500)

@router.get("/soc-events/sources")
async def get_soc_event_sources():
    latest = _get_latest_ndjson()
    if not latest:
        raise HTTPException(status_code=404, detail="No SOC ndjson dataset found")
    sources = set()
    attack_types = set()
    with open(latest) as f:
        for i, line in enumerate(f):
            if i >= 5000:
                break
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            ds = event.get("dataset_source")
            if ds:
                sources.add(ds)
            at = event.get("attack_type")
            if at:
                attack_types.add(at)
    return {
        "dataset_sources": sorted(sources),
        "attack_types": sorted(attack_types),
        "total_in_dataset": _count_ndjson_lines(latest),
    }

@router.get("/llm-datasets/{dataset_name}")
async def get_llm_dataset(
    dataset_name: str,
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    valid = {"analyst_notes", "escalation_decisions", "suppression_reasons"}
    if dataset_name not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid dataset. Choose from: {valid}")
    llm_dir = OUTPUTS_DIR / "llm_datasets"
    files = list(llm_dir.glob(f"{dataset_name}_*.json"))
    if not files:
        raise HTTPException(status_code=404, detail=f"No {dataset_name} dataset found")
    latest = sorted(files)[-1]
    with open(latest) as f:
        data = json.load(f)
    total = len(data) if isinstance(data, list) else 1
    page = data[offset:offset + limit] if isinstance(data, list) else [data]
    return {
        "source": latest.name,
        "dataset": dataset_name,
        "total_entries": total,
        "offset": offset,
        "limit": limit,
        "entries": page,
    }

@router.get("/ndjson/latest")
async def get_latest_ndjson():
    latest = _get_latest_ndjson()
    if not latest:
        raise HTTPException(status_code=404, detail="No ndjson file found")
    return FileResponse(str(latest), media_type="application/x-ndjson", filename=latest.name)

@router.get("/ndjson/{filename}")
async def get_ndjson_file(filename: str):
    file_path = OUTPUTS_DIR / filename
    if not file_path.exists() or not file_path.suffix == ".ndjson":
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(file_path), media_type="application/x-ndjson")

@router.get("/csv/{filename}")
async def get_csv_file(filename: str):
    file_path = OUTPUTS_DIR / filename
    if not file_path.exists() or not file_path.suffix == ".csv":
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(file_path), media_type="text/csv")

def _count_ndjson_lines(path: Path) -> int:
    count = 0
    with open(path) as f:
        for line in f:
            if line.strip():
                count += 1
    return count

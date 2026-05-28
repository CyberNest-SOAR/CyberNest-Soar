"""
simulation_engine/main.py — CyberNestSOAR Attack Simulation Framework

FastAPI application that orchestrates configurable attack telemetry generation
across Wazuh, Suricata, Zeek, Velociraptor, and osquery.

**Endpoints:**
- ``POST /simulate/generate`` — Generate events and return in requested formats
- ``POST /simulate/campaign`` — Run a multi-campaign replay
- ``GET  /simulate/status`` — Show current simulation status
- ``POST /simulate/config`` — Update attack distribution config at runtime
"""

import asyncio
import json
import logging
import os
import random
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse

from config import (
    load_config, get_config, get_attack_distribution,
    get_total_events, get_campaign_id, set_campaign_id,
    get_simulation_setting, get_seed,
)
from generators.base import RawEvent, BaseGenerator
from generators.benign_traffic import BenignTrafficGenerator
from generators.malware_simulator import MalwareSimulator
from generators.brute_force_simulator import BruteForceSimulator
from generators.phishing_simulator import PhishingSimulator
from generators.ddos_simulator import DDoSSimulator
from generators.lateral_movement import LateralMovementGenerator
from generators.privilege_escalation import PrivilegeEscalationGenerator

from telemetry.wazuh_events import format_wazuh_batch, format_wazuh_ndjson
from telemetry.suricata_alerts import format_suricata_batch, format_suricata_ndjson
from telemetry.zeek_logs import format_zeek_batch, format_zeek_ndjson
from telemetry.velociraptor_events import format_velociraptor_batch, format_velociraptor_ndjson
from telemetry.osquery_events import format_osquery_batch, format_osquery_ndjson

from pipelines.dataset_builder import build_dataset, build_normalized_json
from pipelines.opensearch_export import export_to_opensearch, format_opensearch_bulk_ndjson
from pipelines.thehive_cases import export_to_thehive, format_thehive_cases_json
from pipelines.file_injector import inject_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("simulation_engine")

app = FastAPI(
    title="CyberNestSOAR Simulation Engine",
    description="Configurable attack simulation & SOC telemetry generator",
    version="1.0.0",
)

# Generator registry
GENERATORS: Dict[str, BaseGenerator] = {}


def _init_generators(campaign_id: str = None):
    cid = campaign_id or get_campaign_id()
    global GENERATORS
    GENERATORS = {
        "benign_traffic": BenignTrafficGenerator(campaign_id=cid),
        "noise_alerts": BenignTrafficGenerator(campaign_id=cid),
        "malware": MalwareSimulator(campaign_id=cid),
        "brute_force": BruteForceSimulator(campaign_id=cid),
        "phishing": PhishingSimulator(campaign_id=cid),
        "ddos": DDoSSimulator(campaign_id=cid),
        "lateral_movement": LateralMovementGenerator(campaign_id=cid),
        "privilege_escalation": PrivilegeEscalationGenerator(campaign_id=cid),
    }
    return GENERATORS


def _generate_all(distribution: Dict[str, int], total: int) -> List[RawEvent]:
    """Generate events proportionally across attack types."""
    if not GENERATORS:
        _init_generators()
    total_pct = sum(distribution.values())
    if total_pct == 0:
        return []
    events: List[RawEvent] = []
    for attack_type, pct in distribution.items():
        gen = GENERATORS.get(attack_type)
        if gen is None:
            continue
        count = max(1, int(total * pct / sum(distribution.values())))
        evts = gen.generate(count)
        if attack_type == "noise_alerts":
            for e in evts:
                e.attack_type = "noise"
                e.true_positive = False
                e.noise = True
        events.extend(evts)
    random.Random(get_seed()).shuffle(events)
    return events


def detect_targets_from_format(fmt: str) -> List[str]:
    """Map a format string to injectable telemetry targets."""
    mapping = {
        "suricata":       ["suricata"],
        "zeek":           ["zeek"],
        "velociraptor":   ["velociraptor"],
        "osquery":        ["osquery"],
        "all":            ["suricata", "zeek", "velociraptor", "arkime"],
    }
    return mapping.get(fmt, ["suricata"])


# --------------------------------------------------------------------------- #
# Startup                                                                      #
# --------------------------------------------------------------------------- #
@app.on_event("startup")
async def startup():
    cfg_path = Path(__file__).parent / "config" / "attack_profiles.yaml"
    if not cfg_path.exists():
        logger.warning("Config not found at %s — using defaults", cfg_path)
    load_config(cfg_path)
    cid = get_campaign_id()
    _init_generators(cid)
    logger.info("Simulation Engine started — campaign: %s", cid)
    dist = get_attack_distribution()
    logger.info("Attack distribution: %s", dist)


# --------------------------------------------------------------------------- #
# Endpoints                                                                    #
# --------------------------------------------------------------------------- #
@app.api_route("/simulate/generate", methods=["GET", "POST"])
async def generate(
    total: int = Query(default=None, description="Total events to generate"),
    campaign_id: str = Query(default="", description="Override campaign ID"),
    format: str = Query(default="json", description="Output format: json, ndjson, wazuh, suricata, zeek, velociraptor, osquery, opensearch_bulk, csv, all"),
    export_opensearch: bool = Query(default=False, description="Export to OpenSearch"),
    export_thehive: bool = Query(default=False, description="Create TheHive cases for high-sev events"),
    write_files: bool = Query(default=False, description="Write events to sensor log files (eve.json, etc.) for Wazuh ingestion"),
):
    """Generate simulated security events with configurable attack distribution.

    When ``write_files=true`` the generated events are also appended to the
    Suricata / Zeek / Velociraptor / Arkime log files that the Wazuh agent
    monitors, causing alerts to appear in the Wazuh dashboard (30-60s delay).
    The target set is inferred from the ``format`` parameter
    (e.g. ``format=suricata`` → only suricata, ``format=all`` → all four).
    """
    total = total or get_total_events()
    cid = campaign_id or str(uuid.uuid4())[:8]
    set_campaign_id(cid)
    _init_generators(cid)

    dist = get_attack_distribution()
    logger.info("Generating %d events — campaign: %s — distribution: %s", total, cid, dist)

    raw_events = _generate_all(dist, total)

    noise_level = get_simulation_setting("noise_level", 0.15)
    seed = get_seed()
    rng = random.Random(seed)
    dupe_count = 0
    for ev in list(raw_events):
        if rng.random() < noise_level:
            dup = RawEvent(**ev.to_dict())
            dup.event_id = ev.event_id + "-dup"
            dup.noise = True
            dup.true_positive = False
            dup.severity = max(1, dup.severity - 2)
            raw_events.append(dup)
            dupe_count += 1
    logger.info("Added %d noise/duplicate events", dupe_count)

    # Clustering: group events into attack waves
    if get_simulation_setting("alert_clustering", True):
        cluster_size = max(5, total // 20)
        for i in range(0, len(raw_events), cluster_size):
            cluster_time = raw_events[i].timestamp
            for j in range(i, min(i + cluster_size, len(raw_events))):
                raw_events[j].timestamp = cluster_time + timedelta(
                    seconds=random.Random(seed + j).randint(0, 300)
                )

    fmt = format.lower()

    if fmt == "all":
        result = {
            "campaign_id": cid,
            "total_events": len(raw_events),
            "datasets": build_dataset(raw_events, ["json", "ndjson", "csv", "opensearch_bulk"]),
            "wazuh": format_wazuh_ndjson(raw_events),
            "suricata": format_suricata_ndjson(raw_events),
            "zeek_conn": format_zeek_ndjson(raw_events, "conn"),
            "zeek_http": format_zeek_ndjson(raw_events, "http"),
            "zeek_dns": format_zeek_ndjson(raw_events, "dns"),
            "velociraptor": format_velociraptor_ndjson(raw_events),
            "osquery": format_osquery_ndjson(raw_events),
            "thehive_cases": format_thehive_cases_json(raw_events),
        }
    elif fmt == "wazuh":
        result = {"campaign_id": cid, "total": len(raw_events), "events": format_wazuh_batch(raw_events)}
    elif fmt == "suricata":
        result = {"campaign_id": cid, "total": len(raw_events), "events": format_suricata_batch(raw_events)}
    elif fmt == "zeek":
        result = {"campaign_id": cid, "total": len(raw_events), "conn": format_zeek_batch(raw_events, "conn"),
                  "http": format_zeek_batch(raw_events, "http"), "dns": format_zeek_batch(raw_events, "dns")}
    elif fmt == "velociraptor":
        result = {"campaign_id": cid, "total": len(raw_events), "events": format_velociraptor_batch(raw_events)}
    elif fmt == "osquery":
        result = {"campaign_id": cid, "total": len(raw_events), "events": format_osquery_batch(raw_events)}
    elif fmt in ("ndjson", "opensearch_bulk", "csv"):
        ds = build_dataset(raw_events, [fmt])
        return JSONResponse(content={"campaign_id": cid, "total": len(raw_events), "data": ds[fmt]})
    else:
        result = {"campaign_id": cid, "total": len(raw_events), "events": build_normalized_json(raw_events)}

    # Optional OpenSearch export
    if export_opensearch:
        try:
            if fmt == "wazuh":
                docs = format_wazuh_batch(raw_events)
            elif fmt == "suricata":
                docs = format_suricata_batch(raw_events)
            else:
                docs = build_normalized_json(raw_events)
            indexed = await export_to_opensearch(docs)
            result["opensearch_indexed"] = indexed
        except Exception as e:
            logger.warning("OpenSearch export failed: %s", e)
            result["opensearch_error"] = str(e)

    # Optional TheHive case creation
    if export_thehive:
        try:
            created = await export_to_thehive(raw_events)
            result["thehive_cases_created"] = created
        except Exception as e:
            logger.warning("TheHive export failed: %s", e)
            result["thehive_error"] = str(e)

    # Optional file injection → Wazuh agent → alerts
    if write_files:
        from pipelines.file_injector import (
            inject_suricata, inject_zeek,
            inject_velociraptor, inject_arkime,
        )
        targets = detect_targets_from_format(fmt)
        injected = {}
        for t in targets:
            try:
                if t == "suricata":
                    injected[t] = inject_suricata(raw_events)
                elif t == "zeek":
                    injected[t] = inject_zeek(raw_events)
                elif t == "velociraptor":
                    injected[t] = inject_velociraptor(raw_events)
                elif t == "arkime":
                    injected[t] = inject_arkime(raw_events)
            except Exception as e:
                logger.warning("Injection for %s failed: %s", t, e)
                injected[t] = f"error: {e}"
        result["injected"] = injected

    return result


@app.api_route("/simulate/inject", methods=["GET", "POST"])
async def inject_events(
    total: int = Query(default=50, description="Events to generate and inject"),
    campaign_id: str = Query(default="", description="Override campaign ID"),
    target: str = Query(default="all", description="Target: all, suricata, zeek, velociraptor, arkime"),
    format: str = Query(default="json", description="Output format for returned event data: json, ndjson, wazuh, suricata, zeek, velociraptor, osquery, all"),
):
    """Generate events, inject them into Wazuh-monitored log files, and return
    the formatted event data.

    Writes synthetic Suricata eve.json, Zeek logs, Velociraptor events.json,
    and Arkime sessions.log entries to the actual filesystem paths that the
    Wazuh agent monitors.  This triggers analysisd → rules → alerts visible
    in the Wazuh dashboard (30-60s delay).

    Requires write access to ``sensors/`` log directories.
    """
    cid = campaign_id or str(uuid.uuid4())[:8]
    set_campaign_id(cid)
    _init_generators(cid)
    dist = get_attack_distribution()
    raw_events = _generate_all(dist, total)

    targets = ["suricata", "zeek", "velociraptor", "arkime"] if target == "all" else [target]
    injection_results = {}

    for t in targets:
        if t == "all":
            continue
        if t == "suricata":
            from pipelines.file_injector import inject_suricata
            injection_results["suricata"] = inject_suricata(raw_events)
        elif t == "velociraptor":
            from pipelines.file_injector import inject_velociraptor
            injection_results["velociraptor"] = inject_velociraptor(raw_events)
        elif t == "arkime":
            from pipelines.file_injector import inject_arkime
            injection_results["arkime"] = inject_arkime(raw_events)
        elif t == "zeek":
            from pipelines.file_injector import inject_zeek
            injection_results["zeek"] = inject_zeek(raw_events)

    if "suricata" not in injection_results and "zeek" not in injection_results and "velociraptor" not in injection_results and "arkime" not in injection_results:
        injection_results = inject_all(raw_events)

    fmt = format.lower()
    formatted = {}
    if fmt == "all":
        formatted = {
            "wazuh": format_wazuh_ndjson(raw_events),
            "suricata": format_suricata_ndjson(raw_events),
            "zeek_conn": format_zeek_ndjson(raw_events, "conn"),
            "zeek_http": format_zeek_ndjson(raw_events, "http"),
            "zeek_dns": format_zeek_ndjson(raw_events, "dns"),
            "velociraptor": format_velociraptor_ndjson(raw_events),
            "osquery": format_osquery_ndjson(raw_events),
        }
    elif fmt == "wazuh":
        formatted["events"] = format_wazuh_batch(raw_events)
    elif fmt == "suricata":
        formatted["events"] = format_suricata_batch(raw_events)
    elif fmt == "zeek":
        formatted["conn"] = format_zeek_batch(raw_events, "conn")
        formatted["http"] = format_zeek_batch(raw_events, "http")
        formatted["dns"] = format_zeek_batch(raw_events, "dns")
    elif fmt == "velociraptor":
        formatted["events"] = format_velociraptor_batch(raw_events)
    elif fmt == "osquery":
        formatted["events"] = format_osquery_batch(raw_events)
    elif fmt == "ndjson":
        formatted["data"] = build_dataset(raw_events, ["ndjson"])["ndjson"]
    else:
        formatted["events"] = build_normalized_json(raw_events)

    logger.info("Injection complete: %s", injection_results)
    return {
        "campaign_id": cid,
        "events_generated": len(raw_events),
        "injection_results": injection_results,
        "formatted": formatted,
        "note": "Alerts may take 30-60s to appear in the Wazuh dashboard after injection",
    }


@app.post("/simulate/campaign")
async def run_campaign(
    total: int = Query(5000, description="Total events across all waves"),
    waves: int = Query(5, description="Number of attack waves"),
    interval_seconds: int = Query(60, description="Seconds between waves"),
    format: str = Query("json", description="Output format"),
):
    """Run a time-based multi-wave attack campaign with escalating intensity."""
    results = []
    wave_size = total // waves
    for wave in range(waves):
        cid = f"campaign-wave-{wave+1}-{uuid.uuid4().hex[:6]}"
        logger.info("Wave %d/%d — %s — generating %d events", wave + 1, waves, cid, wave_size)
        dist = get_attack_distribution()
        set_campaign_id(cid)
        _init_generators(cid)
        raw_events = _generate_all(dist, wave_size)
        result = {
            "wave": wave + 1,
            "campaign_id": cid,
            "events_generated": len(raw_events),
            "events": build_normalized_json(raw_events)[:10],  # sample
        }
        results.append(result)
        if wave < waves - 1:
            await asyncio.sleep(interval_seconds)
    return {"total_waves": waves, "total_events": sum(r["events_generated"] for r in results), "results": results}


@app.get("/simulate/status")
async def status():
    """Show current simulation configuration and generator state."""
    cfg = get_config()
    dist = get_attack_distribution()
    gen_info = {}
    for name, gen in GENERATORS.items():
        gen_info[name] = {"events_generated": gen._event_counter, "class": type(gen).__name__}
    return {
        "campaign_id": get_campaign_id(),
        "attack_distribution": dist,
        "total_config_events": cfg.get("simulation", {}).get("total_events", 1000),
        "generators": gen_info,
        "config_path": str(Path(__file__).parent / "config" / "attack_profiles.yaml"),
    }


@app.post("/simulate/config")
async def update_config(config: Dict[str, Any] = Body(...)):
    """Update attack distribution at runtime.  Accepts partial updates."""
    try:
        cfg = get_config()
        if "attack_distribution" in config:
            cfg["attack_distribution"] = config["attack_distribution"]
        if "simulation" in config:
            cfg.setdefault("simulation", {}).update(config["simulation"])
        if "ioc_pools" in config:
            cfg.setdefault("ioc_pools", {}).update(config["ioc_pools"])
        cfg_path = Path(__file__).parent / "config" / "attack_profiles.yaml"
        with open(cfg_path, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False)
        _init_generators()
        return {"status": "updated", "attack_distribution": get_attack_distribution()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/simulate/dataset/{format}")
async def download_dataset(
    total: int = Query(1000),
    format: str = "ndjson",
):
    """Download a generated dataset file."""
    raw_events = _generate_all(get_attack_distribution(), total)
    ds = build_dataset(raw_events, [format])
    content = ds.get(format, "")
    media_type = "application/json"
    if format == "csv":
        media_type = "text/csv"
    elif format == "ndjson":
        media_type = "application/x-ndjson"
    return JSONResponse(content={"format": format, "size": len(content), "data": content})


# --------------------------------------------------------------------------- #
# CLI entrypoint                                                               #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("SIMULATION_ENGINE_PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

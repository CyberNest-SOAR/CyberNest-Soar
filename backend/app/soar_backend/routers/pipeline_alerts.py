import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from schemas.models import UnifiedAlert, HostContext, EnrichmentData, SocReasoningData
from services.normalizer import normalizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline-alerts", tags=["Pipeline Alerts"])

OUTPUTS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "dataset_pipeline" / "data" / "outputs"

def _get_latest_ndjson():
    files = sorted(OUTPUTS_DIR.glob("soc_dataset_*.ndjson"))
    if not files:
        return None
    return files[-1]

def _pipeline_event_to_unified_alert(event: dict) -> UnifiedAlert:
    event_id = event.get("event_id", "unknown")
    source = event.get("dataset_source", "pipeline")
    ts_str = event.get("timestamp")
    try:
        timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00")) if ts_str else datetime.now(timezone.utc)
    except (ValueError, AttributeError):
        timestamp = datetime.now(timezone.utc)

    description = event.get("alert_signature", "Pipeline Alert")
    severity = event.get("alert_severity", 3)
    src_ip = event.get("src_ip", "unknown")
    dst_ip = event.get("dst_ip", "unknown")

    host_context = HostContext(
        hostname=event.get("hostname") or event.get("process_name", "unknown"),
        ip_address=src_ip if src_ip != "unknown" else dst_ip,
    )

    enrichment_data = EnrichmentData(
        tags=[
            t for t in [
                event.get("attack_type"),
                event.get("mitre_tactic"),
                "pipeline",
            ] if t and t not in ("None", "")
        ],
    )

    epss = event.get("enrichment_epss_score")
    if epss is not None:
        enrichment_data.epss = {"score": float(epss)}
    cvss = event.get("enrichment_cvss_score")
    if cvss is not None:
        enrichment_data.nvd = {"cvss": float(cvss)}
    vt = event.get("enrichment_vt_score")
    if vt is not None:
        enrichment_data.virus_total = {"score": int(vt)}
    abuse = event.get("enrichment_abuse_score")
    if abuse is not None:
        enrichment_data.abuse_ipdb = {"score": int(abuse)}
    misp = event.get("enrichment_misp_matches")
    if misp:
        enrichment_data.misp = {"matches": misp, "count": len(misp)}
    risk = event.get("risk_adjusted_priority")
    if risk is not None:
        enrichment_data.risk_score = int(risk)

    # Build SOC reasoning data (pip line fields → SocReasoningData)
    mapping = {
        "asset_criticality": event.get("asset_criticality"),
        "analyst_verdict": event.get("analyst_verdict"),
        "analyst_notes": event.get("analyst_notes"),
        "analyst_assigned": event.get("analyst_assigned"),
        "escalation_level": event.get("escalation_level"),
        "playbook_outcome": event.get("playbook_outcome"),
        "suppression_hit": event.get("suppression_hit"),
        "true_positive": event.get("true_positive"),
        "noise": event.get("noise"),
        "mitre_technique_id": event.get("mitre_technique_id"),
        "mitre_technique_name": event.get("mitre_technique_name"),
        "mitre_tactic": event.get("mitre_tactic"),
        "attack_type": event.get("attack_type"),
        "campaign_id": event.get("campaign_id"),
        "cluster_id": event.get("cluster_id"),
        "confidence": event.get("confidence"),
        "risk_adjusted_priority": event.get("risk_adjusted_priority"),
        "asset_value": event.get("asset_value"),
        "host_role": event.get("host_role"),
        "department": event.get("department"),
        "business_unit": event.get("business_unit"),
        "owner_team": event.get("owner_team"),
        "user_role": event.get("user_role"),
        "environment_context": event.get("environment_context"),
        "closure_reason": event.get("closure_reason"),
        "repeated_behavior_score": event.get("repeated_behavior_score"),
        "similar_alerts_last_hour": event.get("similar_alerts_last_hour"),
        "historically_seen": event.get("historically_seen"),
        "historical_false_positive_rate": event.get("historical_false_positive_rate"),
        "recurring_alert": event.get("recurring_alert"),
        "prior_case_count": event.get("prior_case_count"),
        "timeline_position": event.get("timeline_position"),
        "remediation_action": event.get("remediation_action") or event.get("recommended_action") or event.get("playbook_action"),
        "dataset_source": event.get("dataset_source"),
    }
    # Filter out None values
    soc_kwargs = {k: v for k, v in mapping.items() if v is not None and v != "None"}

    return UnifiedAlert(
        event_id=event_id,
        source=source,
        timestamp=timestamp,
        description=description,
        severity=severity,
        host_context=host_context,
        raw_data=event,
        enrichment_data=enrichment_data,
        soc_reasoning=SocReasoningData(**soc_kwargs),
    )

@router.get("/")
async def get_pipeline_alerts(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    severity_min: Optional[int] = Query(None, ge=0, le=15),
    attack_type: Optional[str] = Query(None),
    source_filter: Optional[str] = Query(None, description="dataset_source filter"),
    enrich: bool = Query(False, description="Map pipeline enrichment into backend EnrichmentData"),
):
    latest = _get_latest_ndjson()
    if not latest:
        raise HTTPException(status_code=404, detail="No pipeline dataset found. Run the dataset pipeline first.")

    total = 0
    matched = 0
    alerts = []
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
            if len(alerts) >= limit:
                continue
            alerts.append(_pipeline_event_to_unified_alert(event))
            matched += 1

    return {
        "source": latest.name,
        "total_events": total,
        "returned": len(alerts),
        "offset": offset,
        "limit": limit,
        "alerts": [a.model_dump() for a in alerts],
    }

@router.get("/fields")
async def get_pipeline_fields():
    latest = _get_latest_ndjson()
    if not latest:
        raise HTTPException(status_code=404, detail="No pipeline dataset found")
    with open(latest) as f:
        first = f.readline().strip()
        if not first:
            raise HTTPException(status_code=404, detail="Empty dataset")
        event = json.loads(first)
    return {
        "source": latest.name,
        "total_fields": len(event),
        "field_names": sorted(event.keys()),
        "sample_event": event,
    }

@router.get("/sources")
async def get_pipeline_sources():
    latest = _get_latest_ndjson()
    if not latest:
        raise HTTPException(status_code=404, detail="No pipeline dataset found")
    sources = set()
    attack_types = set()
    severities = set()
    count = 0
    with open(latest) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            count += 1
            event = json.loads(line)
            ds = event.get("dataset_source")
            if ds:
                sources.add(ds)
            at = event.get("attack_type")
            if at:
                attack_types.add(at)
            sev = event.get("alert_severity")
            if sev is not None:
                severities.add(sev)
    return {
        "total_events": count,
        "dataset_sources": sorted(sources),
        "attack_types": sorted(attack_types),
        "severity_range": [min(severities), max(severities)] if severities else [],
    }

@router.post("/{event_id}/enrich")
async def enrich_pipeline_event(event_id: str):
    latest = _get_latest_ndjson()
    if not latest:
        raise HTTPException(status_code=404, detail="No pipeline dataset found")
    with open(latest) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            if event.get("event_id") == event_id:
                alert = _pipeline_event_to_unified_alert(event)
                return {
                    "event_id": event_id,
                    "original_enrichment": {
                        "vt_score": event.get("enrichment_vt_score"),
                        "abuse_score": event.get("enrichment_abuse_score"),
                        "misp_matches": event.get("enrichment_misp_matches"),
                        "epss_score": event.get("enrichment_epss_score"),
                    },
                    "mapped_enrichment": alert.enrichment_data.model_dump(exclude_none=True),
                    "soc_reasoning": alert.soc_reasoning.model_dump(exclude_none=True),
                }
    raise HTTPException(status_code=404, detail=f"Event {event_id} not found in pipeline dataset")

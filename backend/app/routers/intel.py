import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, Body
from typing import Dict, List, Any
from app.schemas.models import MispSyncResponse, UnifiedAlert, IntelResponse, IocLookupRequest, IocLookupResult, HostContext, EnrichmentData
from app.services.collector import collector
from app.services.enrichment import enrichment_service
from app.services.normalizer import normalizer
from app.services.intel import enrich_alert_intel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/threat-intel", tags=["Team 5: Threat Intel"])

@router.post("/lookup", response_model=IntelResponse)
async def intel_lookup(alert: UnifiedAlert):
    """
    Looks up IOCs from a UnifiedAlert in VirusTotal and MISP.
    """
    return await enrich_alert_intel(alert)


@router.post("/batch-lookup", response_model=List[IntelResponse])
async def intel_lookup_batch(alerts: List[UnifiedAlert]):
    """
    Enrich a batch of alerts with threat intel. Accepts the raw
    ``List[UnifiedAlert]`` array returned by ``GET /alerts/``.
    """
    results = await asyncio.gather(
        *[enrich_alert_intel(a) for a in alerts],
        return_exceptions=True,
    )
    out = []
    for alert, result in zip(alerts, results):
        if isinstance(result, Exception):
            logger.warning("[Intel] Batch enrichment failed for %s: %s", alert.event_id, result)
            out.append(IntelResponse(
                ioc=alert.host_context.ip_address or "unknown",
                malicious=False,
                reputation=100,
                sources=[],
            ))
        else:
            out.append(result)
    return out

@router.post("/lookup-ioc", response_model=IocLookupResult)
async def ioc_lookup(req: IocLookupRequest):
    """
    Look up a single IOC value against all configured threat intel providers.
    Constructs a minimal alert payload and runs the full enrichment pipeline.
    Returns per-source enrichment details suitable for the frontend IOC dialog.
    """
    raw_data: Dict[str, Any] = {}
    host_ip = "unknown"
    if req.ioc_type == "ip":
        host_ip = req.ioc
    elif req.ioc_type == "domain":
        raw_data["dns"] = {"query": req.ioc}
    elif req.ioc_type in ("hash", "url"):
        raw_data["fileinfo"] = {"md5": req.ioc} if len(req.ioc) == 32 else {}
        if req.ioc_type == "url":
            raw_data["url"] = req.ioc

    alert = UnifiedAlert(
        event_id=f"ioc-lookup-{req.ioc[:16]}",
        source="manual",
        timestamp=datetime.now(),
        description=f"Manual IOC lookup for {req.ioc} ({req.ioc_type})",
        severity=0,
        host_context=HostContext(hostname=host_ip, ip_address=host_ip),
        raw_data=raw_data,
    )

    await enrich_alert_intel(alert)

    enrichment: Dict[str, Any] = {}
    if alert.enrichment_data.virus_total:
        enrichment["virus_total"] = alert.enrichment_data.virus_total
    if alert.enrichment_data.abuse_ipdb:
        enrichment["abuse_ipdb"] = alert.enrichment_data.abuse_ipdb
    if alert.enrichment_data.misp:
        enrichment["misp"] = alert.enrichment_data.misp
    if alert.enrichment_data.urlhaus:
        enrichment["urlhaus"] = alert.enrichment_data.urlhaus
    if alert.enrichment_data.alienvault_otx:
        enrichment["alienvault_otx"] = alert.enrichment_data.alienvault_otx

    malicious = bool(enrichment.get("virus_total", {}).get("malicious", 0))
    sources = []
    if enrichment.get("virus_total"): sources.append("VirusTotal")
    if enrichment.get("abuse_ipdb"): sources.append("AbuseIPDB")
    if enrichment.get("misp"): sources.append("MISP")
    if enrichment.get("urlhaus"): sources.append("URLhaus")
    if enrichment.get("alienvault_otx"): sources.append("AlienVault OTX")

    return IocLookupResult(
        ioc=req.ioc,
        malicious=malicious,
        reputation=100 if not malicious else 0,
        sources=sources,
        enrichment=enrichment,
    )


@router.post("/misp-sync", response_model=MispSyncResponse)
async def misp_sync():
    """
    Syncs recent OpenSearch hits with MISP explicitly.
    """
    raw_data = await collector.query_opensearch(query={"size": 50, "query": {"match_all": {}}})
    hits = raw_data.get("hits", {}).get("hits", [])
    
    synced_events = 0
    synced_list = []
    
    for hit in hits:
        alert = normalizer.from_wazuh(hit)
        ip = alert.host_context.ip_address
        if ip and ip != "unknown":
            results = await enrichment_service.search_misp_async(ip)
            if results:
                synced_events += 1
                synced_list.append({"event_id": alert.event_id, "ip": ip, "misp_matches": len(results)})
                
    return MispSyncResponse(
        status="success",
        synced_events=synced_events,
        events=synced_list
    )

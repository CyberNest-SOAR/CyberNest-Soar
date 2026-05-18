from fastapi import APIRouter, Body
from schemas.models import MispSyncResponse, UnifiedAlert, IntelResponse
from services.collector import collector
from services.enrichment import enrichment_service
from services.normalizer import normalizer
from services.intel import enrich_alert_intel

router = APIRouter(prefix="/threat-intel", tags=["Team 5: Threat Intel"])

@router.post("/lookup", response_model=IntelResponse)
async def intel_lookup(alert: UnifiedAlert):
    """
    Looks up IOCs from a UnifiedAlert in VirusTotal and MISP.
    """
    return await enrich_alert_intel(alert)

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

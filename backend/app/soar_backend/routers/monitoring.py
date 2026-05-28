import asyncio
import logging
from fastapi import APIRouter
from services.collector import collector
from services.enrichment import enrichment_service
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/end-point-health", tags=["Monitoring"])

@router.get("/")
async def end_point_health():
    results = {}

    os_status = False
    try:
        response = await collector.client.get(
            f"{settings.OS_HOST}/_cluster/health",
            auth=collector.os_auth,
        )
        if response.status_code == 200:
            os_status = True
            os_data = response.json()
            results["opensearch"] = {
                "status": "connected",
                "cluster": os_data.get("cluster_name", "unknown"),
                "cluster_status": os_data.get("status", "unknown"),
                "nodes": os_data.get("number_of_nodes", 0),
            }
    except Exception as e:
        results["opensearch"] = {"status": "disconnected", "error": str(e)}

    try:
        response = await enrichment_service.client.get(
            f"{settings.MISP_URL}/users/view/me",
            headers={"Authorization": settings.MISP_KEY, "Accept": "application/json"},
            timeout=2.0,
        )
        if response.status_code == 200:
            results["misp"] = {"status": "connected"}
        else:
            results["misp"] = {"status": "error", "http_code": response.status_code}
    except Exception as e:
        results["misp"] = {"status": "disconnected", "error": str(e)}

    for name, key in [
        ("virustotal", settings.VT_API_KEY),
        ("abuseipdb", settings.ABUSE_KEY),
        ("alienvault_otx", settings.OTX_API_KEY),
        ("urlhaus", settings.URLHAUS_API_KEY),
    ]:
        results[name] = {"configured": bool(key) and key not in ("", "VT_API_KEY", "ABUSE_API_KEY")}

    try:
        response = await asyncio.wait_for(
            collector.client.get(f"{settings.WAZUH_URL}/agents", headers={"Authorization": f"Bearer {settings.WAZUH_KEY}"}),
            timeout=2.0,
        )
        if response.status_code == 200:
            results["wazuh"] = {"status": "connected"}
        else:
            results["wazuh"] = {"status": "error", "http_code": response.status_code}
    except Exception as e:
        results["wazuh"] = {"status": "disconnected", "error": str(e)}

    return results

@router.get("/status")
async def monitoring_status():
    return {
        "service": "SOAR Backend",
        "version": "1.0.0",
        "monitoring_endpoint": "/api/v1/end-point-health",
        "description": "Endpoint health monitoring for all SOAR services",
    }

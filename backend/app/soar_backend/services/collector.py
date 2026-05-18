"""
services/collector.py — Data ingestion layer.

All outbound HTTP calls are wrapped in ``asyncio.wait_for(timeout=2.0)``
so that an unreachable OpenSearch / Wazuh / Velociraptor instance never
blocks the caller longer than 2 seconds.  Safe defaults are returned on
timeout or error (**Fail-Soft** pattern).
"""

import asyncio
import httpx
import logging
from typing import Dict, Any, List
from core.config import settings

logger = logging.getLogger(__name__)

# Global timeout applied to every external call (seconds).
_API_TIMEOUT: float = 2.0


class DataCollector:
    def __init__(self):
        self.os_host = settings.OS_HOST
        self.os_auth = tuple(settings.OS_AUTH.split(':')) if ':' in settings.OS_AUTH else None
        self.wazuh_key = settings.WAZUH_KEY
        self.client = None

    async def start(self):
        if not self.client:
            self.client = httpx.AsyncClient(verify=False)

    async def stop(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def query_opensearch(
        self,
        index: str = "wazuh-alerts-*",
        query: Dict[str, Any] = None,
        limit: int = 10,
        offset: int = 0,
        severity: int = None,
    ) -> Dict[str, Any]:
        if not query:
            # Build DSL query with optional severity filter
            if severity is not None:
                dsl_query = {
                    "term": {"rule.level": severity}
                }
            else:
                dsl_query = {"match_all": {}}

            query = {
                "size": limit,
                "from": offset,
                "query": dsl_query,
                "sort": [{"@timestamp": {"order": "desc"}}],
            }

        await self.start()
        url = f"{self.os_host}/{index}/_search"

        kwargs = {"json": query}
        if self.os_auth:
            kwargs["auth"] = self.os_auth

        try:
            response = await asyncio.wait_for(
                self.client.post(url, **kwargs),
                timeout=_API_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except asyncio.TimeoutError:
            logger.warning("OpenSearch query timed out")
            return {"hits": {"hits": []}}
        except Exception:
            return {"hits": {"hits": []}}

    async def fetch_wazuh_agent(self, agent_id: str) -> Dict[str, Any]:
        await self.start()
        url = f"https://wazuh.local/agents/{agent_id}"
        headers = {"Authorization": f"Bearer {self.wazuh_key}"}
        try:
            response = await asyncio.wait_for(
                self.client.get(url, headers=headers),
                timeout=_API_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except asyncio.TimeoutError:
            logger.warning("Wazuh agent lookup timed out for %s", agent_id)
            return {"id": agent_id, "status": "unknown"}
        except Exception:
            return {"id": agent_id, "status": "unknown"}

    async def pull_velociraptor_snapshot(self, host_id: str) -> Dict[str, Any]:
        await self.start()
        url = f"https://velociraptor.local/api/v1/snapshot/{host_id}"
        try:
            response = await asyncio.wait_for(
                self.client.get(url),
                timeout=_API_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except asyncio.TimeoutError:
            logger.warning("Velociraptor snapshot timed out for %s", host_id)
            return {"host_id": host_id, "snapshot": "unavailable"}
        except Exception:
            return {"host_id": host_id, "snapshot": "unavailable"}

collector = DataCollector()
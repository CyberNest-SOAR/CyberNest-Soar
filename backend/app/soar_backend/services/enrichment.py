"""
services/enrichment.py — Centralised external-API enrichment helpers.

Every outbound call is wrapped in ``asyncio.wait_for(timeout=5.0)`` so that
a single slow or offline upstream (VT, AbuseIPDB, NVD, EPSS, MISP) can
never stall the entire pipeline.  Each method catches *all* exceptions and
returns a safe default, giving callers a **Fail-Soft Parallel** guarantee.

All lookups now emit structured log messages so enrichment results are
visible in the application logs for debugging and audit purposes.
"""

import httpx
import asyncio
import logging
from typing import Dict, Any, List
from async_lru import alru_cache
from core.config import settings
from pymisp import PyMISP

logger = logging.getLogger(__name__)

# Global timeout applied to every external API call (seconds).
_API_TIMEOUT: float = 5.0


class EnrichmentService:
    def __init__(self):
        self.vt_key = settings.VT_API_KEY
        self.abuse_key = settings.ABUSE_KEY
        self.misp_url = settings.MISP_URL
        self.misp_key = settings.MISP_KEY
        self.client = None
        # Disable SSL verification for MISP locally if needed by passing False
        try:
            self.misp = PyMISP(self.misp_url, self.misp_key, False)
            logger.info("MISP client initialised for %s", self.misp_url)
        except Exception as exc:
            logger.warning("MISP client init failed: %s — MISP lookups will be disabled", exc)
            self.misp = None

    async def start(self):
        if not self.client:
            self.client = httpx.AsyncClient(verify=False, timeout=_API_TIMEOUT)
            logger.info("EnrichmentService HTTP client started")

    async def stop(self):
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.info("EnrichmentService HTTP client stopped")

    # ------------------------------------------------------------------ #
    # VirusTotal                                                          #
    # ------------------------------------------------------------------ #
    @alru_cache(maxsize=128, ttl=300)
    async def lookup_virustotal(self, ioc: str) -> Dict[str, Any]:
        """
        Uses the VT IP report endpoint which returns a single object with
        ``data.attributes.last_analysis_stats`` — more reliable than /search.
        Falls back to the search endpoint for non-IP IOCs (domains, hashes).
        """
        await self.start()
        headers = {"x-apikey": self.vt_key}
        # Prefer the direct IP report endpoint for IP addresses
        try:
            import ipaddress
            ipaddress.ip_address(ioc)  # raises ValueError if not an IP
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ioc}"
        except ValueError:
            url = f"https://www.virustotal.com/api/v3/search?query={ioc}"

        logger.info("[VT] Starting lookup for IOC: %s → %s", ioc, url)
        try:
            response = await asyncio.wait_for(
                self.client.get(url, headers=headers),
                timeout=_API_TIMEOUT,
            )
            status = response.status_code
            if status != 200:
                logger.warning("[VT] Non-200 response for %s: HTTP %d — %s", ioc, status, response.text[:300])
                return {"_http_status": status, "_error": response.text[:500]}
            data = response.json()
            data["_http_status"] = status
            data["_response_preview"] = str(data)[:300]
            # Log a meaningful summary instead of the full payload
            if "data" in data:
                if isinstance(data["data"], dict):
                    stats = data["data"].get("attributes", {}).get("last_analysis_stats", {})
                    logger.info("[VT] ✓ Result for %s: analysis_stats=%s", ioc, stats)
                elif isinstance(data["data"], list):
                    logger.info("[VT] ✓ Result for %s: %d items returned", ioc, len(data["data"]))
                else:
                    logger.info("[VT] ✓ Result for %s: data type=%s", ioc, type(data["data"]).__name__)
            else:
                logger.warning("[VT] Response for %s has no 'data' key. Keys: %s", ioc, list(data.keys()))
            return data
        except asyncio.TimeoutError:
            logger.warning("[VT] ✗ Lookup TIMED OUT for %s (limit=%ss)", ioc, _API_TIMEOUT)
            return {"_http_status": 0, "_error": "timeout"}
        except Exception as exc:
            logger.warning("[VT] ✗ Lookup FAILED for %s: %s", ioc, exc)
            return {"_http_status": 0, "_error": str(exc)}

    # ------------------------------------------------------------------ #
    # AbuseIPDB                                                           #
    # ------------------------------------------------------------------ #
    @alru_cache(maxsize=128, ttl=300)
    async def lookup_abuseipdb(self, ip: str) -> Dict[str, Any]:
        await self.start()
        headers = {"Key": self.abuse_key, "Accept": "application/json"}
        params = {"ipAddress": ip, "maxAgeInDays": "90", "verbose": ""}
        url = "https://api.abuseipdb.com/api/v2/check"

        logger.info("[AbuseIPDB] Starting lookup for IP: %s", ip)
        try:
            response = await asyncio.wait_for(
                self.client.get(url, headers=headers, params=params),
                timeout=_API_TIMEOUT,
            )
            status = response.status_code
            if status != 200:
                logger.warning("[AbuseIPDB] Non-200 response for %s: HTTP %d — %s", ip, status, response.text[:300])
                return {"_http_status": status, "_error": response.text[:500]}
            data = response.json()
            data["_http_status"] = status
            data["_response_preview"] = str(data)[:300]
            if "data" in data:
                abuse_score = data["data"].get("abuseConfidenceScore")
                total_reports = data["data"].get("totalReports", 0)
                logger.info(
                    "[AbuseIPDB] ✓ Result for %s: abuseConfidenceScore=%s, totalReports=%s",
                    ip, abuse_score, total_reports,
                )
            else:
                logger.warning("[AbuseIPDB] Response for %s has no 'data' key. Keys: %s", ip, list(data.keys()))
            return data
        except asyncio.TimeoutError:
            logger.warning("[AbuseIPDB] ✗ Lookup TIMED OUT for %s (limit=%ss)", ip, _API_TIMEOUT)
            return {"_http_status": 0, "_error": "timeout"}
        except Exception as exc:
            logger.warning("[AbuseIPDB] ✗ Lookup FAILED for %s: %s", ip, exc)
            return {"_http_status": 0, "_error": str(exc)}

    # ------------------------------------------------------------------ #
    # EPSS                                                                #
    # ------------------------------------------------------------------ #
    @alru_cache(maxsize=128, ttl=300)
    async def lookup_epss(self, cve: str) -> Dict[str, Any]:
        await self.start()
        url = f"https://api.first.org/data/v1/epss?cve={cve}"
        logger.info("[EPSS] Starting lookup for CVE: %s", cve)
        try:
            response = await asyncio.wait_for(
                self.client.get(url),
                timeout=_API_TIMEOUT,
            )
            status = response.status_code
            if status != 200:
                logger.warning("[EPSS] Non-200 response for %s: HTTP %d", cve, status)
                return {"_http_status": status, "_error": response.text[:500]}
            data = response.json()
            data["_http_status"] = status
            data["_response_preview"] = str(data)[:300]
            epss_data = data.get("data", [])
            if epss_data:
                logger.info("[EPSS] ✓ Result for %s: epss=%s, percentile=%s",
                            cve,
                            epss_data[0].get("epss") if isinstance(epss_data, list) and epss_data else "N/A",
                            epss_data[0].get("percentile") if isinstance(epss_data, list) and epss_data else "N/A")
            else:
                logger.warning("[EPSS] Response for %s returned empty data", cve)
            return data
        except asyncio.TimeoutError:
            logger.warning("[EPSS] ✗ Lookup TIMED OUT for %s (limit=%ss)", cve, _API_TIMEOUT)
            return {"_http_status": 0, "_error": "timeout"}
        except Exception as exc:
            logger.warning("[EPSS] ✗ Lookup FAILED for %s: %s", cve, exc)
            return {"_http_status": 0, "_error": str(exc)}

    # ------------------------------------------------------------------ #
    # NVD                                                                 #
    # ------------------------------------------------------------------ #
    @alru_cache(maxsize=128, ttl=300)
    async def lookup_nvd(self, cve: str) -> Dict[str, Any]:
        await self.start()
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve}"
        logger.info("[NVD] Starting lookup for CVE: %s", cve)
        try:
            response = await asyncio.wait_for(
                self.client.get(url),
                timeout=_API_TIMEOUT,
            )
            status = response.status_code
            if status != 200:
                logger.warning("[NVD] Non-200 response for %s: HTTP %d", cve, status)
                return {"_http_status": status, "_error": response.text[:500]}
            data = response.json()
            data["_http_status"] = status
            data["_response_preview"] = str(data)[:300]
            vulns = data.get("vulnerabilities", [])
            logger.info("[NVD] ✓ Result for %s: %d vulnerabilities returned", cve, len(vulns))
            return data
        except asyncio.TimeoutError:
            logger.warning("[NVD] ✗ Lookup TIMED OUT for %s (limit=%ss)", cve, _API_TIMEOUT)
            return {"_http_status": 0, "_error": "timeout"}
        except Exception as exc:
            logger.warning("[NVD] ✗ Lookup FAILED for %s: %s", cve, exc)
            return {"_http_status": 0, "_error": str(exc)}

    # ------------------------------------------------------------------ #
    # MISP (sync PyMISP → thread pool → asyncio)                         #
    # ------------------------------------------------------------------ #
    def _sync_search_misp(self, value: str) -> List[Dict[str, Any]]:
        if not self.misp:
            logger.warning("[MISP] Client not initialised — skipping lookup for %s", value)
            return []
        try:
            results = self.misp.search(value=value)
            logger.info("[MISP] ✓ Sync search returned %d events for %s", len(results) if results else 0, value)
            return results
        except Exception as exc:
            logger.warning("[MISP] ✗ Sync search FAILED for %s: %s", value, exc)
            return []

    async def search_misp_async(self, value: str) -> List[Dict[str, Any]]:
        """Run the blocking PyMISP search in a thread, capped at _API_TIMEOUT."""
        logger.info("[MISP] Starting async lookup for: %s", value)
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self._sync_search_misp, value),
                timeout=_API_TIMEOUT,
            )
            logger.info("[MISP] ✓ Async lookup complete for %s: %d events", value, len(result) if result else 0)
            return result
        except asyncio.TimeoutError:
            logger.warning("[MISP] ✗ Lookup TIMED OUT for %s (limit=%ss)", value, _API_TIMEOUT)
            return []
        except Exception as exc:
            logger.warning("[MISP] ✗ Lookup FAILED for %s: %s", value, exc)
            return []

enrichment_service = EnrichmentService()

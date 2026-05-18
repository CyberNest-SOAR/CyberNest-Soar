"""
services/intel.py — Team 5: Threat Intel enrichment helper.

Provides ``enrich_alert_intel`` which is called by the /threat-intel/lookup
router.  It runs VT, AbuseIPDB, and MISP concurrently and returns an
``IntelResponse`` summary.  It also directly mutates ``alert.enrichment_data``
so callers that pass a live UnifiedAlert get the side-effect for free.

**Deep Monitoring (Data Trip):**
  - Outgoing: logs the IP and service being called.
  - Incoming: logs raw HTTP status code and response snippet.
  - Mapping: logs exactly which value is assigned to the UnifiedAlert.

**CVE Extraction Engine:**
  - Scans ``alert.description`` and ``alert.raw_data`` for ``CVE-\\d{4}-\\d{4,}``
    and appends ``vuln:CVE-YYYY-XXXX`` tags.

Every enrichment_service method enforces a 5-second ``asyncio.wait_for``
internally, so this layer only uses ``asyncio.gather`` with
``return_exceptions=True`` to run them in parallel and handle per-service
failures independently (**Fail-Soft Parallel** architecture).
"""

import asyncio
import ipaddress
import logging
import re
from typing import List
from schemas.models import UnifiedAlert, IntelResponse
from services.enrichment import enrichment_service

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# CVE Extraction Engine                                                       #
# --------------------------------------------------------------------------- #
_CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}")


def extract_cves(alert: UnifiedAlert) -> List[str]:
    """Scan ``alert.description`` and ``alert.raw_data`` for CVE identifiers.

    Appends matched CVEs as ``vuln:CVE-YYYY-XXXX`` tags to
    ``alert.enrichment_data.tags``.  Idempotent — will not re-add an
    already-present tag.

    Returns the list of unique CVE IDs found.
    """
    text = alert.description or ""
    if alert.raw_data:
        text += " " + str(alert.raw_data)
    raw_matches = _CVE_PATTERN.findall(text)
    seen: List[str] = []
    for cve in raw_matches:
        if cve not in seen:
            seen.append(cve)
        tag = f"vuln:{cve}"
        if tag not in alert.enrichment_data.tags:
            alert.enrichment_data.tags.append(tag)
            logger.info("[CVE] Tagged alert %s with %s", alert.event_id, tag)
    return seen


async def _fetch_cve_scores(alert: UnifiedAlert, cves: List[str]) -> None:
    """Fetch EPSS and CVSS scores for every CVE, store the max values.

    Runs EPSS and NVD lookups concurrently for all CVEs found in the alert.
    Uses ``asyncio.gather`` with ``return_exceptions=True`` so a single
    failing lookup never blocks the rest.  Stores the **maximum** EPSS
    probability and CVSS base score across all CVEs.
    """
    if not cves:
        return

    logger.info("[CVE] Fetching EPSS/CVSS scores for %d CVEs on alert %s", len(cves), alert.event_id)

    epss_tasks = [enrichment_service.lookup_epss(cve) for cve in cves]
    nvd_tasks = [enrichment_service.lookup_nvd(cve) for cve in cves]

    epss_results, nvd_results = await asyncio.gather(
        asyncio.gather(*epss_tasks, return_exceptions=True),
        asyncio.gather(*nvd_tasks, return_exceptions=True),
    )

    max_epss = 0.0
    max_cvss = 0.0

    for cve, result in zip(cves, epss_results):
        if isinstance(result, Exception):
            alert.enrichment_data.debug_info.setdefault(f"epss_error_{cve}", str(result))
            continue
        try:
            data_list = result.get("data", [])
            if data_list and isinstance(data_list, list):
                epss_val = data_list[0].get("epss")
                if epss_val is not None:
                    max_epss = max(max_epss, float(epss_val))
        except (ValueError, TypeError, IndexError) as exc:
            alert.enrichment_data.debug_info.setdefault(f"epss_parse_error_{cve}", str(exc))

    for cve, result in zip(cves, nvd_results):
        if isinstance(result, Exception):
            alert.enrichment_data.debug_info.setdefault(f"nvd_error_{cve}", str(result))
            continue
        try:
            vulns = result.get("vulnerabilities", [])
            if vulns and isinstance(vulns, list):
                cve_data = vulns[0].get("cve", {})
                metrics = cve_data.get("metrics", {})
                for metric_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                    metric_list = metrics.get(metric_key, [])
                    if metric_list and isinstance(metric_list, list):
                        cvss_val = metric_list[0].get("cvssData", {}).get("baseScore")
                        if cvss_val is not None:
                            max_cvss = max(max_cvss, float(cvss_val))
                            break
        except (ValueError, TypeError, IndexError, KeyError) as exc:
            alert.enrichment_data.debug_info.setdefault(f"nvd_parse_error_{cve}", str(exc))

    if max_epss > 0.0:
        alert.enrichment_data.epss_score = max_epss
        logger.info("[CVE] EPSS score = %s for alert %s (across %d CVEs)", max_epss, alert.event_id, len(cves))
    if max_cvss > 0.0:
        alert.enrichment_data.cvss_score = int(max_cvss) if max_cvss.is_integer() else max_cvss
        logger.info("[CVE] CVSS score = %s for alert %s (across %d CVEs)", max_cvss, alert.event_id, len(cves))


# --------------------------------------------------------------------------- #
# IP helpers                                                                   #
# --------------------------------------------------------------------------- #
def _is_enrichable_ip(ip: str) -> bool:
    """Return True for valid, routable public IP addresses only."""
    if not ip or ip.strip().lower() in ("unknown", ""):
        return False
    try:
        addr = ipaddress.ip_address(ip.strip())
        return (
            not addr.is_private
            and not addr.is_loopback
            and not addr.is_link_local
            and not addr.is_multicast
            and not addr.is_reserved
            and not addr.is_unspecified
        )
    except ValueError:
        return False


# --------------------------------------------------------------------------- #
# Core enrichment                                                              #
# --------------------------------------------------------------------------- #
async def enrich_alert_intel(alert: UnifiedAlert) -> IntelResponse:
    """
    Enrich a single alert against VT, AbuseIPDB and MISP in parallel.

    Populates ``alert.enrichment_data`` as a side-effect and returns an
    ``IntelResponse`` summarising the findings.
    """
    ip = alert.host_context.ip_address

    # ---- Non-routable / private IP → safe defaults ----
    if not _is_enrichable_ip(ip):
        logger.info(
            "[Intel] Skipping enrichment for alert %s — IP '%s' is not a public/routable address; "
            "initialising enrichment_data with safe defaults.",
            alert.event_id, ip,
        )
        if alert.enrichment_data.vt_score is None:
            alert.enrichment_data.vt_score = 0
        if alert.enrichment_data.abuse_score is None:
            alert.enrichment_data.abuse_score = 100
        found_cves = extract_cves(alert)
        if found_cves:
            await _fetch_cve_scores(alert, found_cves)
        return IntelResponse(ioc=ip or "unknown", malicious=False, reputation=100, sources=[])

    logger.info("[Intel] Starting parallel enrichment for alert %s (IP: %s)", alert.event_id, ip)

    # ---- Monitor: Outgoing ----
    logger.info("[Monitor] Outgoing → VT | IP: %s", ip)
    logger.info("[Monitor] Outgoing → AbuseIPDB | IP: %s", ip)
    logger.info("[Monitor] Outgoing → MISP | IP: %s", ip)

    # ---- Parallel lookups ----
    vt_result, abuse_result, misp_result = await asyncio.gather(
        enrichment_service.lookup_virustotal(ip),
        enrichment_service.lookup_abuseipdb(ip),
        enrichment_service.search_misp_async(ip),
        return_exceptions=True,
    )

    malicious = False
    reputation = 100
    sources: list[str] = []

    # ------------------------------------------------------------------ #
    # VirusTotal                                                          #
    # ------------------------------------------------------------------ #
    try:
        if isinstance(vt_result, Exception):
            alert.enrichment_data.debug_info["vt_error"] = f"VT exception: {vt_result}"
            raise vt_result

        # Monitor: Incoming
        http_status = vt_result.get("_http_status", "?")
        preview = vt_result.get("_response_preview", str(vt_result)[:200])
        logger.info("[Monitor] Incoming ← VT | HTTP %s | preview: %s", http_status, preview)

        if http_status not in (200, 0, "?"):
            alert.enrichment_data.debug_info["vt_http_error"] = f"HTTP {http_status}"

        if vt_result and "data" in vt_result:
            data = vt_result["data"]
            if isinstance(data, dict):
                attrs = data.get("attributes", {})
            elif isinstance(data, list) and data:
                attrs = data[0].get("attributes", {})
            else:
                attrs = {}

            stats = attrs.get("last_analysis_stats", {})
            malicious_count = stats.get("malicious", 0)
            suspicious_count = stats.get("suspicious", 0)
            harmless_count = stats.get("harmless", 1)
            total = malicious_count + suspicious_count + harmless_count

            if total > 0:
                vt_score = int((malicious_count / total) * 100)
            else:
                vt_score = 0

            alert.enrichment_data.vt_score = vt_score
            logger.info("[Monitor] Mapping → vt_score = %s (alert %s)", vt_score, alert.event_id)

            if malicious_count > 0 or suspicious_count > 0:
                malicious = True
                reputation = max(0, 100 - vt_score)

            sources.append("VirusTotal")
            logger.info(
                "[Intel] VT for %s → vt_score=%s (mal=%s, sus=%s, harm=%s)",
                ip, vt_score, malicious_count, suspicious_count, harmless_count,
            )
        else:
            logger.warning("[Intel] VT returned empty/no-data for %s: %s", ip, type(vt_result).__name__)
    except Exception as exc:
        logger.warning("[Intel] VT enrichment failed for %s: %s", ip, exc)
        alert.enrichment_data.debug_info.setdefault("vt_error", str(exc))

    # ------------------------------------------------------------------ #
    # AbuseIPDB                                                           #
    # ------------------------------------------------------------------ #
    try:
        if isinstance(abuse_result, Exception):
            alert.enrichment_data.debug_info["abuse_error"] = f"AbuseIPDB exception: {abuse_result}"
            raise abuse_result

        # Monitor: Incoming
        http_status = abuse_result.get("_http_status", "?")
        preview = abuse_result.get("_response_preview", str(abuse_result)[:200])
        logger.info("[Monitor] Incoming ← AbuseIPDB | HTTP %s | preview: %s", http_status, preview)

        if http_status not in (200, 0, "?"):
            alert.enrichment_data.debug_info["abuse_http_error"] = f"HTTP {http_status}"

        if abuse_result and "data" in abuse_result:
            score = abuse_result["data"].get("abuseConfidenceScore")
            if score is not None:
                alert.enrichment_data.abuse_score = int(score)
                logger.info("[Monitor] Mapping → abuse_score = %s (alert %s)", int(score), alert.event_id)
                if score > 25:
                    malicious = True
                    reputation = min(reputation, max(0, 100 - int(score)))
                sources.append("AbuseIPDB")
                logger.info("[Intel] AbuseIPDB for %s → abuse_score=%s", ip, score)
            else:
                logger.warning("[Intel] AbuseIPDB for %s → 'abuseConfidenceScore' missing from data", ip)
        else:
            logger.warning("[Intel] AbuseIPDB returned empty/no-data for %s: %s", ip, type(abuse_result).__name__)
    except Exception as exc:
        logger.warning("[Intel] AbuseIPDB enrichment failed for %s: %s", ip, exc)
        alert.enrichment_data.debug_info.setdefault("abuse_error", str(exc))

    # ------------------------------------------------------------------ #
    # MISP                                                                 #
    # ------------------------------------------------------------------ #
    try:
        if isinstance(misp_result, Exception):
            alert.enrichment_data.debug_info["misp_error"] = f"MISP exception: {misp_result}"
            raise misp_result

        # Monitor: Incoming (MISP returns a list, not a dict)
        logger.info(
            "[Monitor] Incoming ← MISP | type=%s | count=%s",
            type(misp_result).__name__, len(misp_result) if misp_result else 0,
        )

        if misp_result:
            for event in misp_result:
                event_uuid = (
                    str(event.get("Event", {}).get("uuid", ""))
                    if isinstance(event, dict)
                    else str(getattr(event, "uuid", ""))
                )
                if event_uuid and event_uuid not in alert.enrichment_data.misp_matches:
                    alert.enrichment_data.misp_matches.append(event_uuid)

            if alert.enrichment_data.misp_matches:
                malicious = True
                reputation = 0
                if "misp_hit" not in alert.enrichment_data.tags:
                    alert.enrichment_data.tags.append("misp_hit")
                sources.append("MISP")
                logger.info(
                    "[Intel] MISP for %s → %d matches: %s",
                    ip, len(alert.enrichment_data.misp_matches),
                    alert.enrichment_data.misp_matches,
                )
                logger.info(
                    "[Monitor] Mapping → misp_matches = %s | tags includes 'misp_hit' (alert %s)",
                    alert.enrichment_data.misp_matches, alert.event_id,
                )
        else:
            logger.info("[Intel] MISP for %s → no matches", ip)
    except Exception as exc:
        logger.warning("[Intel] MISP enrichment failed for %s: %s", ip, exc)
        alert.enrichment_data.debug_info.setdefault("misp_error", str(exc))

    # ---- CVE Extraction & Score Fetching ----
    found_cves = extract_cves(alert)
    if found_cves:
        await _fetch_cve_scores(alert, found_cves)

    logger.info(
        "[Intel] ✓ Completed enrichment for alert %s — malicious=%s, reputation=%s, sources=%s",
        alert.event_id, malicious, reputation, sources,
    )

    return IntelResponse(
        ioc=ip,
        malicious=malicious,
        reputation=reputation,
        sources=sources,
    )

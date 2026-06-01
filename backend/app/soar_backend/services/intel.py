"""
services/intel.py — Team 5: Threat Intel enrichment helper.

Provides ``enrich_alert_intel`` which enriches an alert by extracting all
IOCs (IPs, domains, hashes, CVEs) from the alert data and running VT,
AbuseIPDB, MISP, EPSS, and NVD lookups concurrently.

**Multi-IOC Extraction:**
  - Scans ``raw_data`` for ``src_ip``, ``dest_ip``, HTTP hosts, DNS queries,
    TLS SNI, and file hashes.  Every public / routable IP is enriched against
    VT, AbuseIPDB, and MISP.
  - Extracts CVE identifiers from descriptions and raw data, then fetches
    EPSS probability and CVSS base scores.

Every enrichment_service method enforces a 5-second ``asyncio.wait_for``
internally, so this layer only uses ``asyncio.gather`` with
``return_exceptions=True`` to run them in parallel and handle per-service
failures independently (**Fail-Soft Parallel** architecture).
"""

import asyncio
import ipaddress
import logging
import re
<<<<<<< HEAD
from typing import List
from soar_backend.schemas.models import UnifiedAlert, IntelResponse
from soar_backend.services.enrichment import enrichment_service
=======
from typing import Dict, List, Set, Tuple
from schemas.models import UnifiedAlert, IntelResponse
from services.enrichment import enrichment_service
>>>>>>> 83a1eb822484b2645de5e14bd1f68707d0d07a8c

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# IOC Extraction                                                               #
# --------------------------------------------------------------------------- #
_CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}")
_HASH_PATTERN = re.compile(r"\b([a-f0-9]{32}|[a-f0-9]{40}|[a-f0-9]{64})\b")


def _extract_iocs(alert: UnifiedAlert) -> Dict[str, List[str]]:
    """Extract all IOCs (IPs, domains, hashes) from alert raw_data.

    Returns a dict keyed by IOC type: ``ips``, ``domains``, ``hashes``.
    """
    raw = alert.raw_data
    data = raw.get("data", {}) if isinstance(raw, dict) else {}

    ips: Set[str] = set()
    domains: Set[str] = set()
    hashes: Set[str] = set()

    # ---- IPs ----
    for field in ("src_ip", "dest_ip", "srcip", "dstip"):
        val = data.get(field)
        if val and isinstance(val, str) and val.strip().lower() not in ("", "unknown"):
            ips.add(val.strip())

    # Also check the alert host_context IP
    hip = alert.host_context.ip_address
    if hip and hip.lower() not in ("unknown", ""):
        ips.add(hip)

    # ---- Domains (DNS queries, HTTP hosts, TLS SNI) ----
    dns_data = data.get("dns", {})
    if isinstance(dns_data, dict):
        q = dns_data.get("query") or dns_data.get("rrname")
        if q and isinstance(q, str):
            domains.add(q.strip().rstrip("."))

    http_data = data.get("http", {})
    if isinstance(http_data, dict):
        host = http_data.get("host")
        if host and isinstance(host, str):
            domains.add(host.strip())

    tls_data = data.get("tls", {})
    if isinstance(tls_data, dict):
        sni = tls_data.get("sni")
        if sni and isinstance(sni, str):
            domains.add(sni.strip())

    # ---- Hashes ----
    fileinfo = data.get("fileinfo", {})
    if isinstance(fileinfo, dict):
        for hf in ("md5", "sha1", "sha256"):
            hv = fileinfo.get(hf)
            if hv and isinstance(hv, str) and _HASH_PATTERN.match(hv):
                hashes.add(hv.strip())

    # Scan full_log + description for hashes
    text = f"{raw.get('full_log', '')} {raw.get('description', '')} {raw.get('message', '')}"
    for m in _HASH_PATTERN.finditer(text):
        hashes.add(m.group(1))

    return {
        "ips": sorted(ips),
        "domains": sorted(domains),
        "hashes": sorted(hashes),
    }


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


def extract_cves(alert: UnifiedAlert) -> List[str]:
    """Scan ``alert.description``, ``alert.raw_data``, and structured
    ``data.vulnerability`` for CVE identifiers.

    Wazuh vulnerability detector writes CVEs under
    ``raw_data.data.vulnerability[].cve`` — this function explicitly
    extracts those in addition to regex-based scanning of text fields.

    Appends matched CVEs as ``vuln:CVE-YYYY-XXXX`` tags to
    ``alert.enrichment_data.tags``.  Idempotent — will not re-add an
    already-present tag.

    Returns the list of unique CVE IDs found.
    """
    seen: List[str] = []

    # 1. Structured extraction from Wazuh vulnerability data
    raw = alert.raw_data or {}
    data = raw.get("data", {}) if isinstance(raw, dict) else {}
    if isinstance(data, dict):
        vuln_list = data.get("vulnerability", [])
        if not isinstance(vuln_list, list):
            vuln_list = [vuln_list] if vuln_list else []
        for vuln in vuln_list:
            cve = vuln.get("cve") if isinstance(vuln, dict) else None
            if cve and _CVE_PATTERN.fullmatch(str(cve).strip()):
                if cve not in seen:
                    seen.append(cve)

    # 2. Regex-based extraction from description + raw_data string
    text = alert.description or ""
    if alert.raw_data:
        text += " " + str(alert.raw_data)
    for cve in _CVE_PATTERN.findall(text):
        if cve not in seen:
            seen.append(cve)

    # 3. Tag all found CVEs
    for cve in seen:
        tag = f"vuln:{cve}"
        if tag not in alert.enrichment_data.tags:
            alert.enrichment_data.tags.append(tag)
            logger.info("[CVE] Tagged alert %s with %s", alert.event_id, tag)
    return seen


async def _fetch_cve_scores(alert: UnifiedAlert, cves: List[str]) -> None:
    """Fetch EPSS, CVSS, and KEV status for every CVE, store the max values.

    Runs EPSS, NVD, and KEV lookups concurrently for all CVEs found in the alert.
    Uses ``asyncio.gather`` with ``return_exceptions=True`` so a single
    failing lookup never blocks the rest.  Stores the **maximum** EPSS
    probability and CVSS base score across all CVEs.
    """
    if not cves:
        return

    logger.info("[CVE] Fetching EPSS/CVSS/KEV scores for %d CVEs on alert %s", len(cves), alert.event_id)

    epss_tasks = [enrichment_service.lookup_epss(cve) for cve in cves]
    nvd_tasks = [enrichment_service.lookup_nvd(cve) for cve in cves]
    kev_tasks = [enrichment_service.lookup_kev(cve) for cve in cves]

    epss_results, nvd_results, kev_results = await asyncio.gather(
        asyncio.gather(*epss_tasks, return_exceptions=True),
        asyncio.gather(*nvd_tasks, return_exceptions=True),
        asyncio.gather(*kev_tasks, return_exceptions=True),
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
        alert.enrichment_data.epss = {"score": max_epss}
        logger.info("[CVE] EPSS score = %s for alert %s (across %d CVEs)", max_epss, alert.event_id, len(cves))
    if max_cvss > 0.0:
        severity = "CRITICAL" if max_cvss >= 9.0 else "HIGH" if max_cvss >= 7.0 else "MEDIUM" if max_cvss >= 4.0 else "LOW"
        alert.enrichment_data.nvd = {
            "cvss": int(max_cvss) if max_cvss.is_integer() else max_cvss,
            "severity": severity,
        }
        logger.info("[CVE] CVSS score = %s for alert %s (across %d CVEs)", max_cvss, alert.event_id, len(cves))

    # ---- CISA KEV check (first CVE found in KEV wins) ----
    if alert.enrichment_data.cisa_kev is None:
        for cve, result in zip(cves, kev_results):
            if isinstance(result, Exception):
                alert.enrichment_data.debug_info.setdefault(f"kev_error_{cve}", str(result))
                continue
            try:
                match = result.get("kev_match")
                if match:
                    alert.enrichment_data.cisa_kev = {
                        "cve": match.get("cveID"),
                        "date_added": match.get("dateAdded"),
                        "short_description": match.get("shortDescription"),
                        "required_action": match.get("requiredAction"),
                        "known_ransomware": match.get("knownRansomwareCampaignUse"),
                        "due_date": match.get("dueDate"),
                    }
                    logger.info("[KEV] CVE %s is in KEV catalog for alert %s", cve, alert.event_id)
                    if "kev" not in alert.enrichment_data.tags:
                        alert.enrichment_data.tags.append("kev")
                    # Only tag the first KEV match
                    break
            except (ValueError, TypeError, KeyError) as exc:
                alert.enrichment_data.debug_info.setdefault(f"kev_parse_error_{cve}", str(exc))


# --------------------------------------------------------------------------- #
# Multi-IP enrichment helpers                                                  #
# --------------------------------------------------------------------------- #
async def _enrich_single_ip(
    alert: UnifiedAlert, ip: str,
) -> Tuple[bool, int, List[str]]:
    """Run VT / AbuseIPDB / MISP lookups for a single IP.

    Mutates ``alert.enrichment_data`` in place.  Returns a tuple of
    ``(malicious, reputation, sources)`` for this IP.
    """
    logger.info("[Intel] Enriching IP %s for alert %s", ip, alert.event_id)
    logger.info("[Monitor] Outgoing → VT | IP: %s", ip)
    logger.info("[Monitor] Outgoing → AbuseIPDB | IP: %s", ip)
    logger.info("[Monitor] Outgoing → MISP | IP: %s", ip)
    logger.info("[Monitor] Outgoing → URLhaus (host) | IP: %s", ip)
    logger.info("[Monitor] Outgoing → OTX | IP: %s", ip)

    vt_result, abuse_result, misp_result, urlhaus_result, otx_result = await asyncio.gather(
        enrichment_service.lookup_virustotal(ip),
        enrichment_service.lookup_abuseipdb(ip),
        enrichment_service.search_misp_async(ip),
        enrichment_service.lookup_urlhaus(ip, ioc_type="host"),
        enrichment_service.lookup_otx(ip, ioc_type="IPv4"),
        return_exceptions=True,
    )

    malicious = False
    reputation = 100
    sources: List[str] = []

    # ---- VirusTotal ----
    try:
        if isinstance(vt_result, Exception):
            alert.enrichment_data.debug_info.setdefault("vt_error", str(vt_result))
            raise vt_result

        http_status = vt_result.get("_http_status", "?")
        preview = vt_result.get("_response_preview", str(vt_result)[:200])
        logger.info("[Monitor] Incoming ← VT | HTTP %s | preview: %s", http_status, preview)

        if http_status not in (200, 0, "?"):
            alert.enrichment_data.debug_info.setdefault("vt_http_error", f"HTTP {http_status} for {ip}")

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
            score = int((malicious_count / total) * 100) if total > 0 else 0

            current_vt = alert.enrichment_data.virus_total or {}
            alert.enrichment_data.virus_total = {
                "score": max(current_vt.get("score", 0), score),
                "malicious": malicious_count,
                "suspicious": suspicious_count,
                "harmless": harmless_count,
            }

            if malicious_count > 0 or suspicious_count > 0:
                malicious = True
                reputation = max(0, 100 - score)

            sources.append("VirusTotal")
            logger.info(
                "[Intel] VT for %s → score=%s (mal=%s, sus=%s, harm=%s)",
                ip, score, malicious_count, suspicious_count, harmless_count,
            )
        else:
            logger.warning("[Intel] VT returned empty/no-data for %s", ip)
    except Exception as exc:
        logger.warning("[Intel] VT enrichment failed for %s: %s", ip, exc)
        alert.enrichment_data.debug_info.setdefault("vt_error", str(exc))

    # ---- AbuseIPDB ----
    try:
        if isinstance(abuse_result, Exception):
            alert.enrichment_data.debug_info.setdefault("abuse_error", str(abuse_result))
            raise abuse_result

        http_status = abuse_result.get("_http_status", "?")
        preview = abuse_result.get("_response_preview", str(abuse_result)[:200])
        logger.info("[Monitor] Incoming ← AbuseIPDB | HTTP %s | preview: %s", http_status, preview)

        if http_status not in (200, 0, "?"):
            alert.enrichment_data.debug_info.setdefault("abuse_http_error", f"HTTP {http_status} for {ip}")

        if abuse_result and "data" in abuse_result:
            score = abuse_result["data"].get("abuseConfidenceScore")
            if score is not None:
                current_abuse = alert.enrichment_data.abuse_ipdb or {}
                alert.enrichment_data.abuse_ipdb = {
                    "score": max(current_abuse.get("score", 0), int(score)),
                    "total_reports": abuse_result["data"].get("totalReports", 0),
                }
                if score > 25:
                    malicious = True
                    reputation = min(reputation, max(0, 100 - int(score)))
                sources.append("AbuseIPDB")
                logger.info("[Intel] AbuseIPDB for %s → score=%s", ip, score)
            else:
                logger.warning("[Intel] AbuseIPDB for %s → 'abuseConfidenceScore' missing", ip)
        else:
            logger.warning("[Intel] AbuseIPDB returned empty/no-data for %s", ip)
    except Exception as exc:
        logger.warning("[Intel] AbuseIPDB enrichment failed for %s: %s", ip, exc)
        alert.enrichment_data.debug_info.setdefault("abuse_error", str(exc))

    # ---- MISP ----
    try:
        if isinstance(misp_result, Exception):
            alert.enrichment_data.debug_info.setdefault("misp_error", str(misp_result))
            raise misp_result

        logger.info(
            "[Monitor] Incoming ← MISP | type=%s | count=%s",
            type(misp_result).__name__, len(misp_result) if misp_result else 0,
        )

        if misp_result:
            matches = []
            for event in misp_result:
                event_uuid = (
                    str(event.get("Event", {}).get("uuid", ""))
                    if isinstance(event, dict)
                    else str(getattr(event, "uuid", ""))
                )
                if event_uuid:
                    matches.append(event_uuid)

            if matches:
                current_misp = alert.enrichment_data.misp or {}
                all_matches = list(set(current_misp.get("matches", []) + matches))
                alert.enrichment_data.misp = {
                    "matches": all_matches,
                    "count": len(all_matches),
                }
                malicious = True
                reputation = 0
                if "misp_hit" not in alert.enrichment_data.tags:
                    alert.enrichment_data.tags.append("misp_hit")
                sources.append("MISP")
                logger.info("[Intel] MISP for %s → %d matches", ip, len(matches))
        else:
            logger.info("[Intel] MISP for %s → no matches", ip)
    except Exception as exc:
        logger.warning("[Intel] MISP enrichment failed for %s: %s", ip, exc)
        alert.enrichment_data.debug_info.setdefault("misp_error", str(exc))

    # ---- URLhaus ----
    try:
        if isinstance(urlhaus_result, Exception):
            alert.enrichment_data.debug_info.setdefault("urlhaus_error", str(urlhaus_result))
            raise urlhaus_result

        http_status = urlhaus_result.get("_http_status", "?")
        logger.info("[Monitor] Incoming ← URLhaus | HTTP %s", http_status)

        if urlhaus_result.get("query_status") == "ok" and urlhaus_result.get("url_status") == "online":
            alert.enrichment_data.urlhaus = {
                "matched": True,
                "url_status": urlhaus_result.get("url_status"),
                "threat": urlhaus_result.get("threat"),
                "tags": urlhaus_result.get("tags", []),
                "date_added": urlhaus_result.get("date_added"),
            }
            malicious = True
            reputation = min(reputation, 0)
            if "urlhaus" not in alert.enrichment_data.tags:
                alert.enrichment_data.tags.append("urlhaus")
            sources.append("URLhaus")
            logger.info("[Intel] URLhaus for %s → malicious (status=%s)", ip, urlhaus_result.get("url_status"))
        else:
            logger.info("[Intel] URLhaus for %s → clean (query_status=%s)", ip, urlhaus_result.get("query_status"))
    except Exception as exc:
        logger.warning("[Intel] URLhaus enrichment failed for %s: %s", ip, exc)
        alert.enrichment_data.debug_info.setdefault("urlhaus_error", str(exc))

    # ---- AlienVault OTX ----
    try:
        if isinstance(otx_result, Exception):
            alert.enrichment_data.debug_info.setdefault("otx_error", str(otx_result))
            raise otx_result

        http_status = otx_result.get("_http_status", "?")
        logger.info("[Monitor] Incoming ← OTX | HTTP %s", http_status)

        pulse_info = otx_result.get("pulse_info", {})
        pulses = pulse_info.get("pulses", []) if pulse_info else []
        if pulses:
            alert.enrichment_data.alienvault_otx = {
                "matched": True,
                "indicator": otx_result.get("indicator"),
                "type": otx_result.get("type"),
                "reputation": otx_result.get("reputation"),
                "validation": otx_result.get("validation"),
                "pulse_count": len(pulses),
                "pulse_names": [p.get("name") for p in pulses if p.get("name")],
            }
            malicious = True
            reputation = min(reputation, max(0, 100 - len(pulses) * 10))
            if "otx" not in alert.enrichment_data.tags:
                alert.enrichment_data.tags.append("otx")
            sources.append("AlienVault OTX")
            logger.info("[Intel] OTX for %s → %d pulses matched", ip, len(pulses))
        else:
            logger.info("[Intel] OTX for %s → no pulses", ip)
    except Exception as exc:
        logger.warning("[Intel] OTX enrichment failed for %s: %s", ip, exc)
        alert.enrichment_data.debug_info.setdefault("otx_error", str(exc))

    return malicious, reputation, sources


# --------------------------------------------------------------------------- #
# Core enrichment                                                              #
# --------------------------------------------------------------------------- #
async def enrich_alert_intel(alert: UnifiedAlert) -> IntelResponse:
    """
    Extract all IOCs from an alert and enrich every public / routable IP
    against VT, AbuseIPDB, MISP, URLhaus, and AlienVault OTX in parallel.
    Also extracts CVE identifiers and fetches EPSS / CVSS scores + CISA KEV
    status.  Domains are enriched against URLhaus and OTX; hashes against OTX.

    Mutates ``alert.enrichment_data`` as a side-effect and returns an
    ``IntelResponse`` summarising the aggregated findings.

    **Multi-IOC support:** ``_extract_iocs`` pulls ``src_ip``, ``dest_ip``,
    HTTP hosts, DNS queries, TLS SNI, and file hashes from ``raw_data``.
    Every public IP is enriched independently; scores use the maximum across
    all checked IPs (most conservative).
    """
    iocs = _extract_iocs(alert)
    public_ips = [ip for ip in iocs["ips"] if _is_enrichable_ip(ip)]

    alert.enrichment_data.debug_info["iocs_extracted"] = iocs
    logger.info(
        "[Intel] Extracted IOCs for alert %s: %d IPs, %d domains, %d hashes (enrichable IPs: %s)",
        alert.event_id, len(iocs["ips"]), len(iocs["domains"]), len(iocs["hashes"]),
        public_ips,
    )

    malicious = False
    reputation = 100
    sources: List[str] = []

    # ---- Enrich all public IPs ----
    if public_ips:
        results = await asyncio.gather(
            *[_enrich_single_ip(alert, ip) for ip in public_ips],
            return_exceptions=True,
        )
        for ip, result in zip(public_ips, results):
            if isinstance(result, Exception):
                logger.warning("[Intel] _enrich_single_ip failed for %s: %s", ip, result)
                continue
            ip_malicious, ip_reputation, ip_sources = result
            if ip_malicious:
                malicious = True
                reputation = min(reputation, ip_reputation)
            for s in ip_sources:
                if s not in sources:
                    sources.append(s)
    else:
        logger.info(
            "[Intel] No public IPs to enrich for alert %s; setting safe defaults.",
            alert.event_id,
        )

    # ---- CVE Extraction & Score Fetching ----
    found_cves = extract_cves(alert)
    if found_cves:
        await _fetch_cve_scores(alert, found_cves)

    # ---- Domain Enrichment (URLhaus + OTX) ----
    for domain in iocs.get("domains", []):
        logger.info("[Intel] Enriching domain %s for alert %s", domain, alert.event_id)
        uh_result, otx_domain_result = await asyncio.gather(
            enrichment_service.lookup_urlhaus(domain, ioc_type="host"),
            enrichment_service.lookup_otx(domain, ioc_type="domain"),
            return_exceptions=True,
        )
        if not isinstance(uh_result, Exception) and uh_result.get("query_status") == "ok":
            alert.enrichment_data.urlhaus = {
                "matched": True,
                "host": domain,
                "url_status": uh_result.get("url_status"),
                "threat": uh_result.get("threat"),
                "tags": uh_result.get("tags", []),
            }
            malicious = True
            if "urlhaus" not in alert.enrichment_data.tags:
                alert.enrichment_data.tags.append("urlhaus")
            if "URLhaus" not in sources:
                sources.append("URLhaus")
            logger.info("[Intel] URLhaus domain match for %s", domain)
        if not isinstance(otx_domain_result, Exception):
            pulses = (otx_domain_result.get("pulse_info") or {}).get("pulses", [])
            if pulses:
                alert.enrichment_data.alienvault_otx = {
                    "matched": True,
                    "indicator": otx_domain_result.get("indicator"),
                    "type": otx_domain_result.get("type"),
                    "pulse_count": len(pulses),
                    "pulse_names": [p.get("name") for p in pulses if p.get("name")],
                }
                malicious = True
                if "otx" not in alert.enrichment_data.tags:
                    alert.enrichment_data.tags.append("otx")
                if "AlienVault OTX" not in sources:
                    sources.append("AlienVault OTX")
                logger.info("[Intel] OTX domain match for %s: %d pulses", domain, len(pulses))

    # ---- Hash Enrichment (OTX) ----
    for h in iocs.get("hashes", []):
        h_type = "SHA256" if len(h) == 64 else ("SHA1" if len(h) == 40 else "MD5")
        logger.info("[Intel] Enriching hash %s (%s) for alert %s", h, h_type, alert.event_id)
        otx_hash_result = await enrichment_service.lookup_otx(h, ioc_type=h_type)
        if not isinstance(otx_hash_result, Exception):
            pulses = (otx_hash_result.get("pulse_info") or {}).get("pulses", [])
            if pulses:
                malicious = True
                if "otx" not in alert.enrichment_data.tags:
                    alert.enrichment_data.tags.append("otx")
                if "AlienVault OTX" not in sources:
                    sources.append("AlienVault OTX")
                logger.info("[Intel] OTX domain match for %s: %d pulses", domain, len(pulses))

    # ---- Hash Enrichment (OTX) ----
    for h in iocs.get("hashes", []):
        h_type = "SHA256" if len(h) == 64 else ("SHA1" if len(h) == 40 else "MD5")
        logger.info("[Intel] Enriching hash %s (%s) for alert %s", h, h_type, alert.event_id)
        otx_hash_result = await enrichment_service.lookup_otx(h, ioc_type=h_type)
        if not isinstance(otx_hash_result, Exception):
            pulses = (otx_hash_result.get("pulse_info") or {}).get("pulses", [])
            if pulses:
                alert.enrichment_data.alienvault_otx = {
                    "matched": True,
                    "indicator": otx_hash_result.get("indicator"),
                    "type": h_type,
                    "pulse_count": len(pulses),
                    "pulse_names": [p.get("name") for p in pulses if p.get("name")],
                }
                malicious = True
                if "otx" not in alert.enrichment_data.tags:
                    alert.enrichment_data.tags.append("otx")
                if "AlienVault OTX" not in sources:
                    sources.append("AlienVault OTX")
                logger.info("[Intel] OTX hash match for %s: %d pulses", h, len(pulses))

    host_ip = alert.host_context.ip_address
    primary_ioc = host_ip if host_ip and host_ip.lower() not in ("", "unknown") else (public_ips or ["unknown"])[0]

    logger.info(
        "[Intel] ✓ Completed enrichment for alert %s — malicious=%s, reputation=%s, sources=%s, IOCs=%s",
        alert.event_id, malicious, reputation, sources, iocs,
    )

    return IntelResponse(
        ioc=primary_ioc,
        malicious=malicious,
        reputation=reputation,
        sources=sources,
    )

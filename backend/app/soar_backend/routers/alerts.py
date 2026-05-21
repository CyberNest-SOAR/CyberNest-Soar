"""
routers/alerts.py — Team 0: Core Data

Fetch and optionally enrich Wazuh alerts.  When ``enrich=true``, all
alerts are enriched **in parallel** via ``asyncio.gather``.  Within each
alert the three external lookups (VT, AbuseIPDB, MISP) also run in
parallel.  Every individual call is capped at 5 s and wrapped in a
try-except so that one slow / offline service never blocks or nullifies
the others (**Fail-Soft Parallel** architecture).

Batch-level protection: the entire gather uses ``return_exceptions=True``
so that a single failing enrichment never kills the rest.  Internal /
non-routable IPs are initialised with safe defaults (vt_score=0,
abuse_score=100) so ``enrichment_data`` is never null.

**Batch pipeline endpoints** (``/api/v1/alerts/batch/*``):
  Accept the raw ``List[UnifiedAlert]`` array returned by ``GET /alerts/``
  and run the full downstream pipeline — threat intel enrichment, patch
  recommendations, risk scoring, and LLM classification — so the output
  of one team's service can be piped directly into another's.
"""

import asyncio
import logging
from fastapi import APIRouter, Query, Body
from typing import List, Optional

from services.collector import collector
from services.normalizer import normalizer
from services.intel import enrich_alert_intel, extract_cves
from services.patch import get_patch_recommendations
from services.risk import calculate_risk_score
from services.filtering import classify_alert
from routers.filtering import prepare_llm_payload
from schemas.models import UnifiedAlert, IntelResponse, PatchResponse, RiskScoreResponse, FilterResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["Team 0: Core Data"])


async def _enrich_alert(alert: UnifiedAlert) -> UnifiedAlert:
    """
    Enrich a single alert via the intel pipeline.

    Delegates to ``enrich_alert_intel`` which handles monitoring,
    CVE extraction, and safe defaults internally.  The alert is
    mutated in-place and returned for gather result collection.
    """
    await enrich_alert_intel(alert)
    return alert


@router.get("/", response_model=List[UnifiedAlert])
async def fetch_alerts(
    limit: int = Query(100, ge=1, description="Number of alerts to fetch"),
    offset: int = Query(0, alias="from", ge=0, description="Number of alerts to skip"),
    severity: Optional[int] = Query(
        None, ge=1, le=15, description="Filter by Wazuh rule level"
    ),
    enrich: bool = Query(
        False, description="Enrich alerts with external intelligence (VT, AbuseIPDB, MISP)"
    ),
    vuln: Optional[bool] = Query(
        None, description="Filter to alerts with CVE vulnerability data (implies enrich=true). "
        "false = only alerts without CVEs, true = only alerts with CVEs"
    ),
):
    """
    Fetch and optionally enrich Wazuh alerts from OpenSearch.

    When ``enrich=true``, each alert is enriched concurrently against
    VirusTotal, AbuseIPDB, and MISP.  The per-alert enrichment calls
    run in parallel via ``asyncio.gather`` with ``return_exceptions=True``
    so that one failing alert never kills the rest.

    When ``vuln=true``, only alerts with CVE identifiers (tagged as
    ``vuln:CVE-*``) are returned.  Implies ``enrich=true`` since CVE
    extraction runs during enrichment.
    """
    # vuln implies enrich
    if vuln is not None:
        enrich = True

    raw_data = await collector.query_opensearch(
        limit=limit,
        offset=offset,
        severity=severity,
    )

    hits = raw_data.get("hits", {}).get("hits", [])
    logger.info("[Alerts] Fetched %d raw hits from OpenSearch (limit=%d, offset=%d)", len(hits), limit, offset)

    alerts: List[UnifiedAlert] = [normalizer.from_wazuh(hit) for hit in hits]

    if enrich and alerts:
        logger.info("[Alerts] Enriching %d alerts in parallel…", len(alerts))

        # ------------------------------------------------------------------ #
        # Parallel enrichment — no artificial batch timeout.                  #
        # return_exceptions=True ensures one failing alert never kills the    #
        # rest.  Each per-service call is already capped at 5 s by the        #
        # enrichment_service layer, so the gather completes when every        #
        # alert is done (or has timed out individually).                      #
        # ------------------------------------------------------------------ #
        results = await asyncio.gather(
            *[_enrich_alert(a) for a in alerts],
            return_exceptions=True,
        )

        # Map results — _enrich_alert mutates in-place and returns the
        # same UnifiedAlert object; re-assign to handle edge cases where
        # an exception was raised instead of a result.
        enriched: List[UnifiedAlert] = []
        for original, result in zip(alerts, results):
            if isinstance(result, Exception):
                logger.warning(
                    "[Alerts] Per-alert enrichment raised an exception for %s: %s — "
                    "returning alert with safe defaults.",
                    original.event_id, result,
                )
                enriched.append(original)
            else:
                enriched.append(result)

        alerts = enriched
        logger.info("[Alerts] Enrichment complete for %d alerts", len(alerts))

    # Filter by CVE vuln tags after enrichment
    if vuln is not None:
        before = len(alerts)
        alerts = [
            a for a in alerts
            if any(t.startswith("vuln:") for t in a.enrichment_data.tags)
            == vuln
        ]
        logger.info(
            "[Alerts] vuln=%s filter: %d → %d alerts", vuln, before, len(alerts),
        )

    return alerts


# --------------------------------------------------------------------------- #
# Batch pipeline endpoints — accept List[UnifiedAlert] (raw GET /alerts/       #
# output) and run all downstream services so data flows without format errors. #
# --------------------------------------------------------------------------- #

@router.post("/batch/process", response_model=List[dict])
async def process_alerts_batch(alerts: List[UnifiedAlert]):
    """
    Run the full downstream pipeline on a batch of alerts.
    Accepts the exact ``List[UnifiedAlert]`` array returned by ``GET /alerts/``.

    For each alert: enriches with threat intel, then runs patch recommendation,
    risk scoring, and LLM classification.  Returns a combined result per alert.
    """
    enriched = await asyncio.gather(
        *[_enrich_alert(a) for a in alerts],
        return_exceptions=True,
    )

    results = []
    for alert, result in zip(alerts, enriched):
        if isinstance(result, Exception):
            logger.warning("[Batch] Enrichment failed for %s: %s", alert.event_id, result)
            continue

        patch_res = await get_patch_recommendations(alert)
        risk_res = await calculate_risk_score(alert)
        filter_payload = prepare_llm_payload(alert)
        filter_res = await classify_alert(filter_payload)

        results.append({
            "event_id": alert.event_id,
            "enrichment": IntelResponse(
                ioc=alert.host_context.ip_address or "unknown",
                malicious=(alert.enrichment_data.abuse_ipdb or {}).get("score", 0) > 25 or bool((alert.enrichment_data.misp or {}).get("matches", [])),
                reputation=max(0, 100 - ((alert.enrichment_data.virus_total or {}).get("score", 0) or 0)),
                sources=[],
            ).model_dump(),
            "patch": patch_res.model_dump(),
            "risk": RiskScoreResponse(
                event_id=alert.event_id,
                risk_score=risk_res["risk_score"],
                priority=risk_res["priority"],
                confidence=risk_res["confidence"],
                features=risk_res["features"],
            ).model_dump(),
            "filter": FilterResult(
                alert_id=alert.event_id,
                classification=filter_res["classification"],
                confidence=filter_res["confidence"],
                summary=f"Rule {filter_payload.get('rule_id', '?')} marked as {filter_res['classification']}",
            ).model_dump(),
        })

    return results


@router.post("/batch/enrich", response_model=List[UnifiedAlert])
async def enrich_alerts_batch(alerts: List[UnifiedAlert]):
    """
    Enrich a batch of alerts with threat intel (VT, AbuseIPDB, MISP).
    Accepts the exact ``List[UnifiedAlert]`` array returned by ``GET /alerts/``.
    """
    results = await asyncio.gather(
        *[_enrich_alert(a) for a in alerts],
        return_exceptions=True,
    )
    out = []
    for alert, result in zip(alerts, results):
        if isinstance(result, Exception):
            logger.warning("[Batch] Enrichment failed for %s: %s", alert.event_id, result)
        out.append(alert)
    logger.info("[Batch] Enriched %d / %d alerts", len(out), len(alerts))
    return out

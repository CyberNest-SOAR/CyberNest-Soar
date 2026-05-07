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
"""

import asyncio
import logging
from fastapi import APIRouter, Query
from typing import List, Optional

from services.collector import collector
from services.normalizer import normalizer
from services.intel import enrich_alert_intel, extract_cves
from schemas.models import UnifiedAlert

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

    # Null-guard: ensure enrichment_data fields are never None
    if alert.enrichment_data.vt_score is None:
        alert.enrichment_data.vt_score = 0
    if alert.enrichment_data.abuse_score is None:
        alert.enrichment_data.abuse_score = 100

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
):
    """
    Fetch and optionally enrich Wazuh alerts from OpenSearch.

    When ``enrich=true``, each alert is enriched concurrently against
    VirusTotal, AbuseIPDB, and MISP.  The per-alert enrichment calls
    run in parallel via ``asyncio.gather`` with ``return_exceptions=True``
    so that one failing alert never kills the rest.
    """
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
                original.enrichment_data.vt_score = (
                    0 if original.enrichment_data.vt_score is None
                    else original.enrichment_data.vt_score
                )
                original.enrichment_data.abuse_score = (
                    100 if original.enrichment_data.abuse_score is None
                    else original.enrichment_data.abuse_score
                )
                enriched.append(original)
            else:
                enriched.append(result)

        alerts = enriched
        logger.info("[Alerts] Enrichment complete for %d alerts", len(alerts))

    return alerts

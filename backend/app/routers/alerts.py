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

**Training format** (``/api/v1/alerts/training-format/``):
  Returns alerts in the dataset_pipeline UnifiedAlert schema (flat, 100+
  fields) so AI models see the same schema during inference as training.
  Flattens enrichment (VT, AbuseIPDB, MISP) into scalar fields matching
  the training data format.

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

from app.services.collector import collector
from app.services.normalizer import normalizer
from app.services.intel import enrich_alert_intel, extract_cves
from app.services.patch import get_patch_recommendations
from app.services.risk import calculate_risk_score
from app.routers.filtering import classify_alert_single, predict_noise
from app.schemas.models import UnifiedAlert, IntelResponse, PatchResponse, RiskScoreResponse, FilterResult
from app.services.indexer import get_indexer
from app.schemas.alert_intelligence import AlertRequest
from app.services.alert_intelligence_service import LLMService
from app.services.playbooks import get_playbook_decision

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

    # Index normalized alerts into Qdrant in background (improves routing accuracy)
    try:
        indexer = get_indexer()
        for a in alerts:
            asyncio.create_task(indexer.index_alert_async(a))
    except Exception:
        logger.debug("Indexer unavailable or indexing failed to schedule")

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

    Integrates the noise classifier as the first decision stage:
    If the alert is noise, it is suppressed (skipped from downstream processing).
    Otherwise, continues with enrichment, patch recommendation, and risk scoring.
    """
    # 1. Threat Enrichment (VT, AbuseIPDB, MISP) on all alerts in parallel
    enriched_results = await asyncio.gather(
        *[_enrich_alert(a) for a in alerts],
        return_exceptions=True,
    )
    enriched_alerts = []
    for original, res in zip(alerts, enriched_results):
        if isinstance(res, Exception):
            logger.warning("[Batch] Enrichment failed for %s: %s", original.event_id, res)
            enriched_alerts.append(original)
        else:
            enriched_alerts.append(res)

    # 2. Run Noise Reduction Model (XGBoost), Confidence Evaluation, and LLM Service
    llm_service = LLMService()
    results = []

    for alert in enriched_alerts:
        # Predict noise on the enriched alert
        res = predict_noise(alert)
        # Extract raw probability of being actionable
        raw_prob = res["confidence"] if res["prediction"] == "Actionable" else round(1.0 - res["confidence"], 4)

        # Prepare AlertRequest
        vt_score = float((alert.enrichment_data.virus_total or {}).get("score", 0.0) or 0.0)
        abuse_score = float((alert.enrichment_data.abuse_ipdb or {}).get("score", 0.0) or 0.0)
        similar_alerts = alert.soc_reasoning.similar_alerts_last_hour or 0
        maintenance = alert.soc_reasoning.maintenance_window or False
        admin = alert.soc_reasoning.known_admin_activity or False
        criticality = alert.soc_reasoning.asset_criticality or "low"

        req = AlertRequest(
            alert_id=alert.event_id,
            alert_severity=alert.severity,
            enrichment_vt_score=vt_score,
            enrichment_abuse_score=abuse_score,
            asset_criticality=criticality,
            similar_alerts_last_hour=similar_alerts,
            maintenance_window=maintenance,
            known_admin_activity=admin,
            noise_confidence=raw_prob
        )

        # Process through the confidence-based routing service
        llm_res = llm_service.process_alert(req)

        if llm_res.verdict == "noise":
            # If noise, we suppress/skip from downstream processing (Risk, Playbooks, TheHive)
            results.append({
                "event_id": alert.event_id,
                "enrichment": None,
                "patch": None,
                "risk": None,
                "playbook": None,
                "thehive": None,
                "filter": FilterResult(
                    alert_id=alert.event_id,
                    classification="noise",
                    confidence=llm_res.confidence,
                    summary=llm_res.reasoning
                ).model_dump()
            })
        else:
            # Actionable! Process with Risk Engine, Playbooks, and TheHive.
            patch_res = await get_patch_recommendations(alert)
            risk_res = await calculate_risk_score(alert)
            playbook_res = await get_playbook_decision(alert)
            
            # Create a case in TheHive if the playbook recommends it
            hive_res = None
            if playbook_res.get("action") == "create_case":
                severity = alert.severity
                hive_severity = 4 if severity >= 10 else 3 if severity >= 7 else 2 if severity >= 4 else 1
                soc = alert.soc_reasoning
                attack_type = getattr(soc, "attack_type", None) or ""
                mitre_tactic = getattr(soc, "mitre_tactic", None) or ""
                source_ip = alert.host_context.ip_address
                title = f"[{'HIGH' if hive_severity >= 3 else 'MEDIUM' if hive_severity >= 2 else 'LOW'}] {alert.description[:80]}"
                
                from app.collectors.thehive_client import create_case
                try:
                    hive_res = create_case(
                        title=title,
                        severity=hive_severity,
                        description=alert.description,
                        tags=[alert.source, attack_type, mitre_tactic] if attack_type else [alert.source],
                        source_ip=source_ip,
                        destination_ip="",
                        attack_type=attack_type,
                        mitre_tactic=mitre_tactic,
                    )
                except Exception as ex:
                    logger.error("Failed to create TheHive case in batch pipeline for alert %s: %s", alert.event_id, ex)
                    hive_res = {"status": "error", "detail": str(ex)}

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
                    predicted_analyst_verdict=risk_res["predicted_analyst_verdict"] if "predicted_analyst_verdict" in risk_res else "actionable",
                    confidence=risk_res["confidence"],
                    features=risk_res["features"],
                ).model_dump(),
                "playbook": playbook_res,
                "thehive": hive_res,
                "filter": FilterResult(
                    alert_id=alert.event_id,
                    classification="important",
                    confidence=llm_res.confidence,
                    summary=llm_res.reasoning
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


# --------------------------------------------------------------------------- #
# Training-format endpoint — returns alerts in dataset_pipeline UnifiedAlert   #
# schema (100+ flat fields) so AI models see the same schema as training data. #
# --------------------------------------------------------------------------- #

@router.get("/training-format", response_model=List[dict])
async def fetch_alerts_training_format(
    limit: int = Query(100, ge=1, description="Number of alerts to fetch"),
    offset: int = Query(0, alias="from", ge=0, description="Number of alerts to skip"),
    enrich: bool = Query(False, description="Enrich and flatten into training schema"),
):
    """
    Fetch alerts in dataset_pipeline training format.
    Returns the UnifiedAlert schema with 100+ flat fields including:
    - Network telemetry (src_ip, dst_ip, ports, protocol)
    - Alert metadata (signature, severity, category, MITRE ATT&CK)
    - Process/HTTP/DNS/IOC fields
    - Enrichment as flat scalars (enrichment_vt_score, etc.)
    - SOC reasoning defaults for live data

    When enrich=true, enrichment is run and flattened into the
    same scalar fields the AI was trained on.
    """
    raw_data = await collector.query_opensearch(
        limit=limit,
        offset=offset,
    )
    hits = raw_data.get("hits", {}).get("hits", [])
    logger.info("[Training] Fetched %d raw hits from OpenSearch", len(hits))

    if not hits:
        return []

    # Convert to training format
    from services.training_format import batch_to_training_format

    if enrich:
        # Enrich first using backend pipeline, then flatten
        alerts = [normalizer.from_wazuh(hit) for hit in hits]
        results = await asyncio.gather(
            *[_enrich_alert(a) for a in alerts],
            return_exceptions=True,
        )
        enrichment_data_list = []
        for original, result in zip(alerts, results):
            if isinstance(result, Exception):
                enrichment_data_list.append(None)
            else:
                enrichment_data_list.append(result.enrichment_data)

        training_alerts = batch_to_training_format(
            hits, enrichment_results=enrichment_data_list,
        )
    else:
        training_alerts = batch_to_training_format(hits)

    logger.info("[Training] Returning %d alerts in training format", len(training_alerts))
    return training_alerts

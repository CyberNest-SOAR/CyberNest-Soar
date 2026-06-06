import logging
from datetime import datetime, timezone
from schemas.models import UnifiedAlert, PatchResponse, Recommendation
from .patch_engine import PatchEnginePredictor, extract_cves_from_alert, calculate_patch_priority

log = logging.getLogger(__name__)
predictor = None


def initialize_patch_service():
    """Initialize patch engine on startup."""
    global predictor
    predictor = PatchEnginePredictor()
    log.info("Patch service initialized with ML models")


async def get_patch_recommendations(alert: UnifiedAlert) -> PatchResponse:
    """
    Generate patch recommendations using ML models.
    Combines CVE data with exploit likelihood, time-to-exploit, and attack patterns.
    """
    global predictor
    if not predictor:
        initialize_patch_service()

    recommendations = []

    # Extract CVE IDs from enrichment tags and raw data
    enrichment_dict = {
        "tags": alert.enrichment_data.tags,
        "description": alert.description,
        "raw_data": alert.raw_data,
    }
    cves = extract_cves_from_alert(enrichment_dict)

    # Cross-reference alert data with NVD/EPSS enrichment scores
    raw_data = alert.raw_data
    vulnerabilities = (
        raw_data.get("data", {}).get("vulnerability", [])
        if isinstance(raw_data.get("data"), dict)
        else raw_data.get("vulnerability", [])
    )
    if not isinstance(vulnerabilities, list):
        vulnerabilities = [vulnerabilities] if vulnerabilities else []

    for vuln in vulnerabilities:
        cve = vuln.get("cve", "UNKNOWN")
        if cve not in cves and cve != "UNKNOWN":
            cves.append(cve)

    if not cves:
        cves = ["CVE-UNKNOWN"]

    # Get CVE year (extract from CVE ID or use current year)
    for cve in cves:
        cve_year = 2024
        year_match = cve.split("-")[1] if "-" in cve else None
        if year_match and year_match.isdigit():
            cve_year = int(year_match)

        # Get CVSS and EPSS from enrichment
        cvss = (alert.enrichment_data.nvd or {}).get("cvss") or 0.0
        epss = (alert.enrichment_data.epss or {}).get("score") or 0.0
        epss_percentile = 0.5

        # Get ML predictions
        exploit_pred = predictor.predict_exploit_likelihood(cve, epss, epss_percentile, cvss, cve_year)
        time_pred = predictor.predict_time_to_exploit(cve, epss, cvss, cve_year)
        patterns = predictor.detect_attack_patterns(str(alert.raw_data))

        # Calculate priority
        priority, action = calculate_patch_priority(
            exploit_pred["probability"],
            time_pred["days"],
            cvss
        )

        ml_confidence = min(
            0.95 if exploit_pred["status"] == "loaded" else 0.6,
            0.95 if time_pred["status"] == "loaded" else 0.6
        )

        recommendations.append(
            Recommendation(
                cve=cve,
                cvss=cvss,
                epss=epss,
                priority=priority,
                action=action,
                exploit_likelihood=exploit_pred["probability"],
                time_to_exploit_days=time_pred["days"],
                attack_patterns=patterns["patterns"],
                ml_confidence=ml_confidence,
            )
        )

    # Fallback: if no explicit recommendation was generated but enrichment has CVE data
    nvd = alert.enrichment_data.nvd
    epss_data = alert.enrichment_data.epss
    if not recommendations and (nvd or epss_data):
        cve = "CVE-SIMULATED"
        cvss = (nvd or {}).get("cvss") or 7.5
        epss = (epss_data or {}).get("score") or 0.1
        cve_year = 2024
        epss_percentile = 0.5

        exploit_pred = predictor.predict_exploit_likelihood(cve, epss, epss_percentile, cvss, cve_year)
        time_pred = predictor.predict_time_to_exploit(cve, epss, cvss, cve_year)
        patterns = predictor.detect_attack_patterns(str(alert.raw_data))

        priority, action = calculate_patch_priority(
            exploit_pred["probability"],
            time_pred["days"],
            cvss
        )

        ml_confidence = min(
            0.95 if exploit_pred["status"] == "loaded" else 0.6,
            0.95 if time_pred["status"] == "loaded" else 0.6
        )

        recommendations.append(
            Recommendation(
                cve=cve,
                cvss=cvss,
                epss=epss,
                priority=priority,
                action=action,
                exploit_likelihood=exploit_pred["probability"],
                time_to_exploit_days=time_pred["days"],
                attack_patterns=patterns["patterns"],
                ml_confidence=ml_confidence,
            )
        )

    return PatchResponse(
        host=alert.host_context.hostname,
        recommendations=recommendations,
        analysis_timestamp=datetime.now(timezone.utc)
    )

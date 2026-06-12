from __future__ import annotations

from io import BytesIO
import json
import logging
from pathlib import Path
from typing import Any, Dict, Tuple

import joblib
import pandas as pd

try:
    from app.config.settings import settings
    from app.schemas.models import UnifiedAlert
except Exception:  # pragma: no cover - supports package import style
    from app.config.settings import settings
    from app.schemas.models import UnifiedAlert

try:
    from app.cache.redis_cache import cache_key, get_bytes, set_bytes
except Exception:  # pragma: no cover - supports running from backend/app cwd
    from cache.redis_cache import cache_key, get_bytes, set_bytes

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


def _artifact_path(value: Path, fallback_name: str) -> Path:
    path = Path(value) if value else ARTIFACTS_DIR / fallback_name
    return path


def _load_risk_artifacts() -> Tuple[Any | None, Any | None]:
    model_path = _artifact_path(settings.RISK_MODEL_PATH, "base_xgb_model_pipeline.joblib")
    label_encoder_path = _artifact_path(settings.RISK_LABEL_ENCODER_PATH, "label_encoder.joblib")

    model = _load_joblib_artifact(model_path, "risk_model")
    label_encoder = _load_joblib_artifact(label_encoder_path, "risk_label_encoder")
    return model, label_encoder


def _load_joblib_artifact(path: Path, label: str) -> Any | None:
    if not path.exists():
        logger.warning("%s artifact not found at %s", label, path)
        return None

    stat = path.stat()
    key = cache_key(
        "artifacts:joblib",
        label,
        path.resolve(),
        stat.st_mtime_ns,
        stat.st_size,
    )

    cached = get_bytes(key)
    if cached is not None:
        try:
            logger.info("Loaded %s artifact from Redis cache: %s", label, path)
            return joblib.load(BytesIO(cached))
        except Exception as exc:
            logger.warning("Failed to load cached %s artifact from Redis: %s", label, exc)

    try:
        raw = path.read_bytes()
        artifact = joblib.load(BytesIO(raw))
        set_bytes(key, raw, ttl=3600)
        logger.info("Loaded %s artifact from disk and cached in Redis: %s", label, path)
        return artifact
    except Exception as exc:
        logger.warning("Failed to load %s artifact from %s: %s", label, path, exc)
        return None


def _build_risk_summary(alert: UnifiedAlert) -> str:
    enrichment = alert.enrichment_data
    parts = [
        f"event_id={alert.event_id}",
        f"source={alert.source}",
        f"severity={alert.severity}",
        f"description={alert.description}",
        f"host={alert.host_context.hostname}",
        f"ip={alert.host_context.ip_address}",
        f"tags={' '.join(enrichment.tags)}",
    ]

    for name in ("virus_total", "abuse_ipdb", "misp", "epss", "nvd", "cisa_kev", "urlhaus", "alienvault_otx"):
        value = getattr(enrichment, name)
        if value:
            parts.append(f"{name}={json.dumps(value, sort_keys=True, default=str)}")

    raw_data = json.dumps(alert.raw_data, sort_keys=True, default=str)
    parts.append(f"raw_data={raw_data}")
    return " | ".join(parts)


def _build_model_features(alert: UnifiedAlert) -> pd.DataFrame:
    enrichment = alert.enrichment_data
    soc = alert.soc_reasoning

    vt_score = 0.0
    if enrichment.virus_total:
        vt_score = float(enrichment.virus_total.get("score") or 0.0)

    abuse_score = 0.0
    if enrichment.abuse_ipdb:
        abuse_score = float(enrichment.abuse_ipdb.get("score") or 0.0)

    cvss_score = 0.0
    if enrichment.nvd:
        cvss_score = float(enrichment.nvd.get("cvss") or 0.0)

    epss_score = 0.0
    if enrichment.epss:
        epss_score = float(enrichment.epss.get("score") or 0.0)

    repeated_behavior_score = float(soc.repeated_behavior_score or 0.0)
    alert_frequency = float(soc.similar_alerts_last_hour or 0.0)
    asset_criticality = str(soc.asset_criticality or "unknown")
    historically_seen = bool(soc.historically_seen or False)

    return pd.DataFrame(
        [
            {
                "enrichment_vt_score": vt_score,
                "enrichment_abuse_score": abuse_score,
                "repeated_behavior_score": repeated_behavior_score,
                "enrichment_cvss_score": cvss_score,
                "enrichment_epss_score": epss_score,
                "alert_frequency": alert_frequency,
                "asset_criticality": asset_criticality,
                "historically_seen": historically_seen,
            }
        ]
    )


def _fallback_verdict(final_score: int) -> str:
    if final_score >= 80:
        return "true_positive"
    if final_score >= 60:
        return "suspicious"
    if final_score >= 35:
        return "investigating"
    if final_score >= 15:
        return "false_positive"
    return "benign"


def _normalize_verdict_label(label: Any) -> str:
    normalized = str(label).strip().lower().replace(" ", "_")
    verdict_map = {
        "tp": "true_positive",
        "truepositive": "true_positive",
        "true_positive": "true_positive",
        "fp": "false_positive",
        "falsepositive": "false_positive",
        "false_positive": "false_positive",
        "benign": "benign",
        "suspicious": "suspicious",
        "investigating": "investigating",
        "unknown": "investigating",
    }
    return verdict_map.get(normalized, normalized)


def _predict_analyst_verdict(
    alert: UnifiedAlert,
    structured_features: Dict[str, float],
    summary_text: str,
    final_score: int,
) -> tuple[str, float, bool]:
    model, label_encoder = _load_risk_artifacts()
    if model is None:
        return _fallback_verdict(final_score), 0.0, False

    try:
        model_input = _build_model_features(alert)

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(model_input)[0]
            best_index = max(range(len(probabilities)), key=lambda index: probabilities[index])
            raw_prediction = model.predict(model_input)[0]
            if label_encoder is not None:
                try:
                    predicted = str(label_encoder.inverse_transform([raw_prediction])[0])
                except Exception:
                    predicted = _normalize_verdict_label(raw_prediction)
            else:
                predicted = _normalize_verdict_label(raw_prediction)
            confidence = float(probabilities[best_index])
        else:
            raw_prediction = model.predict(model_input)[0]
            if label_encoder is not None:
                try:
                    predicted = str(label_encoder.inverse_transform([raw_prediction])[0])
                except Exception:
                    predicted = _normalize_verdict_label(raw_prediction)
            else:
                predicted = _normalize_verdict_label(raw_prediction)
            confidence = 1.0

        return predicted, confidence, True
    except Exception as exc:
        logger.warning("Risk model prediction failed for %s: %s", alert.event_id, exc)
        return _fallback_verdict(final_score), 0.0, False

async def calculate_risk_score(alert: UnifiedAlert) -> dict:
    base_score = alert.severity * 10
    
    enrichment_score = 0
    
    nvd = alert.enrichment_data.nvd
    cvss = nvd.get("cvss") if nvd else None
    if cvss is not None:
        enrichment_score += cvss * 5
        
    epss = alert.enrichment_data.epss
    epss_score = epss.get("score") if epss else None
    if epss_score is not None:
        enrichment_score += epss_score * 50

    abuse = alert.enrichment_data.abuse_ipdb
    abuse_score = abuse.get("score") if abuse else None
    if abuse_score is not None:
        enrichment_score += abuse_score * 0.5
        
    vt = alert.enrichment_data.virus_total
    vt_score = vt.get("score") if vt else None
    if vt_score is not None:
        enrichment_score += vt_score * 0.5

    urlhaus = alert.enrichment_data.urlhaus
    urlhaus_score = 0.0
    if urlhaus and urlhaus.get("matched"):
        if urlhaus.get("url_status") == "online":
            urlhaus_score += 15.0
        threat = urlhaus.get("threat")
        if threat:
            urlhaus_score += 5.0
        tags = urlhaus.get("tags") or []
        urlhaus_score += min(len(tags) * 2.0, 10.0)
        enrichment_score += urlhaus_score

    alienvault_otx = alert.enrichment_data.alienvault_otx
    otx_score = 0.0
    if alienvault_otx and alienvault_otx.get("matched"):
        pulse_count = alienvault_otx.get("pulse_count") or 0
        otx_score = min(float(pulse_count) * 4.0, 20.0)
        enrichment_score += otx_score
        
    final_score = int(base_score + enrichment_score)
    priority = "High" if final_score > 70 else "Medium" if final_score > 30 else "Low"

    structured_features = {
        "severity": float(alert.severity),
        "base_score": float(base_score),
        "enrichment_score": float(enrichment_score),
        "cvss": float(cvss or 0.0),
        "epss": float(epss_score or 0.0),
        "abuse_score": float(abuse_score or 0.0),
        "vt_score": float(vt_score or 0.0),
        "urlhaus_score": float(urlhaus_score),
        "otx_score": float(otx_score),
        "tag_count": float(len(alert.enrichment_data.tags)),
        "heuristic_risk_score": float(min(final_score, 100)),
    }
    summary_text = _build_risk_summary(alert)
    predicted_analyst_verdict, model_confidence, _model_ready = _predict_analyst_verdict(
        alert=alert,
        structured_features=structured_features,
        summary_text=summary_text,
        final_score=final_score,
    )
    
    return {
        "risk_score": min(final_score, 100),
        "priority": priority,
        "predicted_analyst_verdict": predicted_analyst_verdict,
        "confidence": model_confidence,
        "features": {
            "base_severity": base_score, 
            "enrichment": enrichment_score,
            "cvss": cvss or 0.0,
            "epss": epss_score or 0.0,
            "urlhaus": urlhaus_score,
            "alienvault_otx": otx_score,
        },
    }

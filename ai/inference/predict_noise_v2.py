import sys
import logging
from pathlib import Path
import pandas as pd
import joblib

log = logging.getLogger(__name__)

# Resolve model path dynamically relative to this file
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "noise_classifier_v2.pkl"

# ==========================================
# LOAD MODEL (ONCE ON STARTUP)
# ==========================================
if MODEL_PATH.exists():
    try:
        bundle = joblib.load(MODEL_PATH)
        model = bundle["model"]
        features = bundle["features"]
        threshold = bundle["threshold"]
        log.info("Loaded noise classifier model from %s", MODEL_PATH)
    except Exception as e:
        log.exception("Failed to load noise classifier model from %s: %s", MODEL_PATH, e)
        model = None
        features = []
        threshold = 0.5
else:
    log.warning("Noise classifier model not found at %s", MODEL_PATH)
    model = None
    features = []
    threshold = 0.5


# ==========================================
# PREPARE ALERT (Preserved V2 implementation)
# ==========================================

def prepare_alert(alert):

    df = pd.DataFrame([alert])

    categorical_features = [

        "protocol",
        "asset_criticality",
        "host_role",
        "department",
        "user_role",
        "authentication_method",
        "integrity_level",
        "timeline_position"
    ]

    for col in categorical_features:

        if col in df.columns:

            df[col] = (

                df[col]

                .fillna("unknown")

                .astype(str)
            )

    df = pd.get_dummies(

        df,

        columns=categorical_features
    )

    # ======================================
    # ALIGN TRAINING FEATURES
    # ======================================

    for col in features:

        if col not in df.columns:

            df[col] = 0

    df = df[features]
    df = df.astype("float32")

    return df


# ==========================================
# PREDICT (Preserved V2 implementation)
# ==========================================

def predict_alert(alert):

    df = prepare_alert(alert)

    probability = float(
        model.predict_proba(df)[0][1]
    )

    prediction = (
        "actionable"
        if probability >= threshold
        else "noise"
    )

    # ======================================
    # CONFIDENCE-BASED CASCADE
    # ======================================

    requires_llm = (
        0.15 < probability < 0.85
    )

    confidence_level = (
        "high"
        if not requires_llm
        else "medium"
    )

    return {

        "prediction": prediction,

        "confidence": round(
            probability,
            4
        ),

        "confidence_level": confidence_level,

        "requires_llm": requires_llm
    }


# ==========================================
# ROBUST WRAPPER AND INTEGRATION HOOKS
# ==========================================

def get_flat_features(alert) -> dict:
    """
    Extracts flat features from a dictionary or UnifiedAlert object.
    Uses dataset_pipeline mapping to ensure perfect alignment with training schema.
    """
    # Try importing dataset pipeline to_training_format
    to_training_format = None
    try:
        # Dynamically import to_training_format
        # Add backend/app/soar_backend to sys.path if needed
        backend_dir = str(Path(__file__).resolve().parent.parent.parent / "backend" / "app" / "soar_backend")
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from services.training_format import to_training_format
    except Exception as e:
        log.warning("Could not import to_training_format: %s", e)

    flat = {}

    if hasattr(alert, "raw_data") and hasattr(alert, "enrichment_data"):
        # It's a backend UnifiedAlert object
        if to_training_format is not None:
            try:
                flat = to_training_format(alert.raw_data, alert.enrichment_data)
            except Exception as e:
                log.warning("to_training_format failed: %s", e)
        
        # Overlay/enrich with attributes populated on the actual object
        if hasattr(alert, "severity") and alert.severity is not None:
            flat["alert_severity"] = alert.severity
        if hasattr(alert, "description") and alert.description is not None:
            flat["alert_signature"] = alert.description

        if alert.enrichment_data:
            vt = alert.enrichment_data.virus_total or {}
            if vt.get("score") is not None:
                flat["enrichment_vt_score"] = vt.get("score")
            abuse = alert.enrichment_data.abuse_ipdb or {}
            if abuse.get("score") is not None:
                flat["enrichment_abuse_score"] = abuse.get("score")

        if alert.soc_reasoning:
            sr = alert.soc_reasoning
            for attr in [
                "asset_value", "similar_alerts_last_hour", "repeated_behavior_score",
                "business_hours", "weekend_activity", "maintenance_window", "patch_window",
                "known_admin_activity", "vulnerability_scan", "scheduled_backup",
                "mfa_used", "signed_binary", "historically_seen", "recurring_alert",
                "host_role", "department", "user_role", "authentication_method",
                "integrity_level", "timeline_position"
            ]:
                val = getattr(sr, attr, None)
                if val is not None:
                    flat[attr] = val
            if sr.asset_criticality is not None:
                flat["asset_criticality"] = sr.asset_criticality

        if alert.network_session:
            ns = alert.network_session
            if ns.protocol is not None:
                flat["protocol"] = ns.protocol
            if ns.bytes_sent is not None:
                flat["bytes_sent"] = ns.bytes_sent
            if ns.bytes_received is not None:
                flat["bytes_received"] = ns.bytes_received
            if ns.session_duration is not None:
                flat["duration"] = ns.session_duration
            if ns.dst_port is not None:
                flat["dst_port"] = ns.dst_port

        if alert.endpoint_process:
            ep = alert.endpoint_process
            if ep.integrity_level is not None:
                flat["integrity_level"] = ep.integrity_level

        if alert.asset_context:
            ac = alert.asset_context
            if ac.asset_value is not None:
                flat["asset_value"] = ac.asset_value
            if ac.criticality is not None:
                flat["asset_criticality"] = ac.criticality
            if ac.host_role is not None:
                flat["host_role"] = ac.host_role
            if ac.department is not None:
                flat["department"] = ac.department

        if alert.timeline:
            tl = alert.timeline
            if tl.timeline_position is not None:
                flat["timeline_position"] = tl.timeline_position

    elif isinstance(alert, dict):
        if "raw_data" in alert:
            # Dict representation of UnifiedAlert
            raw_data = alert.get("raw_data") or {}
            enrichment = alert.get("enrichment_data")
            if to_training_format is not None:
                try:
                    flat = to_training_format(raw_data, enrichment)
                except Exception as e:
                    log.warning("to_training_format failed on dict: %s", e)
            
            flat["alert_severity"] = alert.get("severity") or flat.get("alert_severity")
            
            sr = alert.get("soc_reasoning") or {}
            for k in [
                "asset_value", "similar_alerts_last_hour", "repeated_behavior_score",
                "business_hours", "weekend_activity", "maintenance_window", "patch_window",
                "known_admin_activity", "vulnerability_scan", "scheduled_backup",
                "mfa_used", "signed_binary", "historically_seen", "recurring_alert",
                "host_role", "department", "user_role", "authentication_method",
                "integrity_level", "timeline_position", "asset_criticality"
            ]:
                if sr.get(k) is not None:
                    flat[k] = sr.get(k)

            ns = alert.get("network_session") or {}
            if ns.get("protocol") is not None:
                flat["protocol"] = ns.get("protocol")
            if ns.get("bytes_sent") is not None:
                flat["bytes_sent"] = ns.get("bytes_sent")
            if ns.get("bytes_received") is not None:
                flat["bytes_received"] = ns.get("bytes_received")
            if ns.get("session_duration") is not None:
                flat["duration"] = ns.get("session_duration")
            if ns.get("dst_port") is not None:
                flat["dst_port"] = ns.get("dst_port")
        else:
            # Flat dictionary
            flat = alert.copy()

    # Convert any binary ints/booleans to integers/floats as needed
    return flat


CATEGORICAL_DEFAULTS = {
    "protocol": "unknown",
    "asset_criticality": "unknown",
    "host_role": "unknown",
    "department": "unknown",
    "user_role": "unknown",
    "authentication_method": "unknown",
    "integrity_level": "unknown",
    "timeline_position": "unknown"
}


def predict_noise(alert) -> dict:
    """
    Predict whether an incoming alert is Noise or Actionable.
    Integrates the V2 noise classifier.
    
    Accepts:
        - A UnifiedAlert backend object
        - A dictionary representation of UnifiedAlert
        - A flat features dictionary
        
    Returns a dictionary matching the V1 output schema with V2 metadata added:
        {
            "prediction": "Actionable" | "Noise",
            "confidence": float,
            "confidence_level": "high" | "medium",
            "requires_llm": bool
        }
    """
    if model is None:
        log.error("Noise classifier V2 model is not loaded; defaulting alert to Actionable.")
        res = {
            "prediction": "Actionable",
            "confidence": 1.0,
            "confidence_level": "high",
            "requires_llm": False
        }
        # Safely attach metadata to object
        _attach_metadata(alert, res)
        return res

    try:
        # 1. Flatten and align features
        flat_alert = get_flat_features(alert)
        
        # Ensure all categorical columns exist to prevent get_dummies KeyError in prepare_alert
        for col, default_val in CATEGORICAL_DEFAULTS.items():
            if col not in flat_alert or flat_alert[col] is None:
                flat_alert[col] = default_val
        
        # 2. Run prediction
        res = predict_alert(flat_alert)
        
        # 3. Map lowercase predictions ("actionable", "noise") to V1 Title Case ("Actionable", "Noise")
        # to ensure compatibility across all existing SOAR workflows, routes, and tests
        mapped_prediction = "Actionable" if res["prediction"] == "actionable" else "Noise"
        
        output = {
            "prediction": mapped_prediction,
            "confidence": res["confidence"],
            "confidence_level": res["confidence_level"],
            "requires_llm": res["requires_llm"]
        }
        
        # 4. Attach metadata to the alert object if applicable
        _attach_metadata(alert, output)
        return output
        
    except Exception as e:
        log.exception("Model prediction failed: %s. Defaulting to Actionable.", e)
        res = {
            "prediction": "Actionable",
            "confidence": 1.0,
            "confidence_level": "high",
            "requires_llm": False
        }
        _attach_metadata(alert, res)
        return res


def _attach_metadata(alert, result_dict: dict) -> None:
    """Helper to attach classification metadata to the alert object's soc_reasoning block."""
    if hasattr(alert, "soc_reasoning") and alert.soc_reasoning is not None:
        try:
            alert.soc_reasoning.prediction = result_dict["prediction"]
            alert.soc_reasoning.confidence = result_dict["confidence"]
            alert.soc_reasoning.confidence_level = result_dict["confidence_level"]
            alert.soc_reasoning.noise = (result_dict["prediction"] == "Noise")
        except Exception as e:
            log.warning("Failed to attach classification metadata to alert.soc_reasoning: %s", e)
    elif isinstance(alert, dict) and "soc_reasoning" in alert:
        try:
            if isinstance(alert["soc_reasoning"], dict):
                alert["soc_reasoning"]["prediction"] = result_dict["prediction"]
                alert["soc_reasoning"]["confidence"] = result_dict["confidence"]
                alert["soc_reasoning"]["confidence_level"] = result_dict["confidence_level"]
                alert["soc_reasoning"]["noise"] = (result_dict["prediction"] == "Noise")
        except Exception as e:
            log.warning("Failed to attach classification metadata to alert dict: %s", e)


if __name__ == "__main__":
    sample_alert = {
        "alert_severity": 15,
        "enrichment_vt_score": 90,
        "enrichment_abuse_score": 80,
        "asset_value": 90,
        "bytes_sent": 50000,
        "bytes_received": 20000,
        "duration": 500,
        "dst_port": 443,
        "similar_alerts_last_hour": 50,
        "repeated_behavior_score": 80,
        "business_hours": False,
        "weekend_activity": False,
        "maintenance_window": False,
        "patch_window": False,
        "known_admin_activity": False,
        "vulnerability_scan": False,
        "scheduled_backup": False,
        "mfa_used": False,
        "signed_binary": False,
        "historically_seen": False,
        "recurring_alert": True,
        "protocol": "TCP",
        "asset_criticality": "critical",
        "host_role": "domain_controller",
        "department": "IT",
        "user_role": "sysadmin",
        "authentication_method": "password",
        "integrity_level": "System",
        "timeline_position": "early"
    }

    result = predict_noise(sample_alert)
    print("Test prediction result:")
    print(result)

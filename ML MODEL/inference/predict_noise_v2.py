import pandas as pd
import joblib


MODEL_PATH = "../models/noise_classifier.pkl"


# ==========================================
# LOAD MODEL
# ==========================================

bundle = joblib.load(MODEL_PATH)

model = bundle["model"]

features = bundle["features"]

threshold = bundle["threshold"]


# ==========================================
# PREPARE ALERT
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
# PREDICT
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
# TEST
# ==========================================

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

    result = predict_alert(
        sample_alert
    )

    print(result)
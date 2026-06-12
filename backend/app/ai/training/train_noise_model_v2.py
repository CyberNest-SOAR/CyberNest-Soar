# train_noise_model.py

import pandas as pd
import json
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    confusion_matrix,
    f1_score
)
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import cross_val_score

from xgboost import XGBClassifier

# =====================================================
# CONFIG
# =====================================================

DATASET_PATH = "../datasets/dataset.ndjson"

MODEL_PATH = "../models/noise_classifier.pkl"

THRESHOLD = 0.50

# =====================================================
# LOAD NDJSON DATASET
# =====================================================

rows = []

print("[+] Loading NDJSON dataset...")

with open(DATASET_PATH, "r", encoding="utf-8") as file:

    for line in file:

        try:

            rows.append(json.loads(line))

        except Exception as e:

            print(f"[-] Skipping broken row: {e}")

            continue

df = pd.DataFrame(rows)

print(f"[+] Loaded {len(df)} alerts")

# =====================================================
# CREATE LABELS
# =====================================================

print("[+] Creating labels from true_positive field...")

df["label"] = (
    df["true_positive"]
    .fillna(False)
    .astype(int)
)

print("\n============================")
print("LABEL DISTRIBUTION")
print("============================")

print(df["label"].value_counts())


# =====================================================
# ENCODE CATEGORICAL FEATURES
# =====================================================

print("\n[+] Encoding categorical features...")

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

print("[+] Categorical encoding complete")


# =====================================================
# FEATURE ENGINEERING
# =====================================================

print("\n[+] Creating engineered features...")

boolean_columns = [
    "business_hours",
    "weekend_activity",
    "maintenance_window",
    "patch_window",
    "known_admin_activity",
    "vulnerability_scan",
    "scheduled_backup",
    "mfa_used",
    "signed_binary",
    "historically_seen",
    "recurring_alert"
]

for col in boolean_columns:

    if col in df.columns:

        df[col] = (
            df[col]
            .fillna(False)
            .astype(int)
        )


# =====================================================
# SELECT FEATURES
# =====================================================

print("\n[+] Selecting optimized features...")

features = [

    # Threat Intel
    "enrichment_vt_score",
    "enrichment_abuse_score",
    "alert_severity",
   
    # Asset
    "asset_value",

    # Network
    "bytes_sent",
    "bytes_received",
    "duration",
    "dst_port",

    # Behavior
    "similar_alerts_last_hour",
    "repeated_behavior_score",
    

    # Boolean
    "business_hours",
    "weekend_activity",
    "maintenance_window",
    "patch_window",
    "known_admin_activity",
    "vulnerability_scan",
    "scheduled_backup",
    "mfa_used",
    "signed_binary",
    "historically_seen",
    "recurring_alert"
]

# =====================================================
# ADD ENCODED FEATURES
# =====================================================

print("\n[+] Adding encoded features...")

encoded_columns = [

    col

    for col in df.columns

    if any(

        col.startswith(cat + "_")

        for cat in categorical_features
    )
]

features.extend(encoded_columns)

print(f"[+] Added {len(encoded_columns)} encoded features")

df = df[features + ["label"]]

# =====================================================
# CLEAN DATA
# =====================================================

print("[+] Cleaning data...")

df.fillna(0, inplace=True)

df.replace(
    [float("inf"), float("-inf")],
    0,
    inplace=True
)

# =====================================================
# FINAL DATASET INFO
# =====================================================

print("\n============================")
print("DATASET INFO")
print("============================")

print(f"Rows: {len(df)}")

print(f"Features: {len(features)}")

print("\nMissing values:")

print(df.isnull().sum())

# =====================================================
# SPLIT DATA
# =====================================================

print("\n[+] Splitting dataset...")

X = df[features]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.2,

    random_state=42,

    stratify=y
)

print(f"[+] Training rows: {len(X_train)}")

print(f"[+] Testing rows: {len(X_test)}")

# =====================================================
# CREATE GPU XGBOOST MODEL
# =====================================================

print("\n[+] Creating GPU-accelerated XGBoost model...")

model = XGBClassifier(

    n_estimators=500,

    max_depth=8,

    learning_rate=0.03,

    subsample=0.9,

    colsample_bytree=0.9,

    scale_pos_weight=3,

    random_state=42,

    n_jobs=-1,

    eval_metric="logloss",

    tree_method="hist",

    device="cuda"
)

# =====================================================
# TRAIN MODEL
# =====================================================

print("[+] Training model...")

model.fit(X_train, y_train)

print("[+] Training complete")

# =====================================================
# EVALUATE MODEL
# =====================================================

print("\n============================")
print("MODEL EVALUATION")
print("============================")

# Predict probabilities
probabilities = model.predict_proba(X_test)

print("\nProbability Statistics")

print(
    pd.Series(probabilities[:,1])
    .describe()
)

# Threshold-based predictions
best_threshold = 0.5
best_f1 = 0

for threshold in [
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
    0.65,
    0.70
]:

    preds = (
        probabilities[:, 1] >= threshold
    ).astype(int)

    score = f1_score(
        y_test,
        preds
    )

    print(
        f"Threshold={threshold:.2f} | F1={score:.4f}"
    )

    if score > best_f1:

        best_f1 = score
        best_threshold = threshold

print(
    f"\nBest Threshold: {best_threshold}"
)

predictions = (
    probabilities[:, 1] >= best_threshold
).astype(int)

accuracy = accuracy_score(
    y_test,
    predictions
)

print(f"\nAccuracy: {accuracy:.4f}")

print(f"\nDecision Threshold: {THRESHOLD}")

print("\nClassification Report:\n")

print(
    classification_report(
        y_test,
        predictions
    )
)

print("\nConfusion Matrix:\n")

print(
    confusion_matrix(
        y_test,
        predictions
    )
)

# =====================================================
# 5-FOLD CROSS VALIDATION
# =====================================================

print("\n============================")
print("5-FOLD CROSS VALIDATION")
print("============================")

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

scores = cross_val_score(
    model,
    X,
    y,
    cv=cv,
    scoring="f1",
    n_jobs=1
)

print(f"Fold Scores: {scores}")
print(f"Mean F1: {scores.mean():.4f}")
print(f"Std F1: {scores.std():.4f}")

metrics = {

    "accuracy": float(accuracy),

    "f1_mean": float(scores.mean()),

    "f1_std": float(scores.std()),

    "threshold": float(best_threshold)

}

joblib.dump(

    metrics,

    "../models/model_metrics.pkl"
)

print(
    "\n[+] Model metrics saved"
)

# =====================================================
# FEATURE IMPORTANCE
# =====================================================

print("\n============================")
print("FEATURE IMPORTANCE")
print("============================")

importance = model.feature_importances_

feature_importance = sorted(
    zip(features, importance),
    key=lambda x: x[1],
    reverse=True
)

zero_importance = []

for feature, score in feature_importance:

    if score == 0:

        zero_importance.append(feature)

print(
    f"\nZero importance features: {len(zero_importance)}"
)

print("\nUnused Features:")

for feature in zero_importance:
    print(feature)
    
for feature, score in feature_importance:

    print(f"{feature}: {score:.4f}")

importance_df = pd.DataFrame(
    feature_importance,
    columns=[
        "feature",
        "importance"
    ]
)

importance_df.to_csv(
    "../models/feature_importance.csv",
    index=False
)

print(
    "\n[+] Feature importance saved"
)
# =====================================================
# SAVE MODEL
# =====================================================

joblib.dump(
    {
        "model": model,
        "features": features,
        "threshold": best_threshold
    },
    MODEL_PATH
)

print("\n============================")
print("MODEL SAVED")
print("============================")

print(f"[+] Saved to: {MODEL_PATH}")

# # =====================================================
# # TEST SINGLE PREDICTION
# # =====================================================

# print("\n============================")
# print("TEST PREDICTION")
# print("============================")

# sample_alert = pd.DataFrame([{

#     "alert_severity": 15,

#     "enrichment_vt_score": 95,

#     "enrichment_abuse_score": 90,

#     "similar_alerts_last_hour": 120,

#     "historical_false_positive_rate": 0.02,

#     "asset_value": 95,

#     "business_hours": 0,

#     "mfa_used": 0,

#     "signed_binary": 0,

#     "suppression_hit": 0
# }])

# probability = model.predict_proba(sample_alert)[0][1]

# prediction = (
#     1 if probability >= THRESHOLD else 0
# )

# result = (
#     "Actionable"
#     if prediction == 1
#     else "Noise"
# )

# print(f"\nPrediction: {result}")

# print(f"Confidence: {probability:.2f}")

# =====================================================
# FINAL SUMMARY
# =====================================================

print("\n============================")
print("TRAINING COMPLETE")
print("============================")

print("SOC Noise Reduction Model Ready")

print(f"Final Accuracy: {accuracy:.4f}")

print(f"Model Path: {MODEL_PATH}")
#!/usr/bin/env python3
"""Train the host attack-pattern clustering model."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_ROOT = PROJECT_ROOT / "services" / "data" / "patch_engine"
DEFAULT_INPUT_FILE = DATA_ROOT / "host_context_prepared.json"
DEFAULT_OUTPUT_DIR = DATA_ROOT / "artifacts" / "runtime"
DEFAULT_REPORTS_DIR = DATA_ROOT / "artifacts" / "reports"
MODEL_FILE = "attack_patterns_kmeans_v0.joblib"
SCALER_FILE = "attack_patterns_scaler_v0.joblib"
MAPPING_FILE = "host_attack_clusters.json"
MANIFEST_FILE = "attack_patterns_kmeans_v0.manifest.json"
REQUIRED_COLUMNS = ["dst_ip", "total_events", "unique_attack_types", "severe_tactics_present"]

# NEW: Candidate features for clustering (will be filtered by what exists)
CANDIDATE_FEATURES = [
    "total_events",
    "unique_attack_types",
    "severe_tactics_present",
    "true_positive_rate",        # NEW: ratio of confirmed real attacks
    "noise_rate",                # NEW: ratio of noise events
    "avg_historical_fp_rate",    # NEW: how often this alert type is a false alarm
    "max_repeated_behavior",     # NEW: is attacker repeating behaviour?
    "unique_campaigns",          # NEW: how many distinct attack campaigns hit this host
    "external_src_count",        # NEW: events from external (non-RFC1918) IPs
]


def configure_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("attack_patterns_train")


def resolve_input_file(preferred: Path, logger: logging.Logger) -> Path:
    if preferred.exists():
        return preferred

    fallback = next(PROJECT_ROOT.rglob("host_context_prepared.json"), None)
    if fallback is not None:
        logger.warning("Resolved host_context_prepared.json via workspace search: %s", fallback)
        return fallback

    raise FileNotFoundError(f"Could not locate host_context_prepared.json at {preferred}")


def load_host_context(input_file: Path, logger: logging.Logger) -> pd.DataFrame:
    logger.info("Loading host context from %s", input_file)
    df = pd.read_json(input_file)

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Host context is missing required columns: {missing}")

    logger.info("Loaded %d host rows", len(df))
    return df


def build_feature_matrix(df: pd.DataFrame, logger: logging.Logger) -> tuple[pd.DataFrame, list[str]]:
    frame = df.copy()
    
    # Filter candidate features to only those that exist in the dataframe
    available_features = [col for col in CANDIDATE_FEATURES if col in frame.columns]
    logger.info("Available features: %s", available_features)
    
    # For backward compatibility, ensure base features are included
    base_features = ["total_events", "unique_attack_types", "severe_tactics_present"]
    feature_columns = [f for f in available_features if f in base_features] + [f for f in available_features if f not in base_features]
    logger.info("Using %d features for clustering: %s", len(feature_columns), feature_columns)

    # Prepare data
    for col in feature_columns:
        if col in ["severe_tactics_present", "any_recurring_alert"]:
            frame[col] = frame[col].fillna(False).astype(int)
        else:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0)

    features = frame[feature_columns].fillna(0)
    return features, feature_columns


def select_best_k(scaled_features: np.ndarray, k_range: range, logger: logging.Logger) -> int:
    best_k = k_range.start
    best_score = -1.0

    for k in k_range:
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(scaled_features)
        if len(set(labels)) > 1:
            score = float(silhouette_score(scaled_features, labels))
        else:
            score = 0.0
        logger.info("k=%d silhouette=%.4f", k, score)
        if score > best_score:
            best_score = score
            best_k = k

    logger.info("Selected k=%d (silhouette=%.4f)", best_k, best_score)
    return best_k


def save_reports(
    df: pd.DataFrame,
    features: pd.DataFrame,
    scaled_features: np.ndarray,
    clusters: np.ndarray,
    reports_dir: Path,
    logger: logging.Logger,
) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data size before plotting: {len(df)}")

    ks = list(range(2, 7))
    inertia_values = []
    silhouette_values = []
    for k in ks:
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(scaled_features)
        inertia_values.append(float(model.inertia_))
        if len(set(labels)) > 1:
            silhouette_values.append(float(silhouette_score(scaled_features, labels)))
        else:
            silhouette_values.append(0.0)

    fig, ax1 = plt.subplots(figsize=(10, 6))
    sns.lineplot(x=ks, y=inertia_values, marker="o", color="#4c78a8", ax=ax1, label="Inertia")
    ax1.set_xlabel("Number of Clusters (k)")
    ax1.set_ylabel("Inertia", color="#4c78a8")
    ax1.tick_params(axis="y", labelcolor="#4c78a8")
    ax2 = ax1.twinx()
    sns.lineplot(x=ks, y=silhouette_values, marker="s", color="#f58518", ax=ax2, label="Silhouette")
    ax2.set_ylabel("Silhouette Score", color="#f58518")
    ax2.tick_params(axis="y", labelcolor="#f58518")
    ax1.set_title("Attack Patterns - K Selection")
    fig.tight_layout()
    fig.savefig(reports_dir / "v0_patterns_k_selection.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    cluster_sizes = pd.Series(clusters).value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(
        x=features["total_events"],
        y=features["unique_attack_types"],
        hue=clusters,
        palette="viridis",
        size=features["severe_tactics_present"],
        sizes=(80, 200),
        alpha=0.85,
        ax=ax,
    )
    ax.set_title("Attack Patterns - Host Cluster Profile")
    ax.set_xlabel("Total Events")
    ax.set_ylabel("Unique Attack Types")
    ax.grid(True, alpha=0.2)
    for cluster_id, count in cluster_sizes.items():
        ax.text(0.02, 0.98 - (cluster_id * 0.06), f"Cluster {cluster_id}: {int(count)} hosts", transform=ax.transAxes)
    fig.tight_layout()
    fig.savefig(reports_dir / "v0_patterns_profile.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def train_clustering(input_file: Path, output_dir: Path, logger: logging.Logger) -> dict:
    df = load_host_context(input_file, logger)
    X, feature_columns = build_feature_matrix(df, logger)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    k_range = range(2, 7)
    best_k = select_best_k(X_scaled, k_range, logger)
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    best_silhouette = float(silhouette_score(X_scaled, clusters)) if len(set(clusters)) > 1 else 0.0

    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / MODEL_FILE
    scaler_path = output_dir / SCALER_FILE
    mapping_path = output_dir / MAPPING_FILE
    manifest_path = output_dir / MANIFEST_FILE

    joblib.dump(kmeans, model_path)
    joblib.dump(scaler, scaler_path)

    host_mapping = {str(dst_ip): int(cluster) for dst_ip, cluster in zip(df["dst_ip"].tolist(), clusters.tolist())}
    with open(mapping_path, "w", encoding="utf-8") as handle:
        json.dump(host_mapping, handle, indent=2)

    manifest = {
        "model_type": "KMeans",
        "features": feature_columns,
        "n_clusters": int(best_k),
        "silhouette_score": float(best_silhouette),
        "selected_k_reason": "highest silhouette score",
        "k_range": [int(k) for k in k_range],
        "training_rows": int(len(df)),
    }
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    logger.info("Cluster distribution: %s", pd.Series(clusters).value_counts().to_dict())
    logger.info("Saved model to %s", model_path)
    logger.info("Saved scaler to %s", scaler_path)
    logger.info("Saved host mapping to %s", mapping_path)
    logger.info("Saved manifest to %s", manifest_path)

    save_reports(df, X, X_scaled, clusters, DEFAULT_REPORTS_DIR, logger)
    logger.info("Saved reports to %s", DEFAULT_REPORTS_DIR)

    return {
        "model_path": str(model_path),
        "scaler_path": str(scaler_path),
        "mapping_path": str(mapping_path),
        "manifest_path": str(manifest_path),
        "reports_dir": str(DEFAULT_REPORTS_DIR),
        "features": feature_columns,
        "n_clusters": best_k,
        "selected_k_reason": "highest silhouette score",
        "selected_k_silhouette": float(best_silhouette),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train host attack pattern clustering model.")
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    logger = configure_logging()
    args = parse_args()

    try:
        input_file = resolve_input_file(args.input_file, logger)
        train_clustering(input_file, args.output_dir, logger)
        return 0
    except Exception as exc:
        logger.exception("Attack-pattern training failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
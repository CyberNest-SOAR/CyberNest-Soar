#!/usr/bin/env python3
"""Prepare host-level patch context from SOC logs and analyst decisions.

The script loads the SOC event dataset and the analyst escalation decisions,
merges them on ``event_id``, aggregates host context by ``dst_ip``, and writes
the prepared host context to ``host_context_prepared.json``.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_ROOT = PROJECT_ROOT / "services" / "data" / "patch_engine"
DEFAULT_SOC_FILE = PROJECT_ROOT / "soc_dataset_20260522_115157.csv"
DEFAULT_DECISIONS_FILE = PROJECT_ROOT / "LLM Datasets" / "escalation_decisions_20260522_115206.json"
DEFAULT_SUPPRESSION_FILE = PROJECT_ROOT / "LLM Datasets" / "suppression_reasons_20260522_115206.json"
DEFAULT_OUTPUT_FILE = DATA_ROOT / "host_context_prepared.json"
DEFAULT_LOG_FILE = SCRIPT_DIR / "patch_engine_prepare_data_v1.log"

SEVERE_TACTICS = {"privilege_escalation", "lateral_movement"}
VALID_CRITICALITIES = {"critical", "high", "medium", "low"}


def configure_logging(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    return logging.getLogger("patch_engine_prepare")


def resolve_input_file(filename: str, preferred_paths: Iterable[Path], logger: logging.Logger) -> Path:
    for path in preferred_paths:
        if path.exists():
            return path

    matches = list(PROJECT_ROOT.rglob(filename))
    if matches:
        logger.warning("Resolved %s via workspace search: %s", filename, matches[0])
        return matches[0]

    raise FileNotFoundError(f"Could not locate required input file: {filename}")


def load_soc_logs(csv_path: Path, logger: logging.Logger) -> pd.DataFrame:
    logger.info("Loading SOC dataset from %s", csv_path)
    df = pd.read_csv(csv_path)

    required_columns = {"event_id", "dst_ip", "attack_type", "mitre_tactic"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"SOC dataset is missing required columns: {sorted(missing)}")

    logger.info("Loaded %d SOC rows with %d columns", len(df), len(df.columns))
    return df


def load_escalation_decisions(json_path: Path, logger: logging.Logger) -> pd.DataFrame:
    logger.info("Loading analyst decisions from %s", json_path)

    try:
        df = pd.read_json(json_path)
    except ValueError:
        df = pd.read_json(json_path, lines=True)

    required_columns = {"event_id", "asset_criticality"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Escalation decisions dataset is missing required columns: {sorted(missing)}")

    # Keep additional columns for enrichment
    keep_columns = ["event_id", "asset_criticality", "risk_adjusted_priority", "repeated_behavior_score", "similar_alerts_last_hour"]
    available_columns = [c for c in keep_columns if c in df.columns]
    df = df[available_columns].copy()
    df["asset_criticality"] = df["asset_criticality"].astype("string").str.lower()

    logger.info("Loaded %d analyst decision rows", len(df))
    return df


def load_suppression_reasons(json_path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load suppression reasons and aggregate by event_id."""
    if not json_path.exists():
        logger.warning("Suppression file not found: %s", json_path)
        return pd.DataFrame()

    logger.info("Loading suppression reasons from %s", json_path)
    try:
        df = pd.read_json(json_path)
    except ValueError:
        df = pd.read_json(json_path, lines=True)

    # Aggregate suppression metrics by event_id
    suppression_agg = df.groupby("event_id", as_index=False).agg(
        historical_fp_rate=("historical_false_positive_rate", "mean"),
        recurring_alert=("recurring_alert", "any"),
    )

    logger.info("Aggregated suppression data for %d event_ids", len(suppression_agg))
    return suppression_agg


def normalize_criticality(value: object) -> str:
    if pd.isna(value):
        return "medium"

    normalized = str(value).strip().lower()
    if normalized in VALID_CRITICALITIES:
        return normalized
    return normalized or "medium"


def choose_primary_criticality(series: pd.Series) -> str:
    """Choose the highest severity criticality from a series using priority: critical > high > medium > low."""
    cleaned = series.dropna().astype(str).str.strip().str.lower()
    cleaned = cleaned[cleaned != ""]
    if cleaned.empty:
        return "medium"

    # Define priority order (higher index = lower priority)
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    valid_values = [v for v in cleaned.unique() if v in priority_order]
    
    if not valid_values:
        return "medium"
    
    # Return the value with lowest priority index (highest severity)
    return min(valid_values, key=lambda v: priority_order.get(v, 999))


def build_host_context(merged: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    working = merged.copy()
    working["dst_ip"] = working["dst_ip"].fillna("unknown")
    working["attack_type"] = working["attack_type"].astype("string").str.strip().str.lower()
    working["asset_criticality"] = working["asset_criticality"].apply(normalize_criticality)

    attack_only_severe = working["attack_type"].isin(SEVERE_TACTICS)
    working["mitre_tactic_norm"] = (
        working["mitre_tactic"]
        .astype(str)
        .str.lower()
        .str.strip()
        .str.replace(" ", "_", regex=False)
    )
    attack_type_severe = working["attack_type"].isin(SEVERE_TACTICS)
    mitre_severe = working["mitre_tactic_norm"].isin(SEVERE_TACTICS)
    working["severe_tactic_present"] = attack_type_severe | mitre_severe

    logger.info(
        "Severe tactic hosts before normalization: %d, after normalization: %d",
        int(attack_only_severe.groupby(working["dst_ip"]).any().sum()),
        int(working.groupby("dst_ip")["severe_tactic_present"].any().sum()),
    )

    grouped = (
        working.groupby("dst_ip", dropna=False)
        .agg(
            total_events=("event_id", "size"),
            unique_attack_types=("attack_type", lambda s: s.fillna("unknown").astype(str).str.lower().nunique()),
            severe_tactics_present=("severe_tactic_present", "any"),
            asset_criticality=("asset_criticality", choose_primary_criticality),
            # NEW: From SOC dataset
            true_positive_rate=("true_positive", lambda s: s.fillna(False).astype(bool).mean()),
            noise_rate=("noise", lambda s: s.fillna(False).astype(bool).mean()),
            unique_campaigns=("campaign_id", lambda s: s.dropna().nunique()),
            external_src_count=("geoip_src_country", lambda s: (s.str.upper() != "RFC1918").sum() if hasattr(s, 'str') else 0),
            # NEW: From escalation decisions
            max_risk_priority=("risk_adjusted_priority", lambda s: s.fillna(0).max()),
            max_repeated_behavior=("repeated_behavior_score", lambda s: s.fillna(0).max()),
            max_similar_alerts=("similar_alerts_last_hour", lambda s: s.fillna(0).max()),
            # NEW: From suppression reasons
            avg_historical_fp_rate=("historical_fp_rate", lambda s: s.fillna(0).mean()),
            any_recurring_alert=("recurring_alert", "any"),
        )
        .reset_index()
    )

    grouped["asset_criticality"] = grouped["asset_criticality"].fillna("medium").apply(normalize_criticality)
    grouped["severe_tactics_present"] = grouped["severe_tactics_present"].astype(bool)
    grouped["any_recurring_alert"] = grouped["any_recurring_alert"].astype(bool)

    # Fill NaNs with 0 for numeric fields
    numeric_fields = [
        "true_positive_rate", "noise_rate", "unique_campaigns", "external_src_count",
        "max_risk_priority", "max_repeated_behavior", "max_similar_alerts", "avg_historical_fp_rate"
    ]
    for field in numeric_fields:
        if field in grouped.columns:
            grouped[field] = grouped[field].fillna(0)

    logger.info("Aggregated host context for %d hosts", len(grouped))

    # Log insights
    high_noise_hosts = (grouped["avg_historical_fp_rate"] > 0.5).sum()
    multi_campaign_hosts = (grouped["unique_campaigns"] > 1).sum()
    logger.info("High-noise hosts (avg_historical_fp_rate > 0.5): %d", high_noise_hosts)
    logger.info("Multi-campaign hosts (unique_campaigns > 1): %d", multi_campaign_hosts)

    return grouped


def save_host_context(host_context: pd.DataFrame, output_path: Path, logger: logging.Logger) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = host_context.to_dict(orient="records")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2, ensure_ascii=True)
        handle.write("\n")

    logger.info("Saved host context to %s", output_path)


def prepare_data(
    soc_path: Path,
    decisions_path: Path,
    suppression_path: Path,
    output_path: Path,
    logger: logging.Logger,
) -> pd.DataFrame:
    soc_df = load_soc_logs(soc_path, logger)
    decisions_df = load_escalation_decisions(decisions_path, logger)
    suppression_df = load_suppression_reasons(suppression_path, logger)

    logger.info("Deduplicating analyst decisions by event_id")
    # Use proper aggregation for each column: criticality uses choose_primary, others use max for scores
    agg_dict = {"asset_criticality": ("asset_criticality", choose_primary_criticality)}
    if "risk_adjusted_priority" in decisions_df.columns:
        agg_dict["risk_adjusted_priority"] = ("risk_adjusted_priority", "max")
    if "repeated_behavior_score" in decisions_df.columns:
        agg_dict["repeated_behavior_score"] = ("repeated_behavior_score", "max")
    if "similar_alerts_last_hour" in decisions_df.columns:
        agg_dict["similar_alerts_last_hour"] = ("similar_alerts_last_hour", "max")
    
    decisions_deduped = decisions_df.groupby("event_id", as_index=False).agg(**agg_dict)

    logger.info("Merging SOC logs with analyst decisions using a left join on event_id")
    merged = soc_df.merge(decisions_deduped, on="event_id", how="left")
    merged["asset_criticality"] = merged["asset_criticality"].fillna("medium").apply(normalize_criticality)

    if not suppression_df.empty:
        logger.info("Merging suppression reasons with SOC data")
        merged = merged.merge(suppression_df, on="event_id", how="left")
        merged["historical_fp_rate"] = merged["historical_fp_rate"].fillna(0)
        merged["recurring_alert"] = merged["recurring_alert"].fillna(False)

    host_context = build_host_context(merged, logger)
    save_host_context(host_context, output_path, logger)
    return host_context


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare host context for patch management.")
    parser.add_argument("--soc-file", type=Path, default=DEFAULT_SOC_FILE, help="Path to the SOC CSV dataset")
    parser.add_argument(
        "--decisions-file",
        type=Path,
        default=DEFAULT_DECISIONS_FILE,
        help="Path to the escalation decisions JSON dataset",
    )
    parser.add_argument(
        "--suppression-file",
        type=Path,
        default=DEFAULT_SUPPRESSION_FILE,
        help="Path to the suppression reasons JSON dataset",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path to write host_context_prepared.json",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=DEFAULT_LOG_FILE,
        help="Path to write the preparation log",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = configure_logging(args.log_file)

    try:
        soc_path = resolve_input_file(
            args.soc_file.name,
            [args.soc_file, PROJECT_ROOT / args.soc_file.name, SCRIPT_DIR / args.soc_file.name],
            logger,
        )
        decisions_path = resolve_input_file(
            args.decisions_file.name,
            [
                args.decisions_file,
                PROJECT_ROOT / args.decisions_file.name,
                PROJECT_ROOT / "LLM Datasets" / args.decisions_file.name,
                SCRIPT_DIR / args.decisions_file.name,
            ],
            logger,
        )
        suppression_path = resolve_input_file(
            args.suppression_file.name,
            [
                args.suppression_file,
                PROJECT_ROOT / args.suppression_file.name,
                PROJECT_ROOT / "LLM Datasets" / args.suppression_file.name,
                SCRIPT_DIR / args.suppression_file.name,
            ],
            logger,
        ) if args.suppression_file.exists() or (PROJECT_ROOT / "LLM Datasets" / args.suppression_file.name).exists() else None

        host_context = prepare_data(soc_path, decisions_path, suppression_path or args.suppression_file, args.output_file, logger)
        logger.info("Preparation complete: %d host rows written", len(host_context))
        return 0
    except Exception as exc:
        logger.exception("Data preparation failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Unified inference wrapper for the patch management engine.

This module loads the trained exploit-likelihood and time-to-exploit models,
loads the prepared host context, and exposes a single pipeline API for
risk scoring and SLA tiering.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_ROOT = PROJECT_ROOT / "services" / "data" / "patch_engine"
DEFAULT_ARTIFACTS_DIR = DATA_ROOT / "artifacts" / "runtime"
DEFAULT_HOST_CONTEXT_FILE = DATA_ROOT / "host_context_prepared.json"
CURRENT_YEAR = 2026
TIME_TO_EXPLOIT_INTERVAL_NOTE = "Confidence interval is a heuristic band derived from training MAE, not a statistical CI."

CRITICALITY_WEIGHTS = {
    "critical": 1.0,
    "high": 0.7,
    "medium": 0.4,
    "low": 0.1,
}

SLA_THRESHOLDS = [
    {
        "tier": "critical",
        "min": 0.75,
        "sla_days": 14,
        "description": "Ransomware/known exploit (CISA KEV) — patch within 14 days"
    },
    {
        "tier": "high",
        "min": 0.50,
        "sla_days": 21,
        "description": "Baseline known exploited (CISA KEV catalog) — patch within 21 days"
    },
    {
        "tier": "medium",
        "min": 0.25,
        "sla_days": 30,
        "description": "Standard vulnerability patch — patch within 30 days"
    },
    {
        "tier": "low",
        "min": 0.0,
        "sla_days": 45,
        "description": "Non-critical patch — patch within 45 days"
    },
]

REQUIRED_FEATURES = ["epss", "percentile", "cvss", "cve_age_years"]


@dataclass(frozen=True)
class HostContext:
    dst_ip: str
    total_events: int
    unique_attack_types: int
    severe_tactics_present: bool
    asset_criticality: str
    # NEW fields with defaults for backward compatibility
    true_positive_rate: float = 0.0
    noise_rate: float = 0.0
    unique_campaigns: int = 0
    external_src_count: int = 0
    max_risk_priority: float = 0.0
    max_repeated_behavior: float = 0.0
    max_similar_alerts: float = 0.0
    avg_historical_fp_rate: float = 0.0
    any_recurring_alert: bool = False


def configure_logging(verbose: bool = True) -> logging.Logger:
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("patch_engine_models")


class PatchEngineModels:
    """Unified interface for exploit likelihood, time-to-exploit, and host-aware risk scoring."""

    def __init__(
        self,
        artifacts_dir: Optional[Path] = None,
        host_context_file: Optional[Path] = None,
        verbose: bool = True,
    ) -> None:
        self.verbose = verbose
        self.log = configure_logging(verbose)
        self.artifacts_dir = Path(artifacts_dir or DEFAULT_ARTIFACTS_DIR)
        self.host_context_file = Path(host_context_file or DEFAULT_HOST_CONTEXT_FILE)

        if not self.artifacts_dir.exists():
            raise FileNotFoundError(f"Artifacts directory not found: {self.artifacts_dir}")
        if not self.host_context_file.exists():
            raise FileNotFoundError(f"Host context file not found: {self.host_context_file}")

        self.models: Dict[str, Any] = {}
        self.manifests: Dict[str, Dict[str, Any]] = {}
        self.host_context = self._load_host_context(self.host_context_file)
        self.host_context_index = self._build_host_context_index(self.host_context)

        if self.verbose:
            self.log.info("Initializing PatchEngineModels from %s", self.artifacts_dir)
            self.log.info("Loaded host context from %s", self.host_context_file)

        self._load_models()

    def _load_models(self) -> None:
        self._load_model_pair("exploit_likelihood_v0")
        self._load_model_pair("time_to_exploit_v0")

    def _load_model_pair(self, model_name: str) -> None:
        model_path = self.artifacts_dir / f"{model_name}.joblib"
        manifest_path = self.artifacts_dir / f"{model_name}.manifest.json"

        if not model_path.exists():
            if self.verbose:
                self.log.warning("Model not found: %s", model_path)
            return

        try:
            self.models[model_name] = joblib.load(model_path)
            if manifest_path.exists():
                with open(manifest_path, "r", encoding="utf-8") as handle:
                    self.manifests[model_name] = json.load(handle)
            else:
                self.manifests[model_name] = {}
            if self.verbose:
                self.log.info("Loaded %s", model_name)
        except Exception as exc:
            self.log.error("Failed to load %s: %s", model_name, exc)

    @staticmethod
    def _load_host_context(path: Path) -> pd.DataFrame:
        df = pd.read_json(path)
        required_columns = {"dst_ip", "total_events", "unique_attack_types", "severe_tactics_present", "asset_criticality"}
        missing = required_columns - set(df.columns)
        if missing:
            raise ValueError(f"Host context is missing required columns: {sorted(missing)}")
        return df

    @staticmethod
    def _build_host_context_index(df: pd.DataFrame) -> Dict[str, HostContext]:
        index: Dict[str, HostContext] = {}
        for row in df.itertuples(index=False):
            dst_ip = str(getattr(row, "dst_ip"))
            index[dst_ip] = HostContext(
                dst_ip=dst_ip,
                total_events=int(getattr(row, "total_events", 0) or 0),
                unique_attack_types=int(getattr(row, "unique_attack_types", 0) or 0),
                severe_tactics_present=bool(getattr(row, "severe_tactics_present", False)),
                asset_criticality=str(getattr(row, "asset_criticality", "medium") or "medium").lower(),
                # NEW optional fields with defaults
                true_positive_rate=float(getattr(row, "true_positive_rate", 0.0) or 0.0),
                noise_rate=float(getattr(row, "noise_rate", 0.0) or 0.0),
                unique_campaigns=int(getattr(row, "unique_campaigns", 0) or 0),
                external_src_count=int(getattr(row, "external_src_count", 0) or 0),
                max_risk_priority=float(getattr(row, "max_risk_priority", 0.0) or 0.0),
                max_repeated_behavior=float(getattr(row, "max_repeated_behavior", 0.0) or 0.0),
                max_similar_alerts=float(getattr(row, "max_similar_alerts", 0.0) or 0.0),
                avg_historical_fp_rate=float(getattr(row, "avg_historical_fp_rate", 0.0) or 0.0),
                any_recurring_alert=bool(getattr(row, "any_recurring_alert", False)),
            )
        return index

    def is_ready(self) -> bool:
        return "exploit_likelihood_v0" in self.models and "time_to_exploit_v0" in self.models

    def get_loaded_models(self) -> List[str]:
        return list(self.models.keys())

    @staticmethod
    def _validate_range(name: str, value: float, lower: float, upper: float) -> None:
        if not (lower <= value <= upper):
            raise ValueError(f"{name} must be in [{lower}, {upper}], got {value}")

    def _resolve_host_context(self, agent_id: str) -> HostContext:
        key = str(agent_id)
        if key in self.host_context_index:
            return self.host_context_index[key]

        # Fallback for callers that pass a non-IP identifier.
        return HostContext(
            dst_ip=key,
            total_events=0,
            unique_attack_types=0,
            severe_tactics_present=False,
            asset_criticality="medium",
        )

    def _derive_threat_multiplier(self, host_context: HostContext) -> float:
        """
        Calculate host-aware threat multiplier using ONLY real analyst-enriched context fields.
        
        Implements data-driven logic based on actual SOC analyst decisions and observed behaviors,
        replacing arbitrary heuristics with ground-truth signals from:
        - escalation_decisions_20260522_115206.json (analyst verdicts)
        - suppression_reasons_20260522_115206.json (false positive patterns)
        - host_context_prepared.json (enriched behavioral data)
        
        Logic:
        - Base multiplier: 1.0
        - If max_repeated_behavior >= 8 (sustained targeting from escalation data): +0.2
        - If severe_tactics_present (MITRE ATT&CK signals): +0.3
        - If true_positive_rate > 0.5 (analyst confidence from verdicts): +0.2
        - If avg_historical_fp_rate > 0.4 (alert fatigue from suppressions): -0.2
        - Final cap: [0.5, 2.0] to prevent extreme outliers
        
        Returns: Multiplier in [0.5, 2.0] to apply to base risk_score
        """
        multiplier = 1.0
        
        # Signal 1: Persistence detection from escalation decisions
        if host_context.max_repeated_behavior >= 8:
            multiplier += 0.2
            self.log.debug(
                "Sustained targeting detected (max_repeated_behavior=%d): +0.2",
                host_context.max_repeated_behavior
            )
        
        # Signal 2: MITRE ATT&CK severity (from analyst context preparation)
        if host_context.severe_tactics_present:
            multiplier += 0.3
            self.log.debug("MITRE ATT&CK severe tactics detected: +0.3")
        
        # Signal 3: Analyst confidence from verdicts
        if host_context.true_positive_rate > 0.5:
            multiplier += 0.2
            self.log.debug(
                "High analyst confidence (TP rate=%.2f): +0.2",
                host_context.true_positive_rate
            )
        
        # Signal 4: Alert fatigue penalty from suppression reasons
        if host_context.avg_historical_fp_rate > 0.4:
            multiplier -= 0.2
            self.log.debug(
                "Alert fatigue detected (FP rate=%.2f): -0.2",
                host_context.avg_historical_fp_rate
            )
        
        # Final clipping to reasonable bounds [0.5, 2.0]
        final_multiplier = float(np.clip(multiplier, 0.5, 2.0))
        self.log.debug(
            "Final threat multiplier: %.3f (clipped from %.3f)",
            final_multiplier,
            multiplier
        )
        return final_multiplier

    def _build_feature_frame(
        self,
        epss: float,
        percentile: float,
        cvss_base: float,
        cve_age_years: int,
        feature_order: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        row = {
            "epss": epss,
            "percentile": percentile,
            "cvss": cvss_base,
            "cve_age_years": cve_age_years,
        }
        columns = feature_order or REQUIRED_FEATURES
        return pd.DataFrame([[row.get(column, 0) for column in columns]], columns=columns)

    def predict_exploit_likelihood(
        self,
        epss: float,
        percentile: float,
        cvss_base: float,
        cve_age_years: int,
    ) -> Optional[float]:
        if "exploit_likelihood_v0" not in self.models:
            self.log.warning("exploit_likelihood_v0 model not loaded")
            return None

        self._validate_range("EPSS", epss, 0.0, 1.0)
        self._validate_range("Percentile", percentile, 0.0, 100.0)
        self._validate_range("CVSS", cvss_base, 0.0, 10.0)
        if cve_age_years < 0:
            raise ValueError(f"CVE age cannot be negative, got {cve_age_years}")

        feature_order = self.manifests.get("exploit_likelihood_v0", {}).get("features", REQUIRED_FEATURES)
        features = self._build_feature_frame(epss, percentile, cvss_base, cve_age_years, feature_order)

        proba = self.models["exploit_likelihood_v0"].predict_proba(features)[0, 1]
        return float(proba)

    def predict_time_to_exploit(
        self,
        epss: float,
        percentile: float,
        cvss_base: float,
        cve_age_years: int,
    ) -> Optional[int]:
        if "time_to_exploit_v0" not in self.models:
            self.log.warning("time_to_exploit_v0 model not loaded")
            return None

        self._validate_range("EPSS", epss, 0.0, 1.0)
        self._validate_range("Percentile", percentile, 0.0, 100.0)
        self._validate_range("CVSS", cvss_base, 0.0, 10.0)
        if cve_age_years < 0:
            raise ValueError(f"CVE age cannot be negative, got {cve_age_years}")

        feature_order = self.manifests.get("time_to_exploit_v0", {}).get("features", REQUIRED_FEATURES)
        features = self._build_feature_frame(epss, percentile, cvss_base, cve_age_years, feature_order)

        predicted_log_days = self.models["time_to_exploit_v0"].predict(features)[0]
        predicted_days = int(np.clip(np.expm1(predicted_log_days), 1, 1500))
        return predicted_days

    def calculate_business_risk_score(
        self,
        exploit_likelihood: float,
        cve_age_years: int,
        host_criticality: str = "medium",
        threat_multiplier: float = 1.0,
    ) -> float:
        self._validate_range("Exploit likelihood", exploit_likelihood, 0.0, 1.0)
        if cve_age_years < 0:
            raise ValueError(f"CVE age cannot be negative, got {cve_age_years}")
        if host_criticality not in CRITICALITY_WEIGHTS:
            raise ValueError(f"Invalid criticality: {host_criticality}")
        if threat_multiplier < 0:
            raise ValueError(f"Threat multiplier cannot be negative, got {threat_multiplier}")

        criticality_weight = CRITICALITY_WEIGHTS[host_criticality]
        age_factor = 1.0 + (cve_age_years / 10.0)
        risk_score = exploit_likelihood * criticality_weight * age_factor * threat_multiplier
        return float(np.clip(risk_score, 0.0, 1.0))

    def determine_sla_tier(self, risk_score: float) -> Dict[str, Any]:
        self._validate_range("Risk score", risk_score, 0.0, 1.0)

        for tier in SLA_THRESHOLDS:
            if risk_score >= tier["min"]:
                return {
                    "tier": tier["tier"],
                    "sla_days": tier["sla_days"],
                    "description": tier["description"],
                }

        return {
            "tier": "low",
            "sla_days": 30,
            "description": "Patch within 30 days",
        }

    def predict_full_pipeline(
        self,
        cve_id: str,
        epss: float,
        percentile: float,
        cvss_base: float,
        cve_year: int,
        agent_id: str,
    ) -> Dict[str, Any]:
        current_year = datetime.now(timezone.utc).year
        cve_age_years = max(0, current_year - cve_year)

        host_context = self._resolve_host_context(agent_id)
        resolved_host_criticality = host_context.asset_criticality if host_context.asset_criticality in CRITICALITY_WEIGHTS else "medium"
        threat_multiplier = self._derive_threat_multiplier(host_context)

        exploit_likelihood = self.predict_exploit_likelihood(epss, percentile, cvss_base, cve_age_years)
        time_to_exploit_days = self.predict_time_to_exploit(epss, percentile, cvss_base, cve_age_years)

        if exploit_likelihood is None or time_to_exploit_days is None:
            raise RuntimeError("Models not fully loaded")

        time_manifest = self.manifests.get("time_to_exploit_v0", {})
        mae_days = float(time_manifest.get("mae_days", 0.0))
        time_interval = {
            "lower": int(max(1, time_to_exploit_days - mae_days)),
            "upper": int(time_to_exploit_days + mae_days),
            "note": TIME_TO_EXPLOIT_INTERVAL_NOTE,
        }

        business_risk_score = self.calculate_business_risk_score(
            exploit_likelihood=exploit_likelihood,
            cve_age_years=cve_age_years,
            host_criticality=resolved_host_criticality,
            threat_multiplier=threat_multiplier,
        )
        sla = self.determine_sla_tier(business_risk_score)

        return {
            "cve_id": cve_id,
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inputs": {
                "epss": float(epss),
                "percentile": float(percentile),
                "cvss_base": float(cvss_base),
                "cve_year": int(cve_year),
                "cve_age_years": int(cve_age_years),
            },
            "host_context": {
                "dst_ip": host_context.dst_ip,
                "asset_criticality": resolved_host_criticality,
                "total_events": host_context.total_events,
                "unique_attack_types": host_context.unique_attack_types,
                "severe_tactics_present": host_context.severe_tactics_present,
                "threat_multiplier": float(threat_multiplier),
                "context_found": host_context.total_events > 0,
            },
            "predictions": {
                "exploit_likelihood": float(exploit_likelihood),
                "exploit_likelihood_pct": f"{exploit_likelihood * 100:.1f}%",
                "time_to_exploit_days": int(time_to_exploit_days),
                "time_to_exploit_confidence": "low",
                "time_to_exploit_note": "Estimate based on heuristic labels — treat as order-of-magnitude only",
                "time_to_exploit_days_confidence_interval": time_interval,
                "business_risk_score": float(business_risk_score),
                "business_risk_pct": f"{business_risk_score * 100:.1f}%",
                "sla": sla,
                "sla_policy_note": "Thresholds are hard-coded policy defaults and should be calibrated against observed risk distributions.",
            },
            "models_used": self.get_loaded_models(),
            "ready": self.is_ready(),
        }


def example_usage() -> None:
    engine = PatchEngineModels(verbose=True)
    result = engine.predict_full_pipeline(
        cve_id="CVE-2024-1234",
        epss=0.92,
        percentile=95.5,
        cvss_base=9.8,
        cve_year=2024,
        agent_id="10.0.0.1",
    )
    print(json.dumps(result, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patch engine unified inference wrapper.")
    parser.add_argument("--example", action="store_true", help="Run a sample prediction")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.example:
        example_usage()

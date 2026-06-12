"""
Patch Engine ML Service — Team 2 AI Models Integration

Loads pre-trained sklearn models for:
- Exploit likelihood prediction
- Time-to-exploit estimation
- Attack pattern detection

Models are trained by notebooks in services/patch_engine/ and saved to
artifacts/patch_engine/ as joblib + manifest JSON files.
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
import joblib
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# Paths to models (relative to backend/app)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "services" / "data" / "patch_engine"
ARTIFACTS_DIR = DATA_DIR / "artifacts" / "runtime"


class PatchEngineModels:
    """Singleton manager for all three patch engine ML models."""

    _instance = None
    _models = {}
    _manifests = {}
    _loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def initialize():
        """Load all models on startup."""
        instance = PatchEngineModels()
        if not instance._loaded:
            instance._load_models()
            instance._loaded = True

    def _load_models(self):
        """Load exploit_likelihood, time_to_exploit, and attack_patterns models."""
        models_to_load = [
            "exploit_likelihood_v0",
            "time_to_exploit_v0",
            "attack_patterns_kmeans_v0",
        ]

        for model_name in models_to_load:
            model_path = ARTIFACTS_DIR / f"{model_name}.joblib"
            manifest_path = ARTIFACTS_DIR / f"{model_name}.manifest.json"

            if model_path.exists():
                try:
                    self._models[model_name] = joblib.load(model_path)
                    if manifest_path.exists():
                        with open(manifest_path) as f:
                            self._manifests[model_name] = json.load(f)
                    else:
                        self._manifests[model_name] = {}
                    log.info(f"Loaded {model_name}")
                except Exception as e:
                    log.error(f"Failed to load {model_name}: {e}")
            else:
                log.warning(f"Model not found: {model_path} (using defaults)")

    def get_model(self, name: str):
        """Retrieve a loaded model."""
        return self._models.get(name)

    def get_manifest(self, name: str):
        """Retrieve model metadata."""
        return self._manifests.get(name, {})

    def is_loaded(self, name: str) -> bool:
        """Check if a model is loaded."""
        return name in self._models


class PatchEnginePredictor:
    """High-level API for making patch engine predictions."""

    def __init__(self):
        PatchEngineModels.initialize()
        self.models = PatchEngineModels()
        self.current_year = datetime.now(timezone.utc).year

    @staticmethod
    def _build_feature_row(manifest: dict, values: dict) -> pd.DataFrame:
        feature_names = manifest.get("features", [])
        return pd.DataFrame([[values.get(name, 0) for name in feature_names]], columns=feature_names)

    def predict_exploit_likelihood(
        self,
        cve_id: str,
        epss: float,
        percentile: float,
        cvss: float,
        cve_year: int,
    ) -> Dict[str, Any]:
        """
        Predict if a CVE will be actively exploited (KEV probability).
        Returns: {'probability': float, 'status': 'loaded'|'fallback', 'reason': str}
        """
        model = self.models.get_model("exploit_likelihood_v0")
        if not model:
            return {"probability": min(epss, 0.9), "status": "fallback", "reason": "Model not loaded, using EPSS"}

        try:
            cve_age = max(0, self.current_year - cve_year)
            manifest = self.models.get_manifest("exploit_likelihood_v0")
            features = self._build_feature_row(
                manifest,
                {
                    "epss": epss,
                    "percentile": percentile,
                    "cvss": cvss,
                    "cve_age_years": cve_age,
                },
            )
            prob = model.predict_proba(features)[0, 1]
            return {"probability": float(prob), "status": "loaded", "reason": "ML prediction"}
        except Exception as e:
            log.warning(f"Exploit likelihood prediction failed for {cve_id}: {e}")
            return {"probability": min(epss, 0.9), "status": "fallback", "reason": str(e)}

    def predict_time_to_exploit(self, cve_id: str, epss: float, cvss: float, cve_year: int) -> Dict[str, Any]:
        """
        Predict days until active exploitation.
        Returns: {'days': float, 'status': 'loaded'|'fallback', 'reason': str}
        """
        model = self.models.get_model("time_to_exploit_v0")
        if not model:
            # Fallback: high CVSS + high EPSS = faster exploitation
            days = max(1, 30 - (cvss * 2 + epss * 10))
            return {
                "days": days,
                "status": "fallback",
                "reason": "Model not loaded, using heuristic",
                "confidence_interval": {
                    "lower": max(1, days - 10),
                    "upper": days + 10,
                    "note": "Heuristic fallback interval",
                },
            }

        try:
            cve_age = max(0, self.current_year - cve_year)
            percentile = 0.0
            manifest = self.models.get_manifest("time_to_exploit_v0")
            features = self._build_feature_row(
                manifest,
                {
                    "epss": epss,
                    "percentile": percentile,
                    "cvss": cvss,
                    "cve_age_years": cve_age,
                },
            )
            days = max(1, float(model.predict(features)[0]))
            mae_days = float(manifest.get("mae_days", 0.0))
            return {
                "days": days,
                "status": "loaded",
                "reason": "ML prediction",
                "confidence_interval": {
                    "lower": max(1, days - mae_days),
                    "upper": days + mae_days,
                    "note": "Heuristic band from training MAE",
                },
            }
        except Exception as e:
            log.warning(f"Time-to-exploit prediction failed for {cve_id}: {e}")
            return {
                "days": 30,
                "status": "fallback",
                "reason": str(e),
                "confidence_interval": {"lower": 1, "upper": 60, "note": "Fallback interval"},
            }

    def detect_attack_patterns(self, raw_logs: str) -> Dict[str, Any]:
        """
        Detect attack patterns in raw logs (regex-based + model if available).
        Returns: {'patterns': [str], 'confidence': float, 'status': 'loaded'|'fallback'}
        """
        patterns = []

        # Regex: look for common attack indicators
        attack_signatures = [
            (r"(?i)(sql\s*injection|union\s*select)", "SQL Injection"),
            (r"(?i)(cross.?site.?scripting|<script|javascript:)", "XSS"),
            (r"(?i)(buffer\s*overflow|stack\s*overflow)", "Buffer Overflow"),
            (r"(?i)(privilege\s*escalation|sudo|whoami)", "Privilege Escalation"),
            (r"(?i)(credential|password|auth.*fail)", "Credential Attack"),
            (r"(?i)(brute.?force|dictionary|wordlist)", "Brute Force"),
        ]

        for regex, label in attack_signatures:
            if re.search(regex, raw_logs):
                patterns.append(label)

        model = self.models.get_model("attack_patterns_kmeans_v0")
        confidence = 0.7 if patterns else 0.3

        return {
            "patterns": list(set(patterns)),  # deduplicate
            "confidence": confidence,
            "status": "loaded" if model else "fallback"
        }


def extract_cves_from_alert(alert_data: Dict[str, Any]) -> list:
    """
    Extract CVE IDs from enrichment tags or raw data.
    Returns list of CVE ID strings (e.g., ['CVE-2024-1234', 'CVE-2023-5678'])
    """
    cves = []
    tags = alert_data.get("tags", [])

    # Extract from tags (e.g., 'vuln:CVE-2013-4235')
    for tag in tags:
        match = re.search(r"(CVE-\d{4}-\d{4,})", str(tag))
        if match:
            cves.append(match.group(1))

    # Extract from raw_data description
    description = alert_data.get("description", "")
    matches = re.findall(r"(CVE-\d{4}-\d{4,})", description)
    cves.extend(matches)

    # Extract from raw vulnerability data
    vulnerabilities = alert_data.get("raw_data", {}).get("vulnerability", [])
    if not isinstance(vulnerabilities, list):
        vulnerabilities = [vulnerabilities] if vulnerabilities else []
    for vuln in vulnerabilities:
        cve = vuln.get("cve")
        if cve:
            cves.append(cve)

    return list(set(cves))  # deduplicate


def calculate_patch_priority(exploit_prob: float, time_to_exploit: float, cvss: float) -> tuple:
    """
    Calculate SLA-based priority and action.
    Returns: (priority: 'critical'|'high'|'medium'|'low', action: str)
    """
    score = (exploit_prob * 100 + cvss * 10 + (30 - time_to_exploit)) / 3

    if score > 75 or (exploit_prob > 0.8 and cvss >= 8.0):
        return "critical", "Patch immediately (emergency)"
    elif score > 60 or (exploit_prob > 0.6 and cvss >= 7.0):
        return "high", "Patch within 24 hours"
    elif score > 40 or (exploit_prob > 0.3 and cvss >= 6.0):
        return "medium", "Patch within 7 days"
    else:
        return "low", "Monitor and patch in routine cycle"

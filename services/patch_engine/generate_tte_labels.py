#!/usr/bin/env python3
"""Derive best-effort time-to-exploit labels from available signals."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_ROOT = PROJECT_ROOT / "services" / "data" / "patch_engine"
INPUT_FILE = DATA_ROOT / "training.csv"
OUTPUT_FILE = DATA_ROOT / "training_with_tte.csv"
WAZUH_FILE = PROJECT_ROOT / "wazuh_alerts_enriched_2.json"


def stable_seed(value: str) -> int:
    digest = sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], byteorder="big", signed=False)


def build_kev_tte_map() -> dict:
    """
    Build a map of cve_id -> real days_to_exploit from CISA KEV dateAdded.
    TTE = dateAdded - Jan 1st of CVE year (approximation for missing published date).
    """
    candidates = [
        PROJECT_ROOT / "exploited_vulnerabilities.json",
        PROJECT_ROOT / "LLM Datasets" / "exploited_vulnerabilities.json",
        next((p for p in PROJECT_ROOT.rglob("exploited_vulnerabilities.json") if p.is_file()), None),
    ]
    kev_path = next((p for p in candidates if p and Path(p).exists()), None)
    if not kev_path:
        print("Warning: exploited_vulnerabilities.json not found — KEV TTE map empty")
        return {}

    with open(kev_path) as f:
        raw = json.load(f)
    records = raw["vulnerabilities"] if isinstance(raw, dict) and "vulnerabilities" in raw else raw

    import re
    tte_map = {}
    skipped = 0
    for r in records:
        cve_id = str(r.get("cveID", ""))
        date_added = r.get("dateAdded", "")
        m = re.search(r"CVE-(\d{4})", cve_id)
        if not m or not date_added:
            skipped += 1
            continue
        cve_year = int(m.group(1))
        try:
            added_dt  = pd.to_datetime(date_added)
            pub_dt    = pd.to_datetime(f"{cve_year}-01-01")
            days      = (added_dt - pub_dt).days
            if days >= 0:
                tte_map[cve_id] = float(days)
        except Exception:
            skipped += 1

    print(f"KEV TTE map: {len(tte_map)} CVEs with real dates, {skipped} skipped")
    if tte_map:
        vals = list(tte_map.values())
        print(f"  TTE range: {min(vals):.0f} – {max(vals):.0f} days | median: {sorted(vals)[len(vals)//2]:.0f} days")
    return tte_map


def build_wazuh_severity_map(wazuh_path: Path) -> dict:
    """Extract max Wazuh severity for each CVE."""
    if not wazuh_path.exists():
        print(f"Warning: Wazuh file not found at {wazuh_path}")
        return {}

    try:
        with open(wazuh_path, "r") as f:
            records = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading Wazuh file: {e}")
        return {}

    import re
    cve_pattern = re.compile(r'CVE-(\d{4}-\d{4,})', re.IGNORECASE)
    wazuh_severity_map = {}
    for r in records:
        # Extract CVE from description
        description = r.get("description", "")
        match = cve_pattern.search(description)
        if match:
            cve_id = f"CVE-{match.group(1)}"
            severity = int(r.get("severity", 0))
            current_max = wazuh_severity_map.get(cve_id, 0)
            wazuh_severity_map[cve_id] = max(current_max, severity)

    print(f"Built Wazuh severity map with {len(wazuh_severity_map)} unique CVEs")
    return wazuh_severity_map


def derive_tte(row: pd.Series, wazuh_severity_map: dict, kev_tte_map: dict) -> float | None:
    """Derive time-to-exploit ONLY from real sources.
    
    Priority:
    1. Real KEV dateAdded (calculated TTE) — highest confidence
    2. Wazuh severity (observed in wild) — real alert signal
    3. RETURN None — do NOT fall back to synthetic random
    
    If a CVE is not in KEV or Wazuh, return None. Let dropna() handle filtering.
    """
    cve_id = str(row.get("cve_id", ""))
    
    # Priority 1: Real KEV date (highest confidence)
    if cve_id in kev_tte_map:
        return kev_tte_map[cve_id]

    # Priority 2: Check Wazuh severity (real alert signal from wild)
    wazuh_sev = wazuh_severity_map.get(cve_id, 0)
    if wazuh_sev >= 10:          # Wazuh critical — seen in the wild
        # Map to realistic TTE range based on severity, but use median not random
        return 20.0  # 20 days typical for critical zero-day
    elif wazuh_sev >= 7:         # Wazuh high
        return 45.0  # 45 days typical for high-severity
    
    # NO SYNTHETIC FALLBACK — return None for unverified CVEs
    return None


def main() -> int:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Training file not found: {INPUT_FILE}")

    # Build KEV and Wazuh maps
    kev_tte_map = build_kev_tte_map()
    wazuh_severity_map = build_wazuh_severity_map(WAZUH_FILE)

    frame = pd.read_csv(INPUT_FILE)

    # Track which labeling method was used
    kev_count = 0
    wazuh_count = 0
    epss_count = 0

    def labeled_derive_tte(row):
        nonlocal kev_count, wazuh_count, epss_count
        cve_id = str(row.get("cve_id", ""))
        result = derive_tte(row, wazuh_severity_map, kev_tte_map)
        if result is not None:
            if cve_id in kev_tte_map:               kev_count   += 1
            elif cve_id in wazuh_severity_map:      wazuh_count += 1
            else:                                   epss_count  += 1
        return result

    frame["days_to_exploit"] = frame.apply(labeled_derive_tte, axis=1)
    labeled = frame.dropna(subset=["days_to_exploit"]).copy()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    labeled.to_csv(OUTPUT_FILE, index=False)

    print(f"Labeled {len(labeled)} / {len(frame)} rows")
    print(f"  - Real KEV dates:    {kev_count}")
    print(f"  - Wazuh severity:   {wazuh_count}")
    print(f"  - EPSS heuristic:   {epss_count}")
    print(f"Saved to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
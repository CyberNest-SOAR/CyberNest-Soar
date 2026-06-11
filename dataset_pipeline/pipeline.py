"""
dataset_pipeline/pipeline.py — Main processing pipeline orchestrator.

Coordinates:
  1. Dataset download / synthetic generation
  2. Parsing into UnifiedAlert schema
  3. Enrichment (GeoIP, ATT&CK, threat intel)
  4. AI Augmentation (verdicts, clusters, noise, playbooks)
  5. Attack chain generation
  6. SOC Reasoning (7-step transformation for LLM-ready dataset)
  7. Export (NDJSON, CSV, OpenSearch bulk, TheHive, LLM datasets)
"""
import json
import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

from config.settings import (
    RAW_DIR, PROCESSED_DIR, OUTPUTS_DIR, TOTAL_EVENTS_TARGET,
)
from downloaders.download_manager import DatasetDownloadManager
from downloaders.registry import register_all_downloaders
from parsers.base import NDJSONParser
from parsers.normalizer import UnifiedAlert
from enrichment.enrichment_engine import enrich_alerts
from augmentation.analyst_verdicts import simulate_analyst_verdicts
from augmentation.cluster_engine import cluster_alerts
from augmentation.noise_injector import inject_soc_noise
from augmentation.playbook_simulator import simulate_playbooks
from attack_chains.chain_builder import build_attack_chains
from soc_reasoning.reasoning_pipeline import transform_to_soc_reasoning_dataset
from soc_reasoning.reasoning_pipeline import (
    extract_analyst_notes_dataset,
    extract_suppression_reason_dataset,
    extract_escalation_decision_dataset,
)
from export.exporters import export_ndjson, export_csv, export_opensearch_bulk, export_thehive
from export.opensearch import bulk_index

logger = logging.getLogger("pipeline")


class SOCDatasetPipeline:
    def __init__(self, target_events: int = TOTAL_EVENTS_TARGET):
        self.target_events = target_events
        self.alerts: List[UnifiedAlert] = []
        self.stats: Dict[str, Any] = {}

    def run_download(self) -> Dict[str, List[Path]]:
        logger.info("=" * 60)
        logger.info("STEP 1: Downloading datasets")
        logger.info("=" * 60)
        manager = DatasetDownloadManager()
        register_all_downloaders(manager)
        results = manager.download_all()
        logger.info("\n" + manager.summary())
        self.stats["download"] = {k: len(v) for k, v in results.items()}
        return results

    def run_parse(self, download_results: Dict[str, List[Path]]) -> List[UnifiedAlert]:
        logger.info("=" * 60)
        logger.info("STEP 2: Parsing datasets into UnifiedAlert schema")
        logger.info("=" * 60)
        all_alerts = []
        for name, files in download_results.items():
            if not files:
                continue
            logger.info("Parsing %s (%d files) ...", name, len(files))
            parser = NDJSONParser(files)
            parser.name = name
            parsed = parser.parse_all()
            all_alerts.extend(parsed)
        logger.info("Total parsed alerts: %d", len(all_alerts))
        self.stats["parse"] = len(all_alerts)
        return all_alerts

    def run_enrich(self, alerts: List[UnifiedAlert]) -> List[UnifiedAlert]:
        logger.info("=" * 60)
        logger.info("STEP 3: Enrichment (GeoIP, ATT&CK, threat scores)")
        logger.info("=" * 60)
        enriched = enrich_alerts(alerts)
        logger.info("Enriched %d alerts", len(enriched))
        self.stats["enrich"] = len(enriched)
        return enriched

    def run_augment(self, alerts: List[UnifiedAlert]) -> List[UnifiedAlert]:
        logger.info("=" * 60)
        logger.info("STEP 4: AI Augmentation (verdicts, clusters, noise, playbooks)")
        logger.info("=" * 60)
        alerts = simulate_analyst_verdicts(alerts)
        alerts = inject_soc_noise(alerts)
        alerts = cluster_alerts(alerts)
        alerts = simulate_playbooks(alerts)
        logger.info("Augmented %d alerts", len(alerts))
        self.stats["augment"] = len(alerts)
        return alerts

    def run_chains(self, alerts: List[UnifiedAlert]) -> List[UnifiedAlert]:
        logger.info("=" * 60)
        logger.info("STEP 5: Attack chain correlation")
        logger.info("=" * 60)
        alerts = build_attack_chains(alerts)
        logger.info("Attack chains built: %d total alerts", len(alerts))
        self.stats["chains"] = len(alerts)
        return alerts

    def run_reasoning(self, alerts: List[UnifiedAlert]) -> List[UnifiedAlert]:
        logger.info("=" * 60)
        logger.info("STEP 6: SOC Reasoning (7-stage LLM-ready transformation)")
        logger.info("=" * 60)
        alerts = transform_to_soc_reasoning_dataset(alerts)
        self.stats["reasoning"] = len(alerts)
        return alerts

    def run_export(self, alerts: List[UnifiedAlert]) -> Dict[str, Any]:
        logger.info("=" * 60)
        logger.info("STEP 7: Export + LLM training datasets")
        logger.info("=" * 60)
        results = {}
        results["ndjson"] = str(export_ndjson(alerts))
        results["csv"] = str(export_csv(alerts))
        results["opensearch_bulk"] = str(export_opensearch_bulk(alerts))
        results["thehive"] = export_thehive(alerts)

        # LLM-specific training datasets
        llm_dir = OUTPUTS_DIR / "llm_datasets"
        llm_dir.mkdir(exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")

        nd = extract_analyst_notes_dataset(alerts)
        p = llm_dir / f"analyst_notes_{ts}.json"
        p.write_text(json.dumps(nd, indent=2))
        results["llm_analyst_notes"] = str(p)

        sd = extract_suppression_reason_dataset(alerts)
        p = llm_dir / f"suppression_reasons_{ts}.json"
        p.write_text(json.dumps(sd, indent=2))
        results["llm_suppression_reasons"] = str(p)

        ed = extract_escalation_decision_dataset(alerts)
        p = llm_dir / f"escalation_decisions_{ts}.json"
        p.write_text(json.dumps(ed, indent=2))
        results["llm_escalation_decisions"] = str(p)

        try:
            results["opensearch_index"] = bulk_index(alerts)
        except Exception as e:
            logger.warning("OpenSearch index failed: %s", e)
            results["opensearch_index"] = {"error": str(e)}
        self.stats["export"] = results
        return results

    def run_all(self) -> Dict[str, Any]:
        t0 = time.time()
        downloads = self.run_download()
        self.alerts = self.run_parse(downloads)
        self.alerts = self.run_enrich(self.alerts)
        self.alerts = self.run_augment(self.alerts)
        self.alerts = self.run_chains(self.alerts)
        self.alerts = self.run_reasoning(self.alerts)
        exports = self.run_export(self.alerts)
        elapsed = time.time() - t0

        self.stats["elapsed_seconds"] = round(elapsed, 1)
        self.stats["final_alert_count"] = len(self.alerts)
        self._summarize()

        return self.stats

    def _summarize(self):
        from collections import Counter
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE — SUMMARY")
        print("=" * 60)
        print(f"  Total alerts:    {len(self.alerts)}")
        print(f"  Target:          {self.target_events}")
        print(f"  Time:            {self.stats.get('elapsed_seconds', 0):.1f}s")
        print()
        atk = Counter(a.attack_type for a in self.alerts if a.attack_type)
        print("  Attack types:")
        for k, v in atk.most_common(10):
            print(f"    {k:25s} {v:6d}")
        print()
        verdicts = Counter(a.analyst_verdict for a in self.alerts if a.analyst_verdict)
        print("  Analyst verdicts:")
        for k, v in verdicts.most_common():
            print(f"    {k:25s} {v:6d}")
        print()
        sev = Counter(a.severity_label for a in self.alerts)
        print("  Severity:")
        for k in ["critical", "high", "medium", "low", "info"]:
            print(f"    {k:25s} {sev.get(k, 0):6d}")
        print()
        # SOC reasoning stats
        maintained = Counter(bool(a.maintenance_window) for a in self.alerts)
        suppressed = Counter(bool(a.suppression_hit) for a in self.alerts)
        scanning = Counter(bool(a.vulnerability_scan) for a in self.alerts)
        print("  SOC Reasoning:")
        print(f"    {'maintenance_window':25s} {maintained.get(True,0):6d}")
        print(f"    {'suppression_hit':25s} {suppressed.get(True,0):6d}")
        print(f"    {'vulnerability_scan':25s} {scanning.get(True,0):6d}")
        asset_crit = Counter(a.asset_criticality for a in self.alerts if a.asset_criticality)
        if asset_crit:
            print(f"    {'asset_criticality':25s} {dict(asset_crit.most_common())}")

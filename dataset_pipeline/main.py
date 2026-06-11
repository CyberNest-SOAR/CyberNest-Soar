"""
dataset_pipeline/main.py — CLI + FastAPI entry point for the SOC dataset pipeline.

Usage:
    # Full pipeline: download, parse, enrich, augment, chains, reasoning, export
    python main.py --events 50000

    # Apply SOC reasoning to existing NDJSON export + LLM datasets
    python main.py --reasoning-only
    python main.py --reasoning-only --reasoning-source data/outputs/my_export.ndjson

    # Re-export existing NDJSON in all formats
    python main.py --export-only

    # Sub-steps
    python main.py --download-only
    python main.py --parse-only

    # API — start FastAPI server
    python main.py --api
    # Then: POST /pipeline/run  {"target_events": 50000}
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List

from pipeline import SOCDatasetPipeline
from parsers.normalizer import UnifiedAlert
from parsers.base import NDJSONParser
from export.exporters import OUTPUTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("main")


def _find_latest_ndjson() -> Path:
    files = sorted(OUTPUTS_DIR.glob("soc_dataset_*.ndjson"))
    # Exclude bulk format
    files = [f for f in files if "_bulk" not in f.name]
    return files[-1] if files else None


def _load_ndjson_alerts(source: Path) -> List[UnifiedAlert]:
    parser = NDJSONParser([source])
    return parser.parse_all()


def run_pipeline(args):
    pipeline = SOCDatasetPipeline(target_events=args.events)
    if args.download_only:
        pipeline.run_download()
        return
    if args.parse_only:
        downloads = pipeline.run_download()
        pipeline.run_parse(downloads)
        return
    if args.export_only:
        logger.info("Export-only mode — re-exporting from existing NDJSON")
        source = _find_latest_ndjson()
        if not source:
            print("No NDJSON export found. Run full pipeline first.")
            return
        logger.info("Loading %s ...", source)
        pipeline = SOCDatasetPipeline(target_events=args.events)
        pipeline.alerts = _load_ndjson_alerts(source)
        logger.info("Loaded %d alerts — starting export", len(pipeline.alerts))
        pipeline.run_export()
        pipeline._summarize()
        return

    if args.reasoning_only:
        logger.info("Reasoning-only mode — applies SOC reasoning to existing NDJSON")
        source = args.reasoning_source or _find_latest_ndjson()
        if not source:
            print("No NDJSON export found. Run full pipeline first.")
            return
        logger.info("Loading %s ...", source)
        pipeline = SOCDatasetPipeline(target_events=args.events)
        pipeline.alerts = _load_ndjson_alerts(source)
        logger.info("Loaded %d alerts — applying SOC reasoning", len(pipeline.alerts))
        pipeline.alerts = pipeline.run_reasoning(pipeline.alerts)
        logger.info("Reasoning complete — %d alerts — exporting", len(pipeline.alerts))
        pipeline.run_export()
        pipeline._summarize()
        return
    stats = pipeline.run_all()
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(stats, indent=2, default=str))
        logger.info("Stats written to %s", output_path)


def start_api():
    from fastapi import FastAPI, HTTPException, Query, Body
    import uvicorn

    app = FastAPI(
        title="CyberNest SOC Dataset Pipeline",
        description="Enterprise-grade SOC dataset generation, enrichment, and ingestion",
        version="1.0.0",
    )

    _pipeline_result = {}

    @app.post("/pipeline/run")
    async def run_pipeline_api(
        target_events: int = Query(50000, description="Target number of events"),
        download_only: bool = Query(False),
        export_only: bool = Query(False),
        reasoning_only: bool = Query(False),
    ):
        nonlocal _pipeline_result
        try:
            pipeline = SOCDatasetPipeline(target_events=target_events)
            if download_only:
                pipeline.run_download()
                return {"status": "download_complete"}
            if export_only:
                source = _find_latest_ndjson()
                if not source:
                    raise HTTPException(404, "No NDJSON export found")
                pipeline.alerts = _load_ndjson_alerts(source)
                pipeline.run_export()
                return {"status": "export_complete", "alert_count": len(pipeline.alerts)}
            if reasoning_only:
                source = _find_latest_ndjson()
                if not source:
                    raise HTTPException(404, "No NDJSON export found")
                pipeline.alerts = _load_ndjson_alerts(source)
                pipeline.alerts = pipeline.run_reasoning(pipeline.alerts)
                pipeline.run_export()
                _pipeline_result = pipeline.stats
                return {"status": "reasoning_complete", "alert_count": len(pipeline.alerts)}
            stats = pipeline.run_all()
            _pipeline_result = stats
            return {"status": "complete", "stats": stats}
        except Exception as e:
            logger.exception("Pipeline failed")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/pipeline/status")
    async def pipeline_status():
        return {
            "status": "complete" if _pipeline_result else "idle",
            "stats": _pipeline_result,
        }

    @app.get("/pipeline/export/{format}")
    async def download_export(format: str = "ndjson"):
        from export.exporters import OUTPUTS_DIR
        import glob
        pattern = str(OUTPUTS_DIR / f"soc_dataset_*.{format}")
        files = sorted(glob.glob(pattern))
        if not files:
            raise HTTPException(status_code=404, detail=f"No {format} exports found")
        return {"files": files, "latest": files[-1]}

    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8003
    logger.info("Starting SOC Dataset Pipeline API on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SOC Dataset Pipeline")
    parser.add_argument("--events", type=int, default=50000, help="Target events")
    parser.add_argument("--download-only", action="store_true", help="Only download datasets")
    parser.add_argument("--parse-only", action="store_true", help="Download and parse")
    parser.add_argument("--export-only", action="store_true", help="Re-export from existing NDJSON in all formats")
    parser.add_argument("--reasoning-only", action="store_true", help="Apply SOC reasoning to existing NDJSON + re-export")
    parser.add_argument("--reasoning-source", type=str, default=None, help="NDJSON source for --reasoning-only (default: latest)")
    parser.add_argument("--api", action="store_true", help="Start FastAPI server")
    parser.add_argument("--port", type=int, default=8003, help="API port")
    parser.add_argument("--output", type=str, help="Output path for pipeline stats JSON")
    args = parser.parse_args()

    if args.api:
        start_api()
    else:
        run_pipeline(args)

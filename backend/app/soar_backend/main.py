import logging
import sys

# ── Configure root logger so all enrichment/service logs are visible ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
    force=True,
)
# Suppress noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from routers import (
    alerts, risk, patch, filtering, playbooks, intel,
    data_outputs, graph, ai_analysis, phishing,
    threat_intel_enhanced, dashboard, monitoring, playbook_config,
    pipeline_alerts, ui_dashboard, reports,
)
from services.collector import collector
from services.enrichment import enrichment_service
from services.patch_engine import PatchEngineModels
from core.config import settings
import httpx
try:
    from app.cache.redis_cache import close_async_client
except Exception:  # pragma: no cover - supports running from backend/app cwd
    from cache.redis_cache import close_async_client

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warn about missing env vars instead of crashing
    mandatory_vars = ['OS_HOST', 'VT_API_KEY', 'MISP_URL', 'MISP_KEY']
    missing = [v for v in mandatory_vars if not getattr(settings, v, None)]
    if missing:
        logger.warning(f"Missing environment variables: {', '.join(missing)} — some services may be unavailable")
    
    # Startup: initialize HTTP clients (errors logged, not fatal)
    try:
        await collector.start()
    except Exception as e:
        logger.warning(f"collector.start() failed: {e}")
    try:
        await enrichment_service.start()
    except Exception as e:
        logger.warning(f"enrichment_service.start() failed: {e}")
        
    # Startup: initialize ML models
    try:
        PatchEngineModels.initialize()
    except Exception as e:
        logger.warning(f"PatchEngineModels.initialize() failed: {e}")
        
    yield
    # Shutdown: clean up HTTP clients
    try:
        await collector.stop()
    except Exception:
        pass
    try:
        await enrichment_service.stop()
    except Exception:
        pass
    try:
        await close_async_client()
    except Exception:
        pass

app = FastAPI(
    title="SOAR Unified API",
    description="Backend API for Wazuh/OpenSearch SOAR System",
    version="1.0.0",
    lifespan=lifespan
)

# Include all team and feature routers
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(patch.router, prefix="/api/v1")
app.include_router(filtering.router, prefix="/api/v1")
app.include_router(playbooks.router, prefix="/api/v1")
app.include_router(intel.router, prefix="/api/v1")

# New feature routers
app.include_router(data_outputs.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")
app.include_router(ai_analysis.router, prefix="/api/v1")
app.include_router(phishing.router, prefix="/api/v1")
app.include_router(threat_intel_enhanced.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")
app.include_router(playbook_config.router, prefix="/api/v1")
app.include_router(pipeline_alerts.router, prefix="/api/v1")
app.include_router(ui_dashboard.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")

@app.post("/predict-noise")
async def predict_noise_endpoint(alert: dict):
    """Testing and validation endpoint for predicting noise on an alert."""
    from routers.filtering import predict_noise
    return predict_noise(alert)

@app.get("/")
async def root():
    return {"status": "SOAR API is online", "version": "v1"}

@app.get("/health")
async def health_check_redirect():
    raise HTTPException(status_code=307, detail="Moved", headers={"Location": "/api/v1/end-point-health/"})

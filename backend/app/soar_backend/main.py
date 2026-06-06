import logging
import sys

# ── Configure root logger so all enrichment/service logs are visible ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
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
<<<<<<< HEAD
from soar_backend.routers import alerts, risk, patch, filtering, playbooks, intel
from soar_backend.services.collector import collector
from soar_backend.services.enrichment import enrichment_service
from soar_backend.services.patch_engine import PatchEngineModels
from soar_backend.core.config import settings
=======
from routers import (
    alerts, risk, patch, filtering, playbooks, intel,
    data_outputs, graph, ai_analysis, phishing,
    threat_intel_enhanced, dashboard, monitoring, playbook_config,
    pipeline_alerts, ui_dashboard, reports,
)
from services.collector import collector
from services.enrichment import enrichment_service
from core.config import settings
>>>>>>> 83a1eb822484b2645de5e14bd1f68707d0d07a8c
import httpx
try:
    from app.cache.redis_cache import close_async_client
except Exception:  # pragma: no cover - supports running from backend/app cwd
    from cache.redis_cache import close_async_client

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
<<<<<<< HEAD
    # Startup validation
    validate_env()
    # Startup: initialize HTTP clients
    await collector.start()
    await enrichment_service.start()
    # Startup: initialize ML models
    PatchEngineModels.initialize()
=======
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
>>>>>>> 83a1eb822484b2645de5e14bd1f68707d0d07a8c
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

# Include all team routers
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

@app.get("/")
async def root():
    return {"status": "SOAR API is online", "version": "v1"}

@app.get("/health")
async def health_check_redirect():
    raise HTTPException(status_code=307, detail="Moved", headers={"Location": "/api/v1/end-point-health/"})

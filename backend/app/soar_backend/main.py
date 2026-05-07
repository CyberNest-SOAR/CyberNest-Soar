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
from routers import alerts, risk, patch, filtering, playbooks, intel
from services.collector import collector
from services.enrichment import enrichment_service
from core.config import settings
import httpx

logger = logging.getLogger(__name__)

def validate_env():
    # Validate mandatory environment variables
    mandatory_vars = ['OS_HOST', 'VT_API_KEY', 'MISP_URL', 'MISP_KEY']
    for var in mandatory_vars:
        val = getattr(settings, var, None)
        # Also fail if using the dummy defaults we had like "misp_api_key_here" if we want to be strict,
        # but just checking for presence/non-empty as per prompt.
        if not val:
            raise RuntimeError(f"Missing mandatory environment variable: {var}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    validate_env()
    # Startup: initialize HTTP clients
    await collector.start()
    await enrichment_service.start()
    yield
    # Shutdown: clean up HTTP clients
    await collector.stop()
    await enrichment_service.stop()

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

@app.get("/")
async def root():
    return {"status": "SOAR API is online", "version": "v1"}

@app.get("/health")
async def health_check():
    # Check OpenSearch (core db)
    os_status = False
    try:
        response = await collector.client.get(f"{settings.OS_HOST}/_cluster/health", auth=collector.os_auth)
        if response.status_code == 200:
            os_status = True
    except Exception:
        pass

    if not os_status:
        raise HTTPException(status_code=503, detail="OpenSearch (core database) is unreachable")

    # Check MISP
    misp_status = False
    try:
        response = await enrichment_service.client.get(
            f"{settings.MISP_URL}/users/view/me", 
            headers={"Authorization": settings.MISP_KEY, "Accept": "application/json"},
            timeout=2.0
        )
        if response.status_code == 200:
            misp_status = True
    except Exception:
        pass

    return {
        "status": "healthy",
        "opensearch": "connected",
        "misp": "connected" if misp_status else "disconnected"
    }

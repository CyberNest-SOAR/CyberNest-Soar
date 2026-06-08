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

from soar_backend.routers import alerts, risk, patch, filtering, playbooks, intel, rag
from soar_backend.services.collector import collector
from soar_backend.services.enrichment import enrichment_service
from soar_backend.core.config import settings
from app.services.vector_manager import get_vector_manager

try:
    from app.cache.redis_cache import close_async_client
except Exception:  # pragma: no cover - supports running from backend/app cwd
    from cache.redis_cache import close_async_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize vector store and embeddings for RAG
    try:
        logger.info("Initializing RAG system (Qdrant + Ollama)...")
        vector_manager = get_vector_manager()
        await vector_manager.bootstrap()
        logger.info("RAG system initialized successfully")
    except Exception as e:
        logger.warning("Failed to initialize RAG system: %s", e)
        # Continue gracefully if RAG fails

    # Startup: initialize HTTP clients
    try:
        await collector.start()
        await enrichment_service.start()
    except Exception as e:
        logger.warning("Failed to start collectors/enrichment: %s", e)

    yield

    # Shutdown: clean up resources
    try:
        await collector.stop()
    except Exception:
        pass
    try:
        await enrichment_service.stop()
    except Exception:
        pass
    try:
        vector_manager = get_vector_manager()
        await vector_manager.close()
    except Exception:
        pass
    try:
        await close_async_client()
    except Exception:
        pass


app = FastAPI(
    title="SOAR Unified API",
    description="Backend API for Wazuh/OpenSearch SOAR System with RAG",
    version="1.0.0",
    lifespan=lifespan,
)

# Include all team routers
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(patch.router, prefix="/api/v1")
app.include_router(filtering.router, prefix="/api/v1")
app.include_router(playbooks.router, prefix="/api/v1")
app.include_router(intel.router, prefix="/api/v1")

# RAG router
app.include_router(rag.router)


@app.get("/")
async def root():
    return {"status": "SOAR API is online", "version": "v1"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SOAR API",
        "version": "v1",
    }


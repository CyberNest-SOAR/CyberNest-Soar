"""Application entrypoint."""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import settings
from app.controllers.classification import router as classification_router
from app.controllers.emails import router as email_router
from app.controllers.alert_intelligence import router as alert_intel_router
from app.services.email_service import EmailService
from app.services.vector_manager import get_vector_manager
from app.services.collector import collector
from app.services.enrichment import enrichment_service
from app.config.logging_config import configure_logging
from app.cache.redis_cache import close_async_client
from app.routers import alerts, risk, patch, filtering, playbooks, intel, rag

# Configure root logger so all enrichment/service logs are visible
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

# Configure logging as early as possible so module imports log consistently.
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    email_service = EmailService(settings)
    app.state.settings = settings
    app.state.email_service = email_service

    try:
        logger = logging.getLogger(__name__)
        logger.info("Initializing RAG system (Qdrant + Ollama)...")
        vector_manager = get_vector_manager()
        await vector_manager.bootstrap()
        logger.info("RAG system initialized successfully")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("Failed to initialize RAG system: %s", e)

    try:
        await collector.start()
        await enrichment_service.start()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("Failed to start collectors/enrichment: %s", e)

    try:
        yield
    finally:
        email_service.close()
        try:
            await collector.stop()
        except Exception:
            pass
        try:
            await enrichment_service.stop()
        except Exception:
            pass
        try:
            await vector_manager.close()
        except Exception:
            pass
        try:
            await close_async_client()
        except Exception:
            pass


app = FastAPI(
    title="CyberNest-Soar Backend API",
    description="Unified backend API for phishing ingestion, SOAR workflows, and RAG semantic search.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(email_router)
app.include_router(classification_router)
app.include_router(alert_intel_router)

app.include_router(alerts.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(patch.router, prefix="/api/v1")
app.include_router(filtering.router, prefix="/api/v1")
app.include_router(playbooks.router, prefix="/api/v1")
app.include_router(intel.router, prefix="/api/v1")
app.include_router(rag.router)


@app.get("/")
async def root():
    return {"status": "CyberNest-Soar backend is online", "version": "v1"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "CyberNest-Soar backend",
        "version": "v1",
    }





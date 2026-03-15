"""Application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Or ["*"] for development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from app.config.settings import settings
from app.controllers.classification import router as classification_router
from app.controllers.emails import router
from app.services.email_service import EmailService
from app.config.logging_config import configure_logging


# Configure logging as early as possible so module imports log consistently.
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    email_service = EmailService(settings)

    app.state.settings = settings
    app.state.email_service = email_service

    try:
        yield
    finally:
        email_service.close()


app = FastAPI(
    title="SOAR Phishing Detection API",
    version="1.0.0",
    description="Essential endpoints for ingesting, analysing, and retrieving email data.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"], # Or ["*"] for development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(classification_router)





"""Application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.config.settings import settings
from backend.app.controllers.classification import router as classification_router
from backend.app.controllers.emails import router
from backend.app.services.email_service import EmailService


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

app.include_router(router)
app.include_router(classification_router)





from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.controllers.classification import router as classification_router
from app.controllers.emails import router as emails_router
from app.services.email_service import EmailService
from app.config.logging_config import configure_logging

configure_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    email_service = EmailService(settings)
    app.state.settings = settings
    app.state.email_service = email_service
    yield
    email_service.close()

app = FastAPI(
    title="SOAR Phishing Detection API",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(emails_router)
app.include_router(classification_router)

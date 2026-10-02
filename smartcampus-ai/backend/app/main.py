"""
SmartCampus AI — FastAPI Application Entry Point

Starts the server, registers routes, creates database tables on startup.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.database import create_tables
from app.api.email_routes import router as email_router
from app.api.complaint_routes import router as complaint_router

# Configure logging — NEVER log credentials
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("smartcampus")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables. Shutdown: cleanup."""
    settings = get_settings()
    logger.info("Starting SmartCampus AI — %s environment", settings.app_env)
    logger.info("Email configured: %s", settings.is_email_configured)
    # NEVER log SMTP credentials
    create_tables()
    logger.info("Database tables ready.")
    yield
    logger.info("SmartCampus AI shutting down.")


settings = get_settings()

app = FastAPI(
    title="SmartCampus AI",
    description="AI-powered campus complaint management platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS — adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(email_router)
app.include_router(complaint_router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SmartCampus AI",
        "version": "1.0.0",
    }


@app.get("/api/email-health")
def email_health():
    """Check email subsystem health without exposing credentials."""
    config = get_settings()
    return {
        "email_enabled": config.email_enabled,
        "smtp_host": config.smtp_host,
        "smtp_port": config.smtp_port,
        "credentials_configured": bool(config.smtp_username and config.smtp_password),
        "from_configured": bool(config.email_from),
        "ready": config.is_email_configured,
    }

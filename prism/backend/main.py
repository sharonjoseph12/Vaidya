"""
PRISM API — FastAPI Application Entry Point
Passive Readings → Intelligent Scalable Medicine
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from backend.utils.logging_config import setup_logging
from backend.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    setup_logging(level="DEBUG" if get_settings().debug else "INFO")
    logger.info("PRISM API starting up — v%s", get_settings().app_version)
    yield
    logger.info("PRISM API shutting down")


app = FastAPI(
    title="PRISM API",
    description="Passive Readings → Intelligent Scalable Medicine. "
                "Multimodal AI diagnostic platform for underserved populations.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS Middleware ---
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Exception Handlers ---
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# --- Routers ---
from backend.routers import patients, diagnostics, abdm, federated  # noqa: E402

app.include_router(patients.router, prefix="/api/v1/patients", tags=["patients"])
app.include_router(diagnostics.router, prefix="/api/v1/diagnostics", tags=["diagnostics"])
app.include_router(abdm.router, prefix="/api/v1/abdm", tags=["abdm"])
app.include_router(federated.router, prefix="/api/v1/federated", tags=["federated"])


# --- Health Check ---
@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint — no auth required."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "service": "prism-api",
    }

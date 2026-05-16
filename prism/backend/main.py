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
from backend.config import get_settings, BACKEND_ENV_FILE
from backend.services.sense_health import sense_pipeline_readiness
from backend.core_ml.model_loader import ml_stack_status
from backend.utils.encryption_key import load_aes_key_bytes_from_b64, raw_encryption_key_from_backend_env

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    settings = get_settings()
    setup_logging(level="DEBUG" if settings.debug else "INFO")
    logger.info("PRISM API starting up — v%s", settings.app_version)
    logger.info("Backend env file: %s (AES reads ENCRYPTION_KEY from here when the file exists)", BACKEND_ENV_FILE)
    try:
        key_len = len(load_aes_key_bytes_from_b64(raw_encryption_key_from_backend_env()))
        logger.info("ENCRYPTION_KEY: %d-byte material for AES (%d-bit)", key_len, key_len * 8)
    except ValueError as exc:
        logger.error("ENCRYPTION_KEY rejected: %s", exc)
        raise
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


@app.get("/health/sense", tags=["system"])
async def health_sense():
    """Layer 1 real SENSE readiness — no auth required.

    When ``use_real_sense`` is true but ``pipeline_constructible`` is false,
    workers typically fall back to legacy mock sensing until deps/Python match
    repo requirements (e.g. MediaPipe ``solutions`` on Python 3.11–3.12).
    """
    s = get_settings()
    body = sense_pipeline_readiness()
    body["use_real_sense_config"] = s.use_real_sense
    body["real_sense_effective"] = bool(
        s.use_real_sense and body.get("pipeline_constructible")
    )
    return body


@app.get("/health/ml", tags=["system"])
async def health_ml():
    """Finetuned ``core_ml`` artifacts (YAMNet .h5, LSTM .pth, causal .pkl) — no auth."""
    return ml_stack_status()

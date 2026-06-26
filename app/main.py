"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging_config import setup_logging, get_logger

settings = get_settings()
setup_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting AI Submission Analyzer", extra={
        "llm_provider": settings.llm_provider,
        "max_zip_mb": settings.max_zip_size_mb,
    })

    # Validate skill catalog exists at startup
    from app.services.skill_matcher import _load_catalog
    try:
        catalog = _load_catalog()
        logger.info(f"Skill catalog loaded", extra={"skills": len(catalog)})
    except Exception as exc:
        logger.error(f"STARTUP WARNING: Skill catalog issue — {exc}")
        # Don't crash on startup; service can still run with empty skills

    yield

    logger.info("AI Submission Analyzer shutting down")


app = FastAPI(
    title="AI Submission Analyzer",
    description=(
        "Analyzes intern/student project ZIP submissions and returns "
        "a mentor-ready evaluation report with skill detection, "
        "viva questions, and outcome evaluation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow the static frontend to call the API
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """Return structured 422 errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "detail": str(exc.errors()),
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "detail": str(exc),
            }
        },
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(router, prefix="/api/v1", tags=["Analysis"])

# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------

_static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health_check():
    """Quick liveness check."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "llm_provider": settings.llm_provider,
    }


@app.get("/", tags=["Health"])
async def root():
    return FileResponse(os.path.join(_static_dir, "index.html")) \
        if os.path.isdir(_static_dir) else \
        {"service": "AI Submission Analyzer", "docs": "/docs", "health": "/health"}

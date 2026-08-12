"""CerberOps — FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from app import __version__
from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.security import get_or_create_api_key, verify_api_key
from app.database import init_db
from app.schemas import SetupResponse

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("cerberops")

# API key header scheme (optional — allows unauthenticated health checks)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    """Dependency that enforces API key authentication."""
    expected = get_or_create_api_key()
    if not expected:
        # First run — no key set yet, allow access
        return ""
    if not api_key or not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide X-API-Key header.",
        )
    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup/shutdown lifecycle."""
    logger.info("CerberOps v%s starting up", __version__)

    # Initialize database tables
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception:
        logger.warning("Database not available — some features will be limited")

    # Generate API key on first run
    key = get_or_create_api_key()
    if key:
        logger.info("API key ready (use X-API-Key header for authenticated endpoints)")

    yield

    logger.info("CerberOps shutting down")


app = FastAPI(
    title="CerberOps",
    description=(
        "DevSecOps Vulnerability Orchestrator — "
        "wraps Nmap, Nuclei, and OWASP ZAP with AI-powered remediation via local Ollama models."
    ),
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount v1 API
app.include_router(api_v1_router)


# ── Setup endpoint (no auth required) ────────────────────────────

@app.post("/api/v1/setup", response_model=SetupResponse, tags=["setup"])
async def first_run_setup() -> SetupResponse:
    """Generate and return an API key (first-run setup)."""
    key = get_or_create_api_key()
    return SetupResponse(api_key=key)


@app.get("/", tags=["root"])
async def root() -> dict:
    return {
        "name": "CerberOps",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/v1/health",
    }

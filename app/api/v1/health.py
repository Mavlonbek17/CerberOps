"""Health check endpoint."""

import shutil

from fastapi import APIRouter

from app import __version__
from app.adapters.zap_adapter import ZapScanner
from app.schemas import HealthCheck
from app.services.ai_remediation import check_ollama_available

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """System health check — reports scanner and service availability."""
    scanners = {
        "nmap": shutil.which("nmap") is not None,
        "nuclei": shutil.which("nuclei") is not None,
        "zap": await ZapScanner().is_available(),
    }

    ollama_ok = await check_ollama_available()

    # Quick DB check
    db_ok = True
    try:
        from sqlalchemy import text

        from app.database import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return HealthCheck(
        status="healthy",
        version=__version__,
        scanners=scanners,
        ollama_available=ollama_ok,
        database=db_ok,
    )

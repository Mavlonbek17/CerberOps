"""Finding-level endpoints — autonomous PoC generation."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import Finding
from app.schemas import ErrorResponse, PocOut
from app.services.poc_generator import generate_poc

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/findings/{finding_id}/poc",
    response_model=PocOut,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def generate_finding_poc(
    finding_id: str,
    regenerate: bool = False,
    session: AsyncSession = Depends(get_session),
) -> PocOut:
    """Generate (or return cached) autonomous verification script for a finding.

    Only available for High/Critical findings. Pass ?regenerate=true to
    force a fresh AI generation instead of returning the cached script.
    """
    stmt = select(Finding).where(Finding.id == finding_id)
    result = await session.execute(stmt)
    finding = result.scalar_one_or_none()

    if not finding:
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found")

    if finding.poc_code and not regenerate:
        return PocOut(
            finding_id=finding.id,
            poc_code=finding.poc_code,
            poc_explanation=finding.poc_explanation or "",
            ai_model_used=finding.poc_model_used or "unknown",
            generated_at=finding.poc_generated_at or datetime.now(UTC),
        )

    if finding.severity.value not in ("critical", "high"):
        raise HTTPException(
            status_code=422,
            detail="PoC generation is only available for High/Critical findings",
        )

    poc = await generate_poc(finding)
    if not poc:
        raise HTTPException(
            status_code=503,
            detail="AI is unavailable or failed to generate a verification script. Try again shortly.",
        )

    finding.poc_code = poc["poc_code"]
    finding.poc_explanation = poc["poc_explanation"]
    finding.poc_model_used = poc["poc_model_used"]
    finding.poc_generated_at = datetime.now(UTC)
    session.add(finding)
    await session.commit()
    await session.refresh(finding)

    return PocOut(
        finding_id=finding.id,
        poc_code=finding.poc_code,
        poc_explanation=finding.poc_explanation,
        ai_model_used=finding.poc_model_used,
        generated_at=finding.poc_generated_at,
    )

"""Scan management endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.exceptions import ScopeValidationError
from app.database import get_session
from app.models import Finding, Report, ScanJob, ScanStatus
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    FindingOut,
    ScanCreated,
    ScanDetail,
    ScanRequest,
    ScanSummary,
)
from app.services.chat_service import chat_about_scan
from app.services.scope_validator import validate_target
from app.tasks.scan_tasks import execute_scan

router = APIRouter()


def _finding_to_out(f: Finding) -> FindingOut:
    """Convert a DB Finding to API response model."""
    return FindingOut(
        id=f.id,
        title=f.title,
        description=f.description,
        severity=f.severity,
        host=f.host,
        port=f.port,
        protocol=f.protocol,
        url=f.url,
        evidence=f.evidence,
        scanner_source=f.scanner_source,
        scanner_sources=(
            [s.strip() for s in f.scanner_sources.split(",") if s.strip()]
            if f.scanner_sources else []
        ),
        cve_ids=(
            [c.strip() for c in f.cve_ids.split(",") if c.strip()]
            if f.cve_ids else []
        ),
        reference_urls=(
            [u.strip() for u in f.reference_urls.split("\n") if u.strip()]
            if f.reference_urls else []
        ),
        remediation=f.remediation,
        is_duplicate=f.is_duplicate,
        created_at=f.created_at,
        ai_verdict=f.ai_verdict,
        ai_triage_notes=f.ai_triage_notes,
        has_poc=bool(f.poc_code),
        cvss_score=f.cvss_score,
        cvss_vector=f.cvss_vector,
    )


def _severity_counts(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.severity.value] = counts.get(f.severity.value, 0) + 1
    return counts


@router.post(
    "/scan",
    response_model=ScanCreated,
    status_code=status.HTTP_202_ACCEPTED,
    responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def create_scan(
    body: ScanRequest,
    session: AsyncSession = Depends(get_session),
) -> ScanCreated:
    """Start a new vulnerability scan.

    Returns 202 Accepted with a job_id for tracking progress.
    """
    # Validate target
    try:
        target = validate_target(body.target, allow_internal=body.allow_internal)
    except ScopeValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Validate scanner names
    valid_scanners = {"nmap", "nuclei", "zap"}
    for s in body.scanners:
        if s not in valid_scanners:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown scanner: {s}. Valid options: {', '.join(sorted(valid_scanners))}",
            )

    # Create scan job
    job = ScanJob(
        target=target,
        scanners=",".join(body.scanners),
        allow_internal=body.allow_internal,
        smart_recon=body.smart_recon,
        tags=",".join(body.tags) if body.tags else None,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)

    # Dispatch Celery task
    execute_scan.delay(job.id)

    return ScanCreated(
        job_id=job.id,
        status=job.status,
        message=f"Scan queued for {target} using {', '.join(body.scanners)}",
    )


@router.get("/scan", response_model=list[ScanSummary])
async def list_scans(
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
    offset: int = 0,
) -> list[ScanSummary]:
    """List recent scans."""
    stmt = (
        select(ScanJob)
        .order_by(ScanJob.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    jobs = result.scalars().all()

    summaries = []
    for job in jobs:
        # Count findings
        count_stmt = select(Finding).where(Finding.scan_job_id == job.id)
        count_result = await session.execute(count_stmt)
        findings_count = len(count_result.scalars().all())

        summaries.append(ScanSummary(
            id=job.id,
            target=job.target,
            status=job.status,
            scanners=[s.strip() for s in job.scanners.split(",")],
            findings_count=findings_count,
            created_at=job.created_at,
            tags=[t.strip() for t in job.tags.split(",") if t.strip()] if job.tags else [],
        ))

    return summaries


@router.get(
    "/scan/{job_id}",
    response_model=ScanDetail,
    responses={404: {"model": ErrorResponse}},
)
async def get_scan(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> ScanDetail:
    """Get scan details and findings."""
    stmt = select(ScanJob).where(ScanJob.id == job_id)
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail=f"Scan job {job_id} not found")

    # Fetch findings
    findings_stmt = select(Finding).where(Finding.scan_job_id == job_id)
    findings_result = await session.execute(findings_stmt)
    findings = list(findings_result.scalars().all())

    return ScanDetail(
        id=job.id,
        target=job.target,
        status=job.status,
        scanners=[s.strip() for s in job.scanners.split(",")],
        progress=job.progress,
        error_message=job.error_message,
        findings_count=len(findings),
        severity_counts=_severity_counts(findings),
        findings=[_finding_to_out(f) for f in findings],
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        smart_recon=job.smart_recon,
        recon_summary=job.recon_summary,
        ai_scan_plan=job.ai_scan_plan,
        tags=[t.strip() for t in job.tags.split(",") if t.strip()] if job.tags else [],
    )


@router.post(
    "/scan/{job_id}/chat",
    response_model=ChatResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def chat_with_scan(
    job_id: str,
    body: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """Ask the local AI a natural-language question about this scan's results.

    Conversation history is kept client-side — pass prior turns in the
    `history` field on each request.
    """
    stmt = select(ScanJob).where(ScanJob.id == job_id)
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail=f"Scan job {job_id} not found")

    if job.status != ScanStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Scan is {job.status.value}. Chat is available only after completion.",
        )

    findings_stmt = select(Finding).where(Finding.scan_job_id == job_id)
    findings_result = await session.execute(findings_stmt)
    findings = list(findings_result.scalars().all())

    report_stmt = select(Report).where(Report.scan_job_id == job_id)
    report_result = await session.execute(report_stmt)
    report = report_result.scalar_one_or_none()

    result_data = await chat_about_scan(
        job=job,
        findings=findings,
        report=report,
        message=body.message,
        history=[h.model_dump() for h in body.history],
    )

    return ChatResponse(response=result_data["response"], ai_model_used=result_data["ai_model_used"])


@router.delete(
    "/scan/{job_id}",
    responses={404: {"model": ErrorResponse}},
)
async def cancel_scan(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Cancel a queued or running scan."""
    stmt = select(ScanJob).where(ScanJob.id == job_id)
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail=f"Scan job {job_id} not found")

    if job.status in (ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED):
        return {"message": f"Scan {job_id} is already {job.status.value}"}

    job.status = ScanStatus.CANCELLED
    job.updated_at = datetime.now(UTC)
    session.add(job)
    await session.commit()

    return {"message": f"Scan {job_id} cancelled"}

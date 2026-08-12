"""Report endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import Finding, Report, ScanJob, ScanStatus
from app.schemas import ErrorResponse, ReportOut
from app.services.ai_remediation import generate_report

router = APIRouter()


@router.get(
    "/report/{job_id}",
    response_model=ReportOut,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def get_report(
    job_id: str,
    regenerate: bool = False,
    session: AsyncSession = Depends(get_session),
) -> ReportOut:
    """Get the AI-generated remediation report for a completed scan.

    Pass ?regenerate=true to force a new AI analysis.
    """
    # Verify scan exists
    stmt = select(ScanJob).where(ScanJob.id == job_id)
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail=f"Scan job {job_id} not found")

    if job.status != ScanStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Scan is {job.status.value}. Report is available only after completion.",
        )

    # Check for existing report
    report_stmt = select(Report).where(Report.scan_job_id == job_id)
    report_result = await session.execute(report_stmt)
    report = report_result.scalar_one_or_none()

    if report and not regenerate:
        return ReportOut(
            id=report.id,
            scan_job_id=report.scan_job_id,
            executive_summary=report.executive_summary,
            technical_details=report.technical_details,
            remediation_plan=report.remediation_plan,
            ai_model_used=report.ai_model_used,
            generated_at=report.generated_at,
        )

    # Generate new report
    findings_stmt = select(Finding).where(Finding.scan_job_id == job_id)
    findings_result = await session.execute(findings_stmt)
    findings = list(findings_result.scalars().all())

    report_data = await generate_report(job.target, findings)

    if report:
        # Update existing
        report.executive_summary = report_data["executive_summary"]
        report.technical_details = report_data["technical_details"]
        report.remediation_plan = report_data["remediation_plan"]
        report.ai_model_used = report_data["ai_model_used"]
    else:
        report = Report(
            scan_job_id=job_id,
            executive_summary=report_data["executive_summary"],
            technical_details=report_data["technical_details"],
            remediation_plan=report_data["remediation_plan"],
            ai_model_used=report_data["ai_model_used"],
        )

    session.add(report)
    await session.commit()
    await session.refresh(report)

    return ReportOut(
        id=report.id,
        scan_job_id=report.scan_job_id,
        executive_summary=report.executive_summary,
        technical_details=report.technical_details,
        remediation_plan=report.remediation_plan,
        ai_model_used=report.ai_model_used,
        generated_at=report.generated_at,
    )

"""Baseline diffing — compares the current scan's findings against the most recent
previous completed scan of the same target, so the AI and UI can highlight what's new."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Finding, ScanJob, ScanStatus


async def get_previous_scan(job: ScanJob, session: AsyncSession) -> ScanJob | None:
    stmt = (
        select(ScanJob)
        .where(
            ScanJob.target == job.target,
            ScanJob.status == ScanStatus.COMPLETED,
            ScanJob.id != job.id,
        )
        .order_by(ScanJob.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def mark_new_findings(job: ScanJob, findings: list[Finding], session: AsyncSession) -> dict:
    """Set finding.is_new for each finding based on fingerprint comparison with the
    previous scan. Returns a summary dict {previous_scan_id, new_count, resolved: [...]}"""
    prev = await get_previous_scan(job, session)
    if not prev:
        for f in findings:
            f.is_new = True
            session.add(f)
        await session.commit()
        return {"previous_scan_id": None, "new_count": len(findings), "resolved": []}

    prev_stmt = select(Finding).where(Finding.scan_job_id == prev.id)
    prev_result = await session.execute(prev_stmt)
    prev_findings = list(prev_result.scalars().all())
    prev_fingerprints = {f.fingerprint for f in prev_findings}
    current_fingerprints = {f.fingerprint for f in findings}

    new_count = 0
    for f in findings:
        f.is_new = f.fingerprint not in prev_fingerprints
        if f.is_new:
            new_count += 1
        session.add(f)
    await session.commit()

    resolved = [
        {"title": f.title, "severity": f.severity.value, "host": f.host}
        for f in prev_findings
        if f.fingerprint not in current_fingerprints
    ]

    return {"previous_scan_id": prev.id, "new_count": new_count, "resolved": resolved}

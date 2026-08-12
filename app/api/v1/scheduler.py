"""Scheduled scan CRUD endpoints."""

import json
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import ScheduledScan
from app.schemas import ErrorResponse, ScheduledScanCreate, ScheduledScanOut

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


# ── Helpers ───────────────────────────────────────────────────────

def _next_run(schedule: str) -> datetime:
    """Compute the next execution timestamp from a schedule string."""
    now = datetime.now(UTC)
    if schedule == "weekly":
        return now + timedelta(weeks=1)
    if schedule == "monthly":
        return now + timedelta(days=30)
    return now + timedelta(days=1)  # daily default


def _sched_to_out(s: ScheduledScan) -> ScheduledScanOut:
    return ScheduledScanOut(
        id=s.id,
        target=s.target,
        scanners=[sc.strip() for sc in s.scanners.split(",") if sc.strip()],
        tags=[t.strip() for t in s.tags.split(",") if t.strip()] if s.tags else [],
        schedule=s.schedule,
        enabled=s.enabled,
        allow_internal=s.allow_internal,
        smart_recon=s.smart_recon,
        last_run_at=s.last_run_at,
        next_run_at=s.next_run_at,
        created_at=s.created_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("", response_model=list[ScheduledScanOut])
async def list_scheduled_scans(
    session: AsyncSession = Depends(get_session),
) -> list[ScheduledScanOut]:
    """List all scheduled scans."""
    result = await session.execute(select(ScheduledScan).order_by(ScheduledScan.created_at.desc()))
    return [_sched_to_out(s) for s in result.scalars().all()]


@router.post("", response_model=ScheduledScanOut, status_code=201)
async def create_scheduled_scan(
    body: ScheduledScanCreate,
    session: AsyncSession = Depends(get_session),
) -> ScheduledScanOut:
    """Create a new scheduled scan."""
    sched = ScheduledScan(
        target=body.target,
        scanners=",".join(body.scanners),
        tags=",".join(body.tags) if body.tags else None,
        schedule=body.schedule,
        enabled=body.enabled,
        allow_internal=body.allow_internal,
        smart_recon=body.smart_recon,
        next_run_at=_next_run(body.schedule),
    )
    session.add(sched)
    await session.commit()
    await session.refresh(sched)
    return _sched_to_out(sched)


@router.get("/{sched_id}", response_model=ScheduledScanOut, responses={404: {"model": ErrorResponse}})
async def get_scheduled_scan(
    sched_id: str,
    session: AsyncSession = Depends(get_session),
) -> ScheduledScanOut:
    """Get a single scheduled scan by ID."""
    result = await session.execute(select(ScheduledScan).where(ScheduledScan.id == sched_id))
    sched = result.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail=f"Scheduled scan {sched_id} not found")
    return _sched_to_out(sched)


@router.patch("/{sched_id}", response_model=ScheduledScanOut, responses={404: {"model": ErrorResponse}})
async def update_scheduled_scan(
    sched_id: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
) -> ScheduledScanOut:
    """Partially update a scheduled scan (enable/disable, change schedule, etc.)."""
    result = await session.execute(select(ScheduledScan).where(ScheduledScan.id == sched_id))
    sched = result.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail=f"Scheduled scan {sched_id} not found")

    allowed_fields = {"enabled", "schedule", "scanners", "tags", "allow_internal", "smart_recon", "target"}
    for key, value in body.items():
        if key not in allowed_fields:
            continue
        if key == "scanners" and isinstance(value, list):
            value = ",".join(value)
        if key == "tags" and isinstance(value, list):
            value = ",".join(value) if value else None
        setattr(sched, key, value)

    # Recompute next_run_at if schedule changed
    if "schedule" in body:
        sched.next_run_at = _next_run(sched.schedule)

    session.add(sched)
    await session.commit()
    await session.refresh(sched)
    return _sched_to_out(sched)


@router.delete("/{sched_id}", responses={404: {"model": ErrorResponse}})
async def delete_scheduled_scan(
    sched_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Delete a scheduled scan."""
    result = await session.execute(select(ScheduledScan).where(ScheduledScan.id == sched_id))
    sched = result.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail=f"Scheduled scan {sched_id} not found")
    await session.delete(sched)
    await session.commit()
    return {"message": f"Scheduled scan {sched_id} deleted"}

"""Celery task to execute due scheduled scans."""

import logging
from datetime import UTC, datetime, timedelta

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.scheduled_scan_tasks.run_due_scheduled_scans")
def run_due_scheduled_scans() -> None:
    """Find all ScheduledScans whose next_run_at is due and dispatch them."""
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()


async def _run() -> None:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from sqlmodel import select

    from app.config import settings
    from app.models import ScheduledScan, ScanJob
    from app.tasks.scan_tasks import execute_scan

    engine = create_async_engine(settings.database_url)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    now = datetime.now(UTC)

    async with async_session_factory() as session:
        stmt = select(ScheduledScan).where(
            ScheduledScan.enabled == True,  # noqa: E712
            ScheduledScan.next_run_at <= now,
        )
        result = await session.execute(stmt)
        due = result.scalars().all()

        for sched in due:
            job = ScanJob(
                target=sched.target,
                scanners=sched.scanners,
                allow_internal=sched.allow_internal,
                smart_recon=sched.smart_recon,
                tags=sched.tags,
            )
            session.add(job)
            await session.commit()
            await session.refresh(job)
            execute_scan.delay(job.id)

            # Update last/next run timestamps
            sched.last_run_at = now
            if sched.schedule == "weekly":
                sched.next_run_at = now + timedelta(weeks=1)
            elif sched.schedule == "monthly":
                sched.next_run_at = now + timedelta(days=30)
            else:
                sched.next_run_at = now + timedelta(days=1)
            session.add(sched)

        await session.commit()

    await engine.dispose()

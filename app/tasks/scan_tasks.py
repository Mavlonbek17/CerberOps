"""Celery task definitions for scan execution."""

import asyncio
import logging
from datetime import UTC

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="app.tasks.scan_tasks.execute_scan",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def execute_scan(self, job_id: str) -> dict:
    """Execute a full scan pipeline.

    This is a Celery task that wraps the async scan service.
    """
    logger.info("Starting scan task for job %s", job_id)

    async def _run():
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from app.config import settings
        from app.models import ScanJob, ScanStatus
        from app.services.scan_service import run_scan

        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            try:
                await run_scan(job_id, session)
                return {"job_id": job_id, "status": "completed"}
            except Exception as exc:
                logger.exception("Scan task failed for job %s", job_id)
                # Mark job as failed
                from datetime import datetime

                from sqlmodel import select

                stmt = select(ScanJob).where(ScanJob.id == job_id)
                result = await session.execute(stmt)
                job = result.scalar_one_or_none()
                if job:
                    job.status = ScanStatus.FAILED
                    job.error_message = str(exc)[:4000]
                    job.updated_at = datetime.now(UTC)
                    session.add(job)
                    await session.commit()
                raise

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error("Scan task error for job %s: %s", job_id, exc)
        raise self.retry(exc=exc) from exc

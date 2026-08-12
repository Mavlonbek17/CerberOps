"""Scan orchestration service — coordinates scanners and processes results."""

import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.adapters import NmapScanner, NucleiScanner, ZapScanner
from app.adapters.base import BaseScanner, RawFinding
from app.core.exceptions import CerberOpsError
from app.models import AiVerdict, Finding, Report, ScanJob, ScanStatus
from app.services.ai_remediation import generate_report
from app.services.ai_triage import triage_findings
from app.services.dedup_service import deduplicate
from app.services.smart_recon import plan_scan

logger = logging.getLogger(__name__)

_SCANNERS: dict[str, type[BaseScanner]] = {
    "nmap": NmapScanner,
    "nuclei": NucleiScanner,
    "zap": ZapScanner,
}


async def run_scan(job_id: str, session: AsyncSession) -> None:
    """Execute a full scan pipeline for the given job.

    Called from a Celery task.  Updates the job status and persists findings
    as it progresses.
    """
    stmt = select(ScanJob).where(ScanJob.id == job_id)
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        logger.error("Scan job %s not found", job_id)
        return

    if job.status == ScanStatus.CANCELLED:
        logger.info("Scan job %s was cancelled, skipping", job_id)
        return

    job.status = ScanStatus.RUNNING
    job.updated_at = datetime.now(UTC)
    session.add(job)
    await session.commit()

    requested_scanners = [s.strip() for s in job.scanners.split(",") if s.strip()]
    all_raw_findings: list[RawFinding] = []
    total_scanners = len(requested_scanners)
    skipped_scanners: list[str] = []

    # ── AI Smart Recon ────────────────────────────────────────────
    # Fingerprint the target and let local AI narrow the Nuclei template
    # set before running the full scan. Fails open: on any error the scan
    # just runs unfiltered, exactly as before this feature existed.
    nuclei_tags: list[str] = []
    if job.smart_recon:
        try:
            plan = await plan_scan(job.target)
            nuclei_tags = plan.get("nuclei_tags", [])
            job.recon_summary = plan.get("recon_summary")
            job.ai_scan_plan = plan.get("ai_scan_plan")
            session.add(job)
            await session.commit()
            logger.info("Smart Recon plan for %s: tags=%s", job.target, nuclei_tags)
        except Exception:
            logger.exception("Smart Recon failed for %s — continuing unfiltered", job.target)

    for idx, scanner_name in enumerate(requested_scanners):
        scanner_cls = _SCANNERS.get(scanner_name)
        if not scanner_cls:
            logger.warning("Unknown scanner: %s, skipping", scanner_name)
            continue

        scanner = scanner_cls()

        try:
            if not await scanner.is_available():
                logger.warning("Scanner %s not available, skipping", scanner_name)
                skipped_scanners.append(scanner_name)
                continue

            logger.info("Running %s against %s", scanner_name, job.target)
            scan_kwargs: dict = {"allow_internal": job.allow_internal}
            if scanner_name == "nuclei" and nuclei_tags:
                scan_kwargs["tags"] = nuclei_tags

            raw = await scanner.run(job.target, **scan_kwargs)
            all_raw_findings.extend(raw)
            logger.info("%s returned %d findings", scanner_name, len(raw))

        except CerberOpsError as exc:
            logger.error("Scanner %s failed: %s", scanner_name, exc)
            skipped_scanners.append(scanner_name)
        except Exception:
            logger.exception("Unexpected error in scanner %s", scanner_name)
            skipped_scanners.append(scanner_name)

        # Update progress
        job.progress = int(((idx + 1) / total_scanners) * 80)
        job.updated_at = datetime.now(UTC)
        session.add(job)
        await session.commit()

    # Dedup + persist
    job.status = ScanStatus.PARSING
    session.add(job)
    await session.commit()

    deduped = deduplicate(all_raw_findings)

    # ── AI False Positive Filter ─────────────────────────────────
    # Review low/medium severity findings against their raw evidence and
    # tag obvious noise as "likely_false_positive". Nothing is dropped —
    # the UI hides these by default but lets users reveal them.
    raw_list = [raw for _, raw in deduped]
    try:
        triage_results = await triage_findings(raw_list)
    except Exception:
        logger.exception("AI triage failed — leaving all findings unreviewed")
        triage_results = [(raw, AiVerdict.UNREVIEWED, None) for raw in raw_list]

    findings: list[Finding] = []

    for (fingerprint, raw), (_, verdict, notes) in zip(deduped, triage_results, strict=True):
        finding = Finding(
            scan_job_id=job.id,
            fingerprint=fingerprint,
            title=raw.title,
            description=raw.description,
            severity=raw.severity,
            host=raw.host,
            port=raw.port,
            protocol=raw.protocol,
            url=raw.url,
            evidence=raw.evidence,
            scanner_source=raw.scanner_source,
            scanner_sources=raw.scanner_source,
            cve_ids=",".join(raw.cve_ids) if raw.cve_ids else None,
            reference_urls="\n".join(raw.reference_urls) if raw.reference_urls else None,
            remediation=raw.remediation,
            is_duplicate=False,
            ai_verdict=verdict,
            ai_triage_notes=notes,
        )
        session.add(finding)
        findings.append(finding)

    await session.commit()

    job.progress = 90
    job.updated_at = datetime.now(UTC)
    session.add(job)
    await session.commit()

    # AI Analysis
    job.status = ScanStatus.ANALYZING
    session.add(job)
    await session.commit()

    try:
        report_data = await generate_report(job.target, findings)
        report = Report(
            scan_job_id=job.id,
            executive_summary=report_data["executive_summary"],
            technical_details=report_data["technical_details"],
            remediation_plan=report_data["remediation_plan"],
            ai_model_used=report_data["ai_model_used"],
        )
        session.add(report)
        await session.commit()
    except Exception:
        logger.exception("AI report generation failed for job %s", job_id)
        await session.rollback()

    # Record any scanners that were unavailable / errored
    if skipped_scanners:
        skip_msg = "Scanner(s) unavailable and skipped: " + ", ".join(skipped_scanners)
        job.error_message = skip_msg
        logger.warning("Job %s — %s", job_id, skip_msg)

    # Done
    job.status = ScanStatus.COMPLETED
    job.progress = 100
    job.completed_at = datetime.now(UTC)
    job.updated_at = datetime.now(UTC)
    session.add(job)
    await session.commit()

    logger.info("Scan job %s completed with %d findings", job_id, len(findings))

"""Baseline diffing, MITRE ATT&CK mapping, compliance dashboards, CVE enrichment,
and safe exploit verification endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import Finding, ScanJob
from app.schemas import (
    BaselineOut,
    ComplianceOut,
    CveEnrichmentOut,
    ErrorResponse,
    FindingOut,
    MitreOut,
    MitreTechnique,
    VerifyResult,
)
from app.services.baseline_service import get_previous_scan
from app.services.compliance_service import compute_compliance_summary
from app.services.cve_enrichment_service import enrich_cve
from app.services.mitre_mapping import map_finding_to_mitre
from app.services.verification_service import verify_finding

router = APIRouter(tags=["intelligence"])


async def _get_job_and_findings(job_id: str, session: AsyncSession) -> tuple[ScanJob, list[Finding]]:
    job_result = await session.execute(select(ScanJob).where(ScanJob.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail=f"Scan job {job_id} not found")
    findings_result = await session.execute(select(Finding).where(Finding.scan_job_id == job_id))
    findings = list(findings_result.scalars().all())
    return job, findings


def _finding_out(f: Finding) -> FindingOut:
    return FindingOut(
        id=f.id, title=f.title, description=f.description, severity=f.severity, host=f.host,
        port=f.port, protocol=f.protocol, url=f.url, evidence=f.evidence,
        scanner_source=f.scanner_source,
        scanner_sources=[s.strip() for s in f.scanner_sources.split(",") if s.strip()] if f.scanner_sources else [],
        cve_ids=[c.strip() for c in f.cve_ids.split(",") if c.strip()] if f.cve_ids else [],
        reference_urls=[u.strip() for u in f.reference_urls.split("\n") if u.strip()] if f.reference_urls else [],
        remediation=f.remediation, is_duplicate=f.is_duplicate, created_at=f.created_at,
        ai_verdict=f.ai_verdict, ai_triage_notes=f.ai_triage_notes, has_poc=bool(f.poc_code),
        cvss_score=f.cvss_score, cvss_vector=f.cvss_vector,
        mitre_techniques=[t.strip() for t in f.mitre_techniques.split(",") if t.strip()] if f.mitre_techniques else [],
        owasp_category=f.owasp_category, is_new=f.is_new,
    )


@router.get("/scan/{job_id}/baseline", response_model=BaselineOut, responses={404: {"model": ErrorResponse}})
async def get_baseline(job_id: str, session: AsyncSession = Depends(get_session)) -> BaselineOut:
    job, findings = await _get_job_and_findings(job_id, session)
    prev = await get_previous_scan(job, session)
    if not prev:
        return BaselineOut(has_baseline=False, new_findings=[_finding_out(f) for f in findings], unchanged_count=0)

    prev_result = await session.execute(select(Finding).where(Finding.scan_job_id == prev.id))
    prev_findings = list(prev_result.scalars().all())
    prev_fps = {f.fingerprint for f in prev_findings}
    current_fps = {f.fingerprint for f in findings}

    new_findings = [f for f in findings if f.fingerprint not in prev_fps]
    resolved = [
        {"title": f.title, "severity": f.severity.value, "host": f.host}
        for f in prev_findings if f.fingerprint not in current_fps
    ]
    unchanged = len(findings) - len(new_findings)

    return BaselineOut(
        has_baseline=True, previous_scan_id=prev.id,
        new_findings=[_finding_out(f) for f in new_findings],
        resolved_findings=resolved, unchanged_count=unchanged,
    )


@router.get("/scan/{job_id}/mitre", response_model=MitreOut, responses={404: {"model": ErrorResponse}})
async def get_mitre(job_id: str, session: AsyncSession = Depends(get_session)) -> MitreOut:
    _, findings = await _get_job_and_findings(job_id, session)
    techniques: dict[str, MitreTechnique] = {}
    for f in findings:
        for tid, tname, tactic in map_finding_to_mitre(f.title, f.description):
            if tid not in techniques:
                techniques[tid] = MitreTechnique(technique_id=tid, technique_name=tname, tactic=tactic, finding_ids=[], finding_count=0)
            techniques[tid].finding_ids.append(f.id)
            techniques[tid].finding_count += 1
    return MitreOut(techniques=list(techniques.values()))


@router.get("/scan/{job_id}/compliance", response_model=ComplianceOut, responses={404: {"model": ErrorResponse}})
async def get_compliance(job_id: str, session: AsyncSession = Depends(get_session)) -> ComplianceOut:
    _, findings = await _get_job_and_findings(job_id, session)
    summary = compute_compliance_summary(findings)
    return ComplianceOut(**summary)


@router.get("/cve/{cve_id}", response_model=CveEnrichmentOut, responses={404: {"model": ErrorResponse}})
async def get_cve(cve_id: str, session: AsyncSession = Depends(get_session)) -> CveEnrichmentOut:
    enrichment = await enrich_cve(cve_id.upper(), session)
    if not enrichment:
        raise HTTPException(status_code=404, detail=f"No enrichment data available for {cve_id}")
    return CveEnrichmentOut(
        cve_id=enrichment.cve_id, description=enrichment.description,
        cvss_score=enrichment.cvss_score, cvss_vector=enrichment.cvss_vector,
        epss_score=enrichment.epss_score, published_date=enrichment.published_date,
        reference_urls=enrichment.reference_urls.split("\n") if enrichment.reference_urls else [],
    )


@router.post("/findings/{finding_id}/verify", response_model=VerifyResult, responses={404: {"model": ErrorResponse}})
async def verify(finding_id: str, session: AsyncSession = Depends(get_session)) -> VerifyResult:
    result = await session.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found")

    verification = await verify_finding(finding.title, finding.description, finding.url, finding.evidence)
    return VerifyResult(
        finding_id=finding_id, verified=verification["verified"],
        method=verification["method"], details=verification["details"],
        verified_at=datetime.now(UTC),
    )

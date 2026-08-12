"""Report export endpoints — JSON and print-ready HTML."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import Finding, Report, ScanJob
from app.schemas import ErrorResponse

router = APIRouter(tags=["export"])

_SEVERITY_COLORS: dict[str, str] = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#d97706",
    "low": "#65a30d",
    "info": "#6b7280",
}


# ── Helpers ───────────────────────────────────────────────────────

async def _fetch_scan_data(job_id: str, session: AsyncSession) -> tuple[ScanJob, list[Finding], Report | None]:
    """Fetch scan job, findings, and optional report from DB."""
    job_result = await session.execute(select(ScanJob).where(ScanJob.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail=f"Scan job {job_id} not found")

    findings_result = await session.execute(
        select(Finding).where(Finding.scan_job_id == job_id).order_by(Finding.severity)
    )
    findings = list(findings_result.scalars().all())

    report_result = await session.execute(select(Report).where(Report.scan_job_id == job_id))
    report = report_result.scalar_one_or_none()

    return job, findings, report


def _build_json_payload(job: ScanJob, findings: list[Finding], report: Report | None) -> dict:
    """Build the dict structure for JSON export."""
    return {
        "scan_id": job.id,
        "target": job.target,
        "status": job.status.value,
        "scanners": [s.strip() for s in job.scanners.split(",") if s.strip()],
        "tags": [t.strip() for t in job.tags.split(",") if t.strip()] if job.tags else [],
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "findings_count": len(findings),
        "report": {
            "executive_summary": report.executive_summary,
            "technical_details": report.technical_details,
            "remediation_plan": report.remediation_plan,
            "ai_model_used": report.ai_model_used,
            "generated_at": report.generated_at.isoformat(),
        } if report else None,
        "findings": [
            {
                "id": f.id,
                "title": f.title,
                "severity": f.severity.value,
                "host": f.host,
                "port": f.port,
                "protocol": f.protocol,
                "url": f.url,
                "cvss_score": f.cvss_score,
                "cvss_vector": f.cvss_vector,
                "cve_ids": [c.strip() for c in f.cve_ids.split(",") if c.strip()] if f.cve_ids else [],
                "description": f.description,
                "evidence": f.evidence,
                "remediation": f.remediation,
                "ai_verdict": f.ai_verdict.value,
                "scanner_source": f.scanner_source,
                "created_at": f.created_at.isoformat(),
            }
            for f in findings
        ],
    }


def _build_html_report(job: ScanJob, findings: list[Finding], report: Report | None) -> str:
    """Render a print-ready HTML report."""
    scanners_str = ", ".join(s.strip() for s in job.scanners.split(",") if s.strip())
    tags_str = ", ".join(t.strip() for t in job.tags.split(",") if t.strip()) if job.tags else "—"
    generated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    completed = job.completed_at.strftime("%Y-%m-%d %H:%M UTC") if job.completed_at else "N/A"

    # Severity counts
    sev_counts: dict[str, int] = {}
    for f in findings:
        sev_counts[f.severity.value] = sev_counts.get(f.severity.value, 0) + 1

    summary_rows = "".join(
        f'<tr><td style="text-transform:capitalize;font-weight:600;color:{_SEVERITY_COLORS.get(sev,"#000")}">'
        f'{sev}</td><td>{cnt}</td></tr>'
        for sev, cnt in sorted(sev_counts.items(), key=lambda x: list(_SEVERITY_COLORS).index(x[0]) if x[0] in _SEVERITY_COLORS else 99)
    )

    finding_rows = ""
    for f in findings:
        color = _SEVERITY_COLORS.get(f.severity.value, "#6b7280")
        cvss_cell = f"{f.cvss_score:.1f}" if f.cvss_score is not None else "—"
        cves = ", ".join(c.strip() for c in f.cve_ids.split(",") if c.strip()) if f.cve_ids else "—"
        finding_rows += (
            f"<tr>"
            f'<td style="color:{color};font-weight:700;text-transform:capitalize">{f.severity.value}</td>'
            f"<td>{cvss_cell}</td>"
            f"<td>{f.title}</td>"
            f"<td>{f.host}</td>"
            f"<td>{f.port if f.port else '—'}</td>"
            f"<td>{cves}</td>"
            f"</tr>"
        )

    exec_summary = (report.executive_summary.replace("\n", "<br>") if report else "Report not generated.")
    remediation = (report.remediation_plan.replace("\n", "<br>") if report else "—")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CerberOps Security Report — {job.target}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; padding: 2rem; color: #1e293b; background: #f8fafc; }}
  header {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #f8fafc; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
  header h1 {{ margin: 0 0 .25rem; font-size: 1.75rem; }}
  header p {{ margin: 0; opacity: .75; font-size: .9rem; }}
  .meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .meta-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; }}
  .meta-card dt {{ font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; color: #64748b; margin-bottom: .25rem; }}
  .meta-card dd {{ margin: 0; font-weight: 600; color: #1e293b; }}
  section {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; }}
  section h2 {{ margin: 0 0 1rem; font-size: 1.1rem; border-bottom: 1px solid #e2e8f0; padding-bottom: .5rem; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .875rem; }}
  th {{ background: #f1f5f9; text-align: left; padding: .5rem .75rem; font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; color: #64748b; }}
  td {{ padding: .5rem .75rem; border-bottom: 1px solid #f1f5f9; vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  .prose {{ line-height: 1.7; color: #374151; }}
  @media print {{
    body {{ background: #fff; padding: 1cm; }}
    section {{ break-inside: avoid; }}
    header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}
</style>
</head>
<body>
<header>
  <h1>🔐 CerberOps Security Report</h1>
  <p>Generated {generated}</p>
</header>

<div class="meta-grid">
  <div class="meta-card"><dl><dt>Target</dt><dd>{job.target}</dd></dl></div>
  <div class="meta-card"><dl><dt>Scan ID</dt><dd style="font-family:monospace;font-size:.8rem">{job.id}</dd></dl></div>
  <div class="meta-card"><dl><dt>Status</dt><dd style="text-transform:capitalize">{job.status.value}</dd></dl></div>
  <div class="meta-card"><dl><dt>Completed</dt><dd>{completed}</dd></dl></div>
  <div class="meta-card"><dl><dt>Scanners</dt><dd>{scanners_str}</dd></dl></div>
  <div class="meta-card"><dl><dt>Tags</dt><dd>{tags_str}</dd></dl></div>
  <div class="meta-card"><dl><dt>Total Findings</dt><dd>{len(findings)}</dd></dl></div>
</div>

<section>
  <h2>Severity Summary</h2>
  <table>
    <thead><tr><th>Severity</th><th>Count</th></tr></thead>
    <tbody>{summary_rows}</tbody>
  </table>
</section>

<section>
  <h2>Executive Summary</h2>
  <div class="prose">{exec_summary}</div>
</section>

<section>
  <h2>Findings</h2>
  <table>
    <thead>
      <tr><th>Severity</th><th>CVSS</th><th>Title</th><th>Host</th><th>Port</th><th>CVEs</th></tr>
    </thead>
    <tbody>{finding_rows}</tbody>
  </table>
</section>

<section>
  <h2>Remediation Plan</h2>
  <div class="prose">{remediation}</div>
</section>

</body>
</html>"""


# ── Endpoints ─────────────────────────────────────────────────────

@router.get(
    "/report/{job_id}/export",
    response_model=None,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def export_report(
    job_id: str,
    format: str = Query(default="json", description="Export format: json or html"),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse | HTMLResponse:
    """Export a scan report as JSON (download) or print-ready HTML."""
    job, findings, report = await _fetch_scan_data(job_id, session)

    if format == "json":
        payload = _build_json_payload(job, findings, report)
        filename = f"cerberops-report-{job_id}.json"
        return JSONResponse(
            content=payload,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    if format == "html":
        html = _build_html_report(job, findings, report)
        return HTMLResponse(content=html)

    raise HTTPException(status_code=400, detail="Unsupported format. Use 'json' or 'html'.")

"""AI remediation report generation via local Ollama."""

import json
import logging

import httpx

from app.config import settings
from app.models import Finding

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are CerberOps AI — a senior security analyst. You receive vulnerability scan \
findings and produce a structured remediation report. Be concise, actionable, and \
prioritize by severity. Use plain language a developer can follow."""

_REPORT_PROMPT_TEMPLATE = """\
Analyze these vulnerability findings from a security scan of {target} and generate \
a remediation report.

## Findings

{findings_text}

## Instructions

Respond in the following JSON format (no markdown fences):
{{
  "executive_summary": "2-3 sentence overview for management",
  "technical_details": "Detailed technical analysis of key vulnerabilities",
  "remediation_plan": "Step-by-step remediation guide, ordered by priority"
}}

Focus on:
1. Most critical vulnerabilities first
2. Quick wins vs long-term fixes
3. Specific commands or config changes where possible
"""


def _format_findings(findings: list[Finding]) -> str:
    """Format findings into a readable text block for the AI prompt."""
    lines: list[str] = []
    for i, f in enumerate(findings, 1):
        parts = [
            f"### {i}. [{f.severity.value.upper()}] {f.title}",
            f"   Host: {f.host}" + (f":{f.port}" if f.port else ""),
        ]
        if f.url:
            parts.append(f"   URL: {f.url}")
        if f.description:
            # Truncate long descriptions to keep prompt size manageable
            desc = f.description[:300]
            parts.append(f"   Description: {desc}")
        if f.cve_ids:
            parts.append(f"   CVEs: {f.cve_ids}")
        if f.evidence:
            parts.append(f"   Evidence: {f.evidence[:200]}")
        lines.append("\n".join(parts))

    return "\n\n".join(lines)


async def check_ollama_available() -> bool:
    """Return True if Ollama is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            return r.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


async def list_models() -> list[str]:
    """List available models in the local Ollama instance."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            if r.status_code == 200:
                models = r.json().get("models", [])
                return [m["name"] for m in models]
    except Exception:
        pass
    return []


async def generate_report(
    target: str,
    findings: list[Finding],
    *,
    model: str | None = None,
) -> dict[str, str]:
    """Generate an AI remediation report for the given findings.

    Returns a dict with keys: executive_summary, technical_details, remediation_plan, ai_model_used.
    Falls back to a template-based report if Ollama is unavailable.
    """
    model = model or settings.ollama_model

    if not findings:
        return {
            "executive_summary": f"No vulnerabilities were found in the scan of {target}.",
            "technical_details": "All scans completed without detecting any issues.",
            "remediation_plan": "No action required. Continue regular security assessments.",
            "ai_model_used": "none",
        }

    findings_text = _format_findings(findings)
    prompt = _REPORT_PROMPT_TEMPLATE.format(target=target, findings_text=findings_text)

    if not await check_ollama_available():
        logger.warning("Ollama unavailable — falling back to template report")
        return _fallback_report(target, findings)

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=120.0)) as client:
            r = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "system": _SYSTEM_PROMPT,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.3, "num_predict": 2048},
                },
            )

            if r.status_code != 200:
                logger.error("Ollama returned %d: %s", r.status_code, r.text[:300])
                return _fallback_report(target, findings)

            body = r.json()
            response_text = body.get("response", "")

            try:
                parsed = json.loads(response_text)
                return {
                    "executive_summary": parsed.get("executive_summary", ""),
                    "technical_details": parsed.get("technical_details", ""),
                    "remediation_plan": parsed.get("remediation_plan", ""),
                    "ai_model_used": model,
                }
            except json.JSONDecodeError:
                # Model returned plain text — use it as the summary
                return {
                    "executive_summary": response_text[:500],
                    "technical_details": response_text,
                    "remediation_plan": "See technical details above.",
                    "ai_model_used": model,
                }

    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.error("Ollama request failed: %s", exc)
        return _fallback_report(target, findings)


def _fallback_report(target: str, findings: list[Finding]) -> dict[str, str]:
    """Generate a basic template report when Ollama is not available."""
    severity_counts: dict[str, int] = {}
    for f in findings:
        severity_counts[f.severity.value] = severity_counts.get(f.severity.value, 0) + 1

    total = len(findings)
    summary_parts = [f"Security scan of {target} found {total} issue(s): "]
    for sev in ("critical", "high", "medium", "low", "info"):
        count = severity_counts.get(sev, 0)
        if count:
            summary_parts.append(f"{count} {sev.upper()}")

    details_lines: list[str] = []
    for f in findings:
        line = f"- [{f.severity.value.upper()}] {f.title} on {f.host}"
        if f.port:
            line += f":{f.port}"
        if f.cve_ids:
            line += f" ({f.cve_ids})"
        details_lines.append(line)

    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    remediation_lines: list[str] = ["Priority-ordered remediation steps:", ""]
    for i, f in enumerate(
        sorted(findings, key=lambda x: sev_order.get(x.severity.value, 5)),
        1,
    ):
        rem = f.remediation or "Investigate and apply vendor-recommended fix."
        remediation_lines.append(f"{i}. {f.title}: {rem}")

    return {
        "executive_summary": ", ".join(summary_parts),
        "technical_details": "\n".join(details_lines),
        "remediation_plan": "\n".join(remediation_lines),
        "ai_model_used": "fallback-template",
    }

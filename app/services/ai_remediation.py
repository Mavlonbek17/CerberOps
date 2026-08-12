"""AI remediation report generation via local Ollama.

Design principles applied:
- temperature=0.1  → deterministic, factual output; no creative hallucinations
- Strict system guardrails → model cannot exaggerate severity or recommend
  deprecated APIs (e.g. X-XSS-Protection)
- Mini-RAG context block → modern security standards injected directly into
  every prompt so the model doesn't rely on potentially stale training data
"""

import logging

from app.config import settings
from app.models import Finding
from app.services.ollama_client import check_ollama_available, generate_json, list_models, to_str

logger = logging.getLogger(__name__)

__all__ = ["check_ollama_available", "generate_report", "list_models"]

# ── System prompt: strict guardrails ─────────────────────────────────────────
_SYSTEM_PROMPT = """\
You are an expert Application Security Engineer (AppSec / DevSecOps specialist) \
working inside the CerberOps vulnerability orchestration platform.

Your job is to analyze raw scan findings and produce a precise, accurate, \
actionable remediation report in valid JSON.

STRICT ACCURACY RULES — follow these exactly:

1. TLS/SSL STANDARDS
   - TLS 1.2 is SECURE and fully industry-standard. Do NOT mark it as critical.
   - Recommend TLS 1.3 as an optional upgrade only.
   - TLS 1.0 and TLS 1.1 ARE deprecated — flag those as HIGH severity.

2. HTTP SECURITY HEADERS
   - RECOMMEND: Content-Security-Policy, X-Frame-Options (SAMEORIGIN),
     X-Content-Type-Options (nosniff), Strict-Transport-Security (HSTS),
     Referrer-Policy, Permissions-Policy.
   - DO NOT recommend X-XSS-Protection — it is deprecated in modern browsers.

3. SEVERITY CALIBRATION
   - CRITICAL: RCE, SQLi, auth bypass, exposed credentials, SSRF.
   - HIGH: XSS, CSRF, open redirect, insecure deserialization, CVEs ≥ CVSS 7.
   - MEDIUM: Missing security headers, outdated software (no known exploit),
     verbose error messages, unnecessary open ports.
   - LOW: Informational disclosures, best-practice gaps, TLS 1.2 on secure configs.
   - Do NOT exaggerate. An open port with no exploit is LOW or INFO, not CRITICAL.

4. OUTPUT FORMAT
   - Respond ONLY with valid JSON — no markdown, no fences, no extra text.
   - All three fields (executive_summary, technical_details, remediation_plan)
     must be plain strings, not nested objects or arrays.
   - remediation_plan must be human-readable numbered steps as a single string.

5. COMMANDS & CONFIGS
   - Provide real server commands (Nginx, Apache, systemd, ufw, iptables).
   - Prefer copy-pasteable one-liners where possible.
   - Do not invent flags or options that do not exist.
"""

# ── OWASP mini-RAG context block ─────────────────────────────────────────────
# Injected into every prompt so the model uses current standards, not memory
_OWASP_CONTEXT = """\
=== MODERN WEB SECURITY REFERENCE (use this as ground truth) ===

RECOMMENDED HTTP HEADERS:
  Content-Security-Policy: default-src 'self'
  X-Frame-Options: SAMEORIGIN
  X-Content-Type-Options: nosniff
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=()

TLS:
  Secure:     TLS 1.2, TLS 1.3
  Deprecated: TLS 1.0, TLS 1.1, SSLv3

EMAIL / DMARC POLICIES:
  p=none       → Monitoring only (no enforcement)
  p=quarantine → Soft fail (spam folder)
  p=reject     → Strict enforcement (recommended)

COMMON PORT RISK LEVELS:
  22 (SSH)        → Low if key-auth; High if password-auth exposed
  21 (FTP)        → High (plaintext credentials)
  23 (Telnet)     → Critical (unencrypted)
  3306 (MySQL)    → High if externally exposed
  6379 (Redis)    → Critical if no auth and externally exposed
  27017 (MongoDB) → High if no auth
  80/443          → Info (expected web ports)
  8080/8443       → Medium if admin panels exposed

OWASP TOP 10 (2021):
  A01 Broken Access Control
  A02 Cryptographic Failures
  A03 Injection (SQLi, XSS, etc.)
  A04 Insecure Design
  A05 Security Misconfiguration
  A06 Vulnerable & Outdated Components
  A07 Identification & Authentication Failures
  A08 Software & Data Integrity Failures
  A09 Security Logging & Monitoring Failures
  A10 Server-Side Request Forgery (SSRF)

=== END REFERENCE ===
"""

# ── Report prompt template ────────────────────────────────────────────────────
_REPORT_PROMPT_TEMPLATE = """\
{owasp_context}

You are analyzing a security scan of: {target}

=== SCAN FINDINGS ===

{findings_text}

=== TASK ===

Generate a security remediation report. Respond with ONLY this JSON (no fences):
{{
  "executive_summary": "2-4 sentence non-technical overview for management. State what was scanned, what was found, and the overall risk level. Be accurate — do not exaggerate.",
  "technical_details": "Detailed technical analysis. For each significant finding: explain what it means, why it matters, and its CVSS/severity rationale. Reference OWASP categories where applicable.",
  "remediation_plan": "Numbered step-by-step remediation guide ordered by priority (highest severity first). Include specific commands, config snippets, or code examples where applicable. Each step must be actionable."
}}
"""


def _format_findings(findings: list[Finding]) -> str:
    """Format findings into a structured text block for the AI prompt."""
    lines: list[str] = []
    for i, f in enumerate(findings, 1):
        parts = [
            f"[{i}] Severity: {f.severity.value.upper()} | {f.title}",
            f"    Host: {f.host}" + (f":{f.port}" if f.port else ""),
        ]
        if f.url:
            parts.append(f"    URL: {f.url}")
        if f.description:
            parts.append(f"    Description: {f.description[:400]}")
        if f.cve_ids:
            parts.append(f"    CVEs: {', '.join(f.cve_ids)}")
        if f.evidence:
            parts.append(f"    Evidence: {f.evidence[:200]}")
        if f.remediation:
            parts.append(f"    Scanner hint: {f.remediation[:200]}")
        lines.append("\n".join(parts))
    return "\n\n".join(lines)


async def generate_report(
    target: str,
    findings: list[Finding],
    *,
    model: str | None = None,
) -> dict[str, str]:
    """Generate an AI remediation report for the given findings.

    Returns a dict with keys: executive_summary, technical_details,
    remediation_plan, ai_model_used.
    Falls back to a template-based report if Ollama is unavailable.
    """
    model = model or settings.ollama_model

    if not findings:
        return {
            "executive_summary": (
                f"The security scan of {target} completed successfully and found "
                "no vulnerabilities. The target appears to be well-configured."
            ),
            "technical_details": (
                "All enabled scanners completed their checks without detecting "
                "any issues. Continue scheduling regular scans to maintain this posture."
            ),
            "remediation_plan": (
                "No immediate action required.\n"
                "1. Schedule recurring scans (weekly recommended).\n"
                "2. Monitor for new CVEs affecting your software stack.\n"
                "3. Review OWASP Top 10 annually against your architecture."
            ),
            "ai_model_used": "none",
        }

    findings_text = _format_findings(findings)
    prompt = _REPORT_PROMPT_TEMPLATE.format(
        owasp_context=_OWASP_CONTEXT,
        target=target,
        findings_text=findings_text,
    )

    if not await check_ollama_available():
        logger.warning("Ollama unavailable — falling back to template report")
        return _fallback_report(target, findings)

    parsed = await generate_json(
        prompt=prompt,
        system=_SYSTEM_PROMPT,
        model=model,
        temperature=0.1,     # Near-deterministic: facts not creativity
        num_predict=2048,
        timeout=180.0,
    )

    if parsed is None:
        logger.warning("Ollama call failed or returned non-JSON; using fallback report")
        return _fallback_report(target, findings)

    return {
        "executive_summary": to_str(parsed.get("executive_summary", "")),
        "technical_details": to_str(parsed.get("technical_details", "")),
        "remediation_plan": to_str(parsed.get("remediation_plan", "")),
        "ai_model_used": model,
    }


def _fallback_report(target: str, findings: list[Finding]) -> dict[str, str]:
    """Generate a structured text report when Ollama is unavailable."""
    severity_counts: dict[str, int] = {}
    for f in findings:
        severity_counts[f.severity.value] = severity_counts.get(f.severity.value, 0) + 1

    total = len(findings)
    sev_summary = ", ".join(
        f"{c} {s.upper()}"
        for s in ("critical", "high", "medium", "low", "info")
        if (c := severity_counts.get(s, 0)) > 0
    )

    summary = (
        f"Security scan of {target} identified {total} finding(s): {sev_summary}. "
        "Review the technical details below and prioritize remediation starting with "
        "the highest severity items."
    )

    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_findings = sorted(findings, key=lambda x: sev_order.get(x.severity.value, 5))

    details_lines: list[str] = []
    for f in sorted_findings:
        line = f"[{f.severity.value.upper()}] {f.title} — {f.host}"
        if f.port:
            line += f":{f.port}"
        if f.cve_ids:
            line += f" | CVEs: {', '.join(f.cve_ids)}"
        if f.description:
            line += f"\n  {f.description[:200]}"
        details_lines.append(line)

    remediation_lines: list[str] = []
    for i, f in enumerate(sorted_findings, 1):
        rem = f.remediation or "Investigate and apply vendor-recommended fix."
        remediation_lines.append(f"{i}. [{f.severity.value.upper()}] {f.title}\n   → {rem}")

    return {
        "executive_summary": summary,
        "technical_details": "\n\n".join(details_lines),
        "remediation_plan": "\n\n".join(remediation_lines),
        "ai_model_used": "fallback-template",
    }

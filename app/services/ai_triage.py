"""AI False Positive Filter — "Zero-Noise Mode".

Scanners like Nuclei and ZAP generate a lot of noise: generic 403/404 pages
flagged as "sensitive file exposure", WAF block pages flagged as real
vulnerabilities, etc. Before findings are shown to the user, this service
asks the local LLM to review borderline (low/medium severity) findings
against their raw evidence and drop the ones that are clearly false
positives — without ever dropping high/critical findings, which are always
shown for human review.
"""

import logging

from app.adapters.base import RawFinding
from app.config import settings
from app.models import AiVerdict
from app.services.ollama_client import check_ollama_available, generate_json

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a strict security triage analyst. You review borderline vulnerability \
scanner findings and decide whether each one is a REAL issue or a FALSE POSITIVE.

RULES:
1. A finding is a FALSE POSITIVE if the evidence shows a generic error page \
(403 Forbidden, 404 Not Found, WAF/CDN block page, empty body) instead of the \
actual sensitive content the scanner claims to have found.
2. A finding is a FALSE POSITIVE if the "evidence" is boilerplate text that \
appears on every page of the site (e.g. a cookie banner, a login form) \
misidentified as a vulnerability.
3. A finding is CONFIRMED if the evidence plausibly shows the actual \
vulnerable behavior (e.g. real file contents, a real error stack trace, a \
real injected payload reflected back, a real open port/service banner).
4. When in doubt, mark it CONFIRMED — never silently hide a possible real \
issue. Only mark FALSE POSITIVE when you are quite confident.
5. Respond with ONLY valid JSON, no markdown fences, no extra text.
"""

_PROMPT_TEMPLATE = """\
Review this single scanner finding and decide: CONFIRMED or FALSE_POSITIVE.

Title: {title}
Scanner: {scanner}
Host: {host}
URL: {url}
Description: {description}
Evidence (raw response/output, truncated): {evidence}

Respond with ONLY this JSON:
{{
  "verdict": "CONFIRMED" or "FALSE_POSITIVE",
  "reason": "one short sentence explaining why"
}}
"""


async def triage_findings(
    findings: list[RawFinding],
) -> list[tuple[RawFinding, AiVerdict, str | None]]:
    """Review low/medium severity findings and tag each with an AI verdict.

    High/Critical/Info findings are always passed through as UNREVIEWED —
    triage is intentionally conservative and only spends AI cycles on the
    noisy middle tier, where false positives are most common.

    Returns a list of (finding, verdict, notes) tuples in the same order
    as the input. Nothing is ever dropped from the list — callers decide
    whether to hide FALSE_POSITIVE findings from the default UI view.
    """
    if not settings.ai_triage_enabled or not findings:
        return [(f, AiVerdict.UNREVIEWED, None) for f in findings]

    triage_severities = {
        s.strip().lower() for s in settings.ai_triage_severities.split(",") if s.strip()
    }

    if not await check_ollama_available():
        logger.info("Ollama unavailable — skipping AI triage, all findings stay UNREVIEWED")
        return [(f, AiVerdict.UNREVIEWED, None) for f in findings]

    results: list[tuple[RawFinding, AiVerdict, str | None]] = []

    for finding in findings:
        if finding.severity.value not in triage_severities:
            results.append((finding, AiVerdict.UNREVIEWED, None))
            continue

        verdict, notes = await _triage_one(finding)
        results.append((finding, verdict, notes))

    dropped = sum(1 for _, v, _ in results if v == AiVerdict.LIKELY_FALSE_POSITIVE)
    if dropped:
        logger.info("AI triage flagged %d/%d findings as likely false positives", dropped, len(findings))

    return results


async def _triage_one(finding: RawFinding) -> tuple[AiVerdict, str | None]:
    """Ask the LLM to classify a single finding. Fails open (CONFIRMED) on error."""
    prompt = _PROMPT_TEMPLATE.format(
        title=finding.title,
        scanner=finding.scanner_source,
        host=finding.host,
        url=finding.url or "N/A",
        description=(finding.description or "")[:400],
        evidence=(finding.evidence or "N/A")[:500],
    )

    parsed = await generate_json(
        prompt=prompt,
        system=_SYSTEM_PROMPT,
        temperature=0.0,   # Fully deterministic — this is a binary classification
        num_predict=150,
        timeout=30.0,
    )

    if not parsed:
        # Fail open: never silently hide a finding just because the AI call failed
        return AiVerdict.UNREVIEWED, None

    raw_verdict = str(parsed.get("verdict", "")).strip().upper()
    reason = parsed.get("reason")
    reason = str(reason)[:500] if reason else None

    if raw_verdict == "FALSE_POSITIVE":
        return AiVerdict.LIKELY_FALSE_POSITIVE, reason
    if raw_verdict == "CONFIRMED":
        return AiVerdict.CONFIRMED, reason

    return AiVerdict.UNREVIEWED, reason

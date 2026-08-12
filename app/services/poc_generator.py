"""Autonomous Proof-of-Concept Generator.

For High/Critical findings, developers often can't tell if a scanner's
"possible SQL injection" or "possible RCE" is real. This service asks the
local LLM to write a small, safe verification script (Python + requests, or
a single curl command) that reproduces the finding so a developer can run
it themselves and see the result — without CerberOps ever executing an
exploit automatically.

This is generation only. Nothing here runs the generated code.
"""

import logging

from app.config import settings
from app.models import Finding
from app.services.ollama_client import check_ollama_available, generate_json

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a security engineer writing SAFE, READ-ONLY verification scripts for \
authorized penetration testing and bug bounty work. Given one confirmed \
vulnerability finding, write a small Python script (using the `requests` \
library) that a developer can run to verify whether the vulnerability is \
real — reproducing the exact request the scanner used.

STRICT RULES:
1. The script must be DEFENSIVE/VERIFICATION only: it sends one or a small \
handful of requests and prints whether the behavior was reproduced. It must \
NEVER perform destructive actions (no data deletion, no write operations \
beyond what is strictly needed to prove the vulnerability, no privilege \
escalation, no lateral movement, no payload chains beyond proving the bug).
2. Assume the user has explicit authorization to test this target — this is \
for their own application or an authorized engagement.
3. Include a comment at the top reminding the user to only run this against \
systems they own or have written permission to test.
4. Keep the script under 40 lines. Use only the `requests` library (already \
a common dependency) — do not import anything exotic.
5. Print a clear "[CONFIRMED]" or "[NOT REPRODUCED]" message based on the \
response, so the output is unambiguous.
6. Respond with ONLY valid JSON, no markdown fences, no extra text.
"""

_PROMPT_TEMPLATE = """\
Finding to verify:

Title: {title}
Severity: {severity}
Host: {host}
Port: {port}
URL: {url}
Description: {description}
CVEs: {cves}
Evidence (from the scanner, may include curl command / matcher / extracted data): {evidence}
Scanner: {scanner}

Write a verification script for this finding.

Respond with ONLY this JSON:
{{
  "poc_code": "the full Python script as a single string with \\n newlines",
  "explanation": "2-3 sentences explaining what the script does and how to read its output"
}}
"""


async def generate_poc(finding: Finding) -> dict[str, str] | None:
    """Generate a safe verification script for a single finding.

    Returns None if PoC generation is disabled, Ollama is unavailable, or
    the finding's severity doesn't warrant it (only High/Critical are
    supported — verifying a missing security header needs no exploit code).
    """
    if not settings.ai_poc_enabled:
        return None

    if finding.severity.value not in ("critical", "high"):
        return None

    if not await check_ollama_available():
        logger.info("Ollama unavailable — cannot generate PoC for finding %s", finding.id)
        return None

    prompt = _PROMPT_TEMPLATE.format(
        title=finding.title,
        severity=finding.severity.value.upper(),
        host=finding.host,
        port=finding.port or "N/A",
        url=finding.url or "N/A",
        description=(finding.description or "")[:500],
        cves=finding.cve_ids or "N/A",
        evidence=(finding.evidence or "N/A")[:600],
        scanner=finding.scanner_source,
    )

    parsed = await generate_json(
        prompt=prompt,
        system=_SYSTEM_PROMPT,
        model=settings.ollama_model,
        temperature=0.1,
        num_predict=1024,
        timeout=90.0,
    )

    if not parsed:
        logger.warning("PoC generation failed for finding %s", finding.id)
        return None

    poc_code = str(parsed.get("poc_code", "")).strip()
    explanation = str(parsed.get("explanation", "")).strip()

    if not poc_code:
        return None

    return {
        "poc_code": poc_code,
        "poc_explanation": explanation or "Run this script to verify the finding.",
        "poc_model_used": settings.ollama_model,
    }

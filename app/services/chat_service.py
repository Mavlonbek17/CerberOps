"""Chat With Your Scan — conversational Q&A over a completed scan's findings.

Loads the scan's findings + AI report into the model's context and lets the
user ask natural-language questions ("Did you find any exposed databases?",
"What's the most urgent thing to fix?"). Conversation history is kept
client-side and passed in on each request — no server-side chat storage.
"""

import logging

from app.config import settings
from app.models import Finding, Report, ScanJob
from app.services.ollama_client import check_ollama_available, generate

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are CerberOps AI, a security analyst assistant. You are given the full \
results of a vulnerability scan (findings + remediation report) and must \
answer the user's questions about it accurately and concisely.

RULES:
1. Only reference facts present in the scan data you were given. Never \
invent vulnerabilities, hosts, ports, or CVEs that are not in the data.
2. If the user asks about something not covered by the scan, say so plainly \
instead of guessing.
3. Prefer short, direct, practical answers. Include exact commands or \
config snippets when the user asks how to fix something.
4. If asked to summarize for a non-technical audience (e.g. "for my \
manager"), write in plain language without jargon.
5. Respond in plain text (not JSON) — this is a normal chat conversation.
"""

_CONTEXT_TEMPLATE = """\
=== SCAN CONTEXT: {target} ===

Findings ({count} total):
{findings_text}

AI Remediation Report:
{report_text}

=== END SCAN CONTEXT ===

Conversation so far:
{history_text}

User: {message}

Respond as CerberOps AI. Answer only the user's latest message, using the \
scan context above as ground truth.
"""


def _format_findings_for_chat(findings: list[Finding], limit: int) -> str:
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_findings = sorted(findings, key=lambda f: sev_order.get(f.severity.value, 5))[:limit]

    lines: list[str] = []
    for f in sorted_findings:
        line = f"- [{f.severity.value.upper()}] {f.title} on {f.host}"
        if f.port:
            line += f":{f.port}"
        if f.cve_ids:
            line += f" (CVEs: {f.cve_ids})"
        if f.ai_verdict.value == "likely_false_positive":
            line += " [AI FLAGGED AS LIKELY FALSE POSITIVE]"
        lines.append(line)

    if len(findings) > limit:
        lines.append(f"... and {len(findings) - limit} more findings not shown here for brevity.")

    return "\n".join(lines) if lines else "No findings were detected in this scan."


def _format_history(history: list[dict]) -> str:
    if not history:
        return "(no prior turns)"
    lines = []
    for turn in history[-10:]:  # keep the last 10 turns to bound prompt size
        role = "User" if turn.get("role") == "user" else "CerberOps AI"
        lines.append(f"{role}: {turn.get('content', '')}")
    return "\n".join(lines)


async def chat_about_scan(
    job: ScanJob,
    findings: list[Finding],
    report: Report | None,
    message: str,
    history: list[dict],
) -> dict[str, str]:
    """Answer a user question about a completed scan.

    Returns {"response": str, "ai_model_used": str}.
    """
    if not await check_ollama_available():
        return {
            "response": (
                "The local AI engine (Ollama) is currently unavailable, so I can't "
                "answer questions right now. You can still review the findings and "
                "report directly in the dashboard."
            ),
            "ai_model_used": "none",
        }

    findings_text = _format_findings_for_chat(findings, settings.ai_chat_max_findings)
    report_text = (
        f"Executive Summary: {report.executive_summary}\n\n"
        f"Remediation Plan: {report.remediation_plan}"
        if report
        else "No AI report has been generated for this scan yet."
    )

    prompt = _CONTEXT_TEMPLATE.format(
        target=job.target,
        count=len(findings),
        findings_text=findings_text,
        report_text=report_text,
        history_text=_format_history(history),
        message=message,
    )

    response_text = await generate(
        prompt=prompt,
        system=_SYSTEM_PROMPT,
        temperature=0.2,
        num_predict=800,
        json_mode=False,
        timeout=90.0,
    )

    if response_text is None:
        return {
            "response": "The AI engine failed to respond. Please try again in a moment.",
            "ai_model_used": "none",
        }

    return {"response": response_text.strip(), "ai_model_used": settings.ollama_model}

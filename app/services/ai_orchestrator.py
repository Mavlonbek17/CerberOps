"""AI Orchestrator — the reasoning layer that takes the full enriched scan context
(asset inventory, tech stack, CVE enrichment, baseline diff, MITRE techniques, compliance
gaps) and asks the local Ollama model to produce a unified, prioritized threat narrative.

This is what makes CerberOps's AI decisions richer than a single scan's raw findings —
the model reasons over everything we know about the target, not just this one run.
"""

import logging

from app.config import settings
from app.models import Finding
from app.services.ollama_client import check_ollama_available, generate

logger = logging.getLogger(__name__)

_FALLBACK_NARRATIVE = (
    "AI orchestration is unavailable (Ollama offline or errored). "
    "Review findings by severity and CVSS score, prioritize any newly introduced "
    "critical/high findings from the baseline diff, and check the compliance summary "
    "for regulatory exposure."
)

_SYSTEM_PROMPT = """\
You are a senior security analyst producing a prioritized threat briefing for a \
DevSecOps team. Be concise, factual, and grounded only in the scan intelligence \
provided — never invent findings, hosts, or CVEs that are not in the data.
"""


def _build_context(
    target: str,
    findings: list[Finding],
    asset_summary: dict,
    baseline_summary: dict,
    mitre_summary: list[dict],
    compliance_summary: dict,
) -> str:
    critical_high = [f for f in findings if f.severity.value in ("critical", "high")]
    new_count = baseline_summary.get("new_count", len(findings))
    resolved_count = len(baseline_summary.get("resolved", []))

    lines = [
        f"Target: {target}",
        f"Total findings: {len(findings)} ({len(critical_high)} critical/high)",
        f"New since last scan: {new_count} | Resolved since last scan: {resolved_count}",
        f"Discovered subdomains: {len(asset_summary.get('subdomains', []))}",
        f"Detected technology stack: {', '.join(asset_summary.get('tech_stack', [])) or 'unknown'}",
        "",
        "Top findings (critical/high):",
    ]
    for f in critical_high[:10]:
        cve_str = f" [{f.cve_ids}]" if f.cve_ids else ""
        lines.append(f"- {f.title} on {f.host} (CVSS {f.cvss_score or 'N/A'}){cve_str}")

    if mitre_summary:
        lines.append("")
        lines.append("MITRE ATT&CK techniques observed:")
        for t in mitre_summary[:8]:
            lines.append(f"- {t['technique_id']} {t['technique_name']} ({t['tactic']}) — {t['finding_count']} finding(s)")

    owasp_items = compliance_summary.get("owasp_top10", [])
    if owasp_items:
        lines.append("")
        lines.append("Compliance exposure (OWASP Top 10):")
        for item in owasp_items[:6]:
            lines.append(f"- {item['framework_id']} — {item['finding_count']} finding(s), max severity {item['max_severity']}")

    return "\n".join(lines)


async def generate_threat_narrative(
    target: str,
    findings: list[Finding],
    asset_summary: dict,
    baseline_summary: dict,
    mitre_summary: list[dict],
    compliance_summary: dict,
) -> str:
    """Produce a prioritized, human-readable threat narrative using the local LLM.
    Fails open with a static fallback narrative if Ollama is unavailable."""
    context = _build_context(target, findings, asset_summary, baseline_summary, mitre_summary, compliance_summary)

    prompt = (
        "You are a senior security analyst producing a prioritized threat briefing for "
        "a DevSecOps team. Given the scan intelligence below, write a concise (max 300 words) "
        "threat narrative that:\n"
        "1. States the overall risk posture in one sentence\n"
        "2. Highlights what changed since the last scan (new vs resolved issues)\n"
        "3. Names the single most urgent action to take, and why\n"
        "4. Notes any compliance/regulatory exposure worth flagging to management\n\n"
        f"SCAN INTELLIGENCE:\n{context}\n\n"
        "Write the briefing now, in plain prose (no markdown headers):"
    )

    try:
        if not await check_ollama_available():
            logger.warning("Ollama unavailable — using fallback threat narrative for %s", target)
            return _FALLBACK_NARRATIVE

        text = await generate(
            prompt=prompt,
            system=_SYSTEM_PROMPT,
            model=settings.ollama_model,
            temperature=0.2,
            num_predict=600,
            json_mode=False,
            timeout=120.0,
        )
        if not text:
            return _FALLBACK_NARRATIVE
        return text.strip()
    except Exception:
        logger.exception("AI orchestrator failed to generate threat narrative for %s", target)
        return _FALLBACK_NARRATIVE

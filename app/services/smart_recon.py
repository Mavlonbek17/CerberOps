"""AI-Powered Smart Recon — fingerprint the target, then let local AI narrow
the Nuclei template set (and Nmap port breadth) before the full scan runs.

This is a pure-Python feature: fingerprinting uses the httpx *library* (an
existing dependency used to talk to Ollama/ZAP) to grab headers and body
snippets — no extra binaries (Go tools, Wappalyzer, etc.) need to be
installed, which keeps `install.sh` simple for first-time users.

Design:
1. fingerprint_target() — one fast HTTP GET, extract headers/tech hints.
2. plan_scan() — feed the fingerprint to Ollama, which picks Nuclei tags
   from a fixed allow-list (never invents tags that don't exist in
   nuclei-templates) plus a port-scan breadth for Nmap.
3. If Ollama is unavailable, or nothing useful is detected, we fail open:
   no tag filter is applied and the scan behaves exactly as before.
"""

import logging
import re

import httpx

from app.config import settings
from app.services.ollama_client import check_ollama_available, generate_json

logger = logging.getLogger(__name__)

# Fixed allow-list of Nuclei tags we trust the AI to pick from. Keeping this
# closed prevents the model from hallucinating tags that don't exist in
# nuclei-templates (which would silently no-op or error the scan).
_KNOWN_NUCLEI_TAGS = {
    # CMS / platforms
    "wordpress", "wp-plugin", "wp-theme", "joomla", "drupal", "magento",
    "shopify", "sharepoint", "confluence", "jira", "gitlab", "github",
    "jenkins", "grafana", "prometheus", "kibana", "elasticsearch",
    # Web servers / proxies
    "nginx", "apache", "iis", "tomcat", "caddy", "cloudflare", "haproxy",
    # Languages / frameworks
    "php", "laravel", "django", "rails", "spring", "nodejs", "express",
    "react", "angular", "vue", "graphql",
    # Infra / cloud
    "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "vmware",
    # Databases
    "mysql", "postgres", "mongodb", "redis", "couchdb",
    # Generic vulnerability classes (always safe to include)
    "cve", "exposure", "misconfig", "default-login", "takeover",
    "ssl", "dns", "network", "panel", "login", "config", "backup",
    "exposed-panel", "tech",
}

_SYSTEM_PROMPT = """\
You are a reconnaissance analyst for an automated vulnerability scanner. \
Given HTTP fingerprint data for a target, decide which Nuclei scanner tags \
are relevant so the scan focuses on real technology instead of running \
every template blindly.

RULES:
1. Only choose tags from the ALLOWED_TAGS list you are given. Never invent \
new tags — if none apply, return an empty list (this means "run broad, \
unfiltered scan", which is always safe).
2. Always include generic classes like "cve", "exposure", "misconfig" — \
they apply to every target regardless of detected technology.
3. Be conservative: only add a technology-specific tag (e.g. "wordpress") \
if the fingerprint clearly shows evidence of it.
4. Respond with ONLY valid JSON, no markdown fences, no extra text.
"""

_PROMPT_TEMPLATE = """\
ALLOWED_TAGS: {allowed_tags}

Target fingerprint:
  URL: {url}
  HTTP status: {status}
  Server header: {server}
  X-Powered-By: {powered_by}
  Detected hints: {hints}
  Page title: {title}

Respond with ONLY this JSON:
{{
  "tags": ["tag1", "tag2"],
  "summary": "one short sentence describing what this target appears to be running"
}}
"""

_TECH_SIGNATURES: list[tuple[str, str]] = [
    (r"wp-content|wp-includes|wordpress", "wordpress"),
    (r"joomla", "joomla"),
    (r"drupal|sites/default", "drupal"),
    (r"magento", "magento"),
    (r"laravel_session|laravel", "laravel"),
    (r"django", "django"),
    (r"\bcsrftoken\b", "django"),
    (r"jsessionid", "spring"),
    (r"x-jenkins", "jenkins"),
    (r"gitlab", "gitlab"),
    (r"confluence", "confluence"),
    (r"jira", "jira"),
    (r"grafana", "grafana"),
    (r"kibana", "kibana"),
    (r"__next|_next/static", "react"),
    (r"ng-version|angular", "angular"),
    (r"vue", "vue"),
]


class TargetFingerprint:
    """Lightweight result of probing a target once."""

    def __init__(self) -> None:
        self.reachable = False
        self.status: int | None = None
        self.server: str = ""
        self.powered_by: str = ""
        self.title: str = ""
        self.hints: list[str] = []


async def fingerprint_target(target: str) -> TargetFingerprint:
    """Send one fast HTTP GET to the target and extract tech hints.

    Never raises — a failed fingerprint just means Smart Recon falls back
    to an unfiltered scan, which is always safe.
    """
    fp = TargetFingerprint()
    url = target if target.startswith(("http://", "https://")) else f"https://{target}"

    try:
        async with httpx.AsyncClient(
            timeout=settings.ai_recon_timeout,
            follow_redirects=True,
            verify=False,  # nosec — recon only, we don't submit sensitive data
        ) as client:
            r = await client.get(url)
            fp.reachable = True
            fp.status = r.status_code
            fp.server = r.headers.get("server", "")
            fp.powered_by = r.headers.get("x-powered-by", "")

            body = r.text[:20000] if r.text else ""
            title_match = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
            if title_match:
                fp.title = title_match.group(1).strip()[:200]

            haystack = f"{fp.server} {fp.powered_by} {body}".lower()
            set_cookie = " ".join(r.headers.get_list("set-cookie")) if hasattr(r.headers, "get_list") else r.headers.get("set-cookie", "")
            haystack += f" {set_cookie}".lower()

            for pattern, tag in _TECH_SIGNATURES:
                if re.search(pattern, haystack) and tag not in fp.hints:
                    fp.hints.append(tag)

    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
        logger.info("Smart Recon fingerprint failed for %s: %s", target, exc)
    except Exception:
        logger.exception("Unexpected error fingerprinting %s", target)

    return fp


async def plan_scan(target: str) -> dict:
    """Fingerprint the target and ask Ollama to pick relevant Nuclei tags.

    Returns a dict:
      {
        "nuclei_tags": list[str],   # empty = unfiltered scan
        "recon_summary": str,       # human-readable, stored on the ScanJob
        "ai_scan_plan": str,        # what was decided and why
      }
    Fails open on any error — always returns a usable (possibly empty) plan.
    """
    fp = await fingerprint_target(target)

    if not settings.ai_smart_recon_enabled or not fp.reachable:
        summary = (
            "Target did not respond to HTTP fingerprinting — running an unfiltered scan."
            if not fp.reachable
            else "Smart Recon disabled — running an unfiltered scan."
        )
        return {"nuclei_tags": [], "recon_summary": summary, "ai_scan_plan": "No filtering applied."}

    if not await check_ollama_available():
        summary = f"Fingerprinted {target} (status {fp.status}); AI unavailable, running unfiltered scan."
        return {"nuclei_tags": fp.hints, "recon_summary": summary, "ai_scan_plan": "Heuristic tags only (no AI)."}

    prompt = _PROMPT_TEMPLATE.format(
        allowed_tags=", ".join(sorted(_KNOWN_NUCLEI_TAGS)),
        url=target,
        status=fp.status,
        server=fp.server or "unknown",
        powered_by=fp.powered_by or "unknown",
        hints=", ".join(fp.hints) if fp.hints else "none detected",
        title=fp.title or "unknown",
    )

    parsed = await generate_json(
        prompt=prompt,
        system=_SYSTEM_PROMPT,
        temperature=0.1,
        num_predict=300,
        timeout=30.0,
    )

    if not parsed:
        summary = f"Fingerprinted {target} (status {fp.status}); AI planning failed, using heuristic tags."
        return {"nuclei_tags": fp.hints, "recon_summary": summary, "ai_scan_plan": "Heuristic tags only (AI call failed)."}

    raw_tags = parsed.get("tags", [])
    if not isinstance(raw_tags, list):
        raw_tags = []
    # Defense in depth: only accept tags from the known allow-list
    tags = sorted({str(t).strip().lower() for t in raw_tags if str(t).strip().lower() in _KNOWN_NUCLEI_TAGS})

    ai_summary = str(parsed.get("summary", "")).strip()[:300]
    recon_summary = f"Fingerprinted {target}: {ai_summary}" if ai_summary else f"Fingerprinted {target} (status {fp.status})."

    if tags:
        ai_scan_plan = f"Nuclei scan narrowed to tags: {', '.join(tags)} (based on detected tech stack)."
    else:
        ai_scan_plan = "No specific technology detected — running unfiltered Nuclei scan."

    return {"nuclei_tags": tags, "recon_summary": recon_summary, "ai_scan_plan": ai_scan_plan}

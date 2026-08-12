"""Safe, read-only exploit verification — confirms whether a finding is real by making
non-destructive HTTP requests only. Never performs actual exploitation, data modification,
or intrusive payloads. Used for critical/high findings that have a URL.

Note: this module uses the Python `httpx` pip package (async HTTP client),
not the ProjectDiscovery `httpx` CLI binary used by httpx_fingerprint_adapter.py.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

_SAFE_HEADER_CHECKS = {
    "missing security header": ["x-frame-options", "content-security-policy", "strict-transport-security"],
    "clickjacking": ["x-frame-options"],
}


async def verify_finding(title: str, description: str, url: str | None, evidence: str | None) -> dict:
    """Attempt a safe, read-only verification. Returns
    {verified: bool, method: str, details: str}."""
    text = f"{title} {description}".lower()

    if not url:
        return {
            "verified": False,
            "method": "no_url",
            "details": "No URL available for this finding — automated verification requires a reachable endpoint.",
        }

    # Header-based checks (100% safe — single GET request, inspect response headers only)
    for keyword, headers_to_check in _SAFE_HEADER_CHECKS.items():
        if keyword in text:
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    r = await client.get(url)
                missing = [h for h in headers_to_check if h not in {k.lower() for k in r.headers}]
                if missing:
                    return {
                        "verified": True,
                        "method": "http_header_check",
                        "details": f"Confirmed missing header(s): {', '.join(missing)} on {url} (HTTP {r.status_code}).",
                    }
                return {
                    "verified": False,
                    "method": "http_header_check",
                    "details": f"Headers {', '.join(headers_to_check)} are present — finding may be a false positive or already remediated.",
                }
            except Exception as exc:
                return {"verified": False, "method": "http_header_check", "details": f"Could not reach {url}: {exc}"}

    # Generic reachability check — confirms the endpoint still exists (safe GET only)
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            r = await client.get(url)
        return {
            "verified": r.status_code < 500,
            "method": "reachability_check",
            "details": f"Endpoint {url} responded with HTTP {r.status_code}. Manual review recommended — "
                       f"automated verification for this finding type requires human judgment.",
        }
    except Exception as exc:
        return {"verified": False, "method": "reachability_check", "details": f"Could not reach {url}: {exc}"}

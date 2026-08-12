"""Simple CVSS score estimation based on severity and evidence."""

_BASE_SCORES: dict[str, float] = {
    "critical": 9.0,
    "high": 7.5,
    "medium": 5.0,
    "low": 2.0,
    "info": 0.0,
}


def estimate_cvss(
    severity: str,
    cve_ids: list[str] | None = None,
    evidence: str | None = None,
) -> tuple[float, str]:
    """Return (score, vector_string) estimated from severity.

    This is a heuristic approximation — not a standards-compliant CVSS
    calculation.  Use real CVSS data when available (e.g. from NVD).
    """
    base = _BASE_SCORES.get(severity.lower(), 0.0)
    # Slight boost if CVE present (means it's a known exploitable vuln)
    if cve_ids:
        base = min(10.0, base + 0.5)
    score = round(base, 1)

    vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U"
    if severity.lower() in ("critical", "high"):
        vector += "/C:H/I:H/A:H"
    elif severity.lower() == "medium":
        vector += "/C:L/I:L/A:L"
    else:
        vector += "/C:N/I:N/A:N"

    return score, vector

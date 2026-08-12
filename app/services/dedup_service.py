"""Deduplication engine — merge duplicate findings from multiple scanners."""

import hashlib

from app.adapters.base import RawFinding


def _fingerprint(finding: RawFinding) -> str:
    """Generate a deterministic fingerprint for a finding.

    Two findings are duplicates when they describe the same vulnerability
    on the same host/port combination.
    """
    parts = [
        finding.host.lower(),
        str(finding.port or ""),
        finding.title.lower().strip(),
    ]
    # Include the first CVE if available for precision
    if finding.cve_ids:
        parts.append(finding.cve_ids[0].upper())

    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def deduplicate(findings: list[RawFinding]) -> list[tuple[str, RawFinding]]:
    """Deduplicate a list of raw findings.

    Returns a list of (fingerprint, merged_finding) tuples.  Duplicate
    entries are merged: scanner_sources are combined, evidence is
    concatenated, and the highest severity wins.
    """
    seen: dict[str, RawFinding] = {}
    source_map: dict[str, set[str]] = {}

    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

    for f in findings:
        fp = _fingerprint(f)

        if fp not in seen:
            seen[fp] = f
            source_map[fp] = {f.scanner_source}
            continue

        # Merge into existing
        existing = seen[fp]
        source_map[fp].add(f.scanner_source)

        # Keep the higher severity
        if severity_rank.get(f.severity.value, 0) > severity_rank.get(existing.severity.value, 0):
            existing.severity = f.severity

        # Append evidence
        if f.evidence and f.evidence not in (existing.evidence or ""):
            existing.evidence = (
                f"{existing.evidence}; [{f.scanner_source}] {f.evidence}"
                if existing.evidence
                else f"[{f.scanner_source}] {f.evidence}"
            )

        # Merge CVEs
        for cve in f.cve_ids:
            if cve not in existing.cve_ids:
                existing.cve_ids.append(cve)

        # Merge references
        for ref in f.reference_urls:
            if ref not in existing.reference_urls:
                existing.reference_urls.append(ref)

        # Prefer non-empty remediation
        if f.remediation and not existing.remediation:
            existing.remediation = f.remediation

        # Prefer non-empty description
        if f.description and not existing.description:
            existing.description = f.description

    # Attach merged sources to each finding
    results: list[tuple[str, RawFinding]] = []
    for fp, finding in seen.items():
        finding.scanner_source = ", ".join(sorted(source_map[fp]))
        results.append((fp, finding))

    return results

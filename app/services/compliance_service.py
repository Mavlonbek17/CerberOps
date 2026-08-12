"""Best-effort compliance mapping — maps findings to OWASP Top 10 (2021), PCI-DSS,
NIST SP 800-53, and ISO 27001 based on keyword classification.

This is a heuristic aid for prioritization, not a substitute for a formal compliance audit.
"""

from app.models import Finding

_SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]

# (keywords, owasp_category, pci_requirement, nist_control, iso_control)
_MAPPING: list[tuple[list[str], str, str, str, str]] = [
    (["sql injection", "sqli", "command injection", "rce"],
     "A03:2021 - Injection", "PCI-DSS 6.5.1", "NIST SI-10", "ISO 27001 A.14.2.5"),
    (["cross-site scripting", "xss", "csrf"],
     "A03:2021 - Injection", "PCI-DSS 6.5.7", "NIST SI-10", "ISO 27001 A.14.2.5"),
    (["default credential", "weak password", "weak credential", "authentication bypass", "broken auth"],
     "A07:2021 - Identification and Authentication Failures", "PCI-DSS 8.2", "NIST IA-5", "ISO 27001 A.9.4.3"),
    (["missing security header", "clickjacking", "ssl", "tls", "certificate"],
     "A05:2021 - Security Misconfiguration", "PCI-DSS 6.5.4", "NIST SC-8", "ISO 27001 A.13.1.1"),
    (["exposed database", "directory listing", "information disclosure", "sensitive data exposure", "exposed file"],
     "A01:2021 - Broken Access Control", "PCI-DSS 3.4", "NIST AC-3", "ISO 27001 A.9.1.1"),
    (["outdated", "end of life", "unsupported version", "cve-"],
     "A06:2021 - Vulnerable and Outdated Components", "PCI-DSS 6.2", "NIST SI-2", "ISO 27001 A.12.6.1"),
    (["ssrf", "open port", "exposed service"],
     "A10:2021 - Server-Side Request Forgery", "PCI-DSS 1.3", "NIST SC-7", "ISO 27001 A.13.1.3"),
]

_DESCRIPTIONS = {
    "PCI-DSS 6.5.1": "Injection flaws, particularly SQL injection",
    "PCI-DSS 6.5.7": "Cross-site scripting (XSS)",
    "PCI-DSS 8.2": "User authentication management",
    "PCI-DSS 6.5.4": "Insecure communications",
    "PCI-DSS 3.4": "Render PAN unreadable / access control",
    "PCI-DSS 6.2": "Ensure systems are protected from known vulnerabilities",
    "PCI-DSS 1.3": "Prohibit direct public access to internal network",
    "NIST SI-10": "Information Input Validation",
    "NIST IA-5": "Authenticator Management",
    "NIST SC-8": "Transmission Confidentiality and Integrity",
    "NIST AC-3": "Access Enforcement",
    "NIST SI-2": "Flaw Remediation",
    "NIST SC-7": "Boundary Protection",
    "ISO 27001 A.14.2.5": "Secure system engineering principles",
    "ISO 27001 A.9.4.3": "Password management system",
    "ISO 27001 A.13.1.1": "Network controls",
    "ISO 27001 A.9.1.1": "Access control policy",
    "ISO 27001 A.12.6.1": "Management of technical vulnerabilities",
    "ISO 27001 A.13.1.3": "Segregation in networks",
}


def _classify(title: str, description: str) -> tuple[list[str], list[str], list[str], list[str]]:
    """Return (owasp[], pci[], nist[], iso[]) matches for one finding."""
    text = f"{title} {description}".lower()
    owasp, pci, nist, iso = [], [], [], []
    for keywords, o, p, n, i in _MAPPING:
        if any(kw in text for kw in keywords):
            owasp.append(o)
            pci.append(p)
            nist.append(n)
            iso.append(i)
    return owasp, pci, nist, iso


def classify_finding(title: str, description: str) -> str | None:
    """Return the primary OWASP category for a single finding (used to tag Finding.owasp_category)."""
    owasp, _, _, _ = _classify(title, description)
    return owasp[0] if owasp else None


def compute_compliance_summary(findings: list[Finding]) -> dict:
    """Aggregate compliance coverage across all findings in a scan."""
    buckets: dict[str, dict] = {"owasp_top10": {}, "pci_dss": {}, "nist_800_53": {}, "iso_27001": {}}

    for f in findings:
        owasp, pci, nist, iso = _classify(f.title, f.description)
        sev_rank = _SEVERITY_ORDER.index(f.severity.value) if f.severity.value in _SEVERITY_ORDER else 0

        for key, items in (
            ("owasp_top10", owasp),
            ("pci_dss", pci),
            ("nist_800_53", nist),
            ("iso_27001", iso),
        ):
            for item in items:
                bucket = buckets[key].setdefault(item, {"count": 0, "max_rank": 0})
                bucket["count"] += 1
                bucket["max_rank"] = max(bucket["max_rank"], sev_rank)

    result = {}
    for key, entries in buckets.items():
        result[key] = [
            {
                "framework_id": fid,
                "description": _DESCRIPTIONS.get(fid, fid),
                "finding_count": data["count"],
                "max_severity": _SEVERITY_ORDER[data["max_rank"]],
            }
            for fid, data in sorted(entries.items(), key=lambda x: -x[1]["max_rank"])
        ]
    return result

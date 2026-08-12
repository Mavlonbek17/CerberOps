"""Best-effort MITRE ATT&CK technique mapping based on finding title/description keywords.

This is a heuristic classifier for prioritization — not an authoritative mapping.
"""

_KEYWORD_MAP: list[tuple[list[str], str, str, str]] = [
    # (keywords, technique_id, technique_name, tactic)
    (["sql injection", "sqli"], "T1190", "Exploit Public-Facing Application", "Initial Access"),
    (["remote code execution", "rce", "command injection"], "T1190", "Exploit Public-Facing Application", "Initial Access"),
    (["cross-site scripting", "xss"], "T1059.007", "JavaScript", "Execution"),
    (["default credential", "weak password", "weak credential"], "T1078", "Valid Accounts", "Defense Evasion"),
    (["directory listing", "path traversal", "exposed file"], "T1083", "File and Directory Discovery", "Discovery"),
    (["open port", "exposed service", "unencrypted service"], "T1046", "Network Service Discovery", "Discovery"),
    (["ssrf", "server-side request forgery"], "T1190", "Exploit Public-Facing Application", "Initial Access"),
    (["exposed database", "database exposed", "mongodb", "elasticsearch exposed"], "T1530", "Data from Cloud Storage", "Collection"),
    (["outdated", "end of life", "unsupported version", "cve-"], "T1190", "Exploit Public-Facing Application", "Initial Access"),
    (["missing security header", "clickjacking", "x-frame-options"], "T1189", "Drive-by Compromise", "Initial Access"),
    (["ssl", "tls", "certificate"], "T1040", "Network Sniffing", "Credential Access"),
    (["information disclosure", "sensitive data exposure"], "T1213", "Data from Information Repositories", "Collection"),
    (["csrf", "cross-site request forgery"], "T1189", "Drive-by Compromise", "Initial Access"),
    (["authentication bypass", "broken auth"], "T1078", "Valid Accounts", "Defense Evasion"),
]


def map_finding_to_mitre(title: str, description: str) -> list[tuple[str, str, str]]:
    """Return list of (technique_id, technique_name, tactic) matches for a finding."""
    text = f"{title} {description}".lower()
    matches: list[tuple[str, str, str]] = []
    seen_ids: set[str] = set()
    for keywords, tid, tname, tactic in _KEYWORD_MAP:
        if any(kw in text for kw in keywords) and tid not in seen_ids:
            matches.append((tid, tname, tactic))
            seen_ids.add(tid)
    return matches

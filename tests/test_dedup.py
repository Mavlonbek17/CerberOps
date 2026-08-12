"""Tests for the deduplication engine."""

from app.adapters.base import RawFinding
from app.models import Severity
from app.services.dedup_service import deduplicate


class TestDeduplication:
    def test_no_duplicates(self):
        findings = [
            RawFinding(title="Port 80 open", host="1.2.3.4", port=80, scanner_source="nmap", severity=Severity.INFO),
            RawFinding(title="Port 443 open", host="1.2.3.4", port=443, scanner_source="nmap", severity=Severity.INFO),
        ]
        result = deduplicate(findings)
        assert len(result) == 2

    def test_merges_same_finding_different_scanners(self):
        findings = [
            RawFinding(
                title="Port 80 open",
                host="1.2.3.4",
                port=80,
                scanner_source="nmap",
                severity=Severity.INFO,
                evidence="nmap-evidence",
            ),
            RawFinding(
                title="Port 80 open",
                host="1.2.3.4",
                port=80,
                scanner_source="nuclei",
                severity=Severity.MEDIUM,
                evidence="nuclei-evidence",
            ),
        ]
        result = deduplicate(findings)
        assert len(result) == 1
        fingerprint, merged = result[0]
        # Higher severity wins
        assert merged.severity == Severity.MEDIUM
        # Both sources recorded
        assert "nmap" in merged.scanner_source
        assert "nuclei" in merged.scanner_source

    def test_cve_dedup_precision(self):
        findings = [
            RawFinding(
                title="CVE-2024-1234",
                host="1.2.3.4",
                port=443,
                scanner_source="nuclei",
                cve_ids=["CVE-2024-1234"],
                severity=Severity.HIGH,
            ),
            RawFinding(
                title="CVE-2024-1234",
                host="1.2.3.4",
                port=443,
                scanner_source="zap",
                cve_ids=["CVE-2024-1234"],
                severity=Severity.HIGH,
            ),
        ]
        result = deduplicate(findings)
        assert len(result) == 1

    def test_different_hosts_not_merged(self):
        findings = [
            RawFinding(title="Port 80 open", host="1.2.3.4", port=80, scanner_source="nmap"),
            RawFinding(title="Port 80 open", host="5.6.7.8", port=80, scanner_source="nmap"),
        ]
        result = deduplicate(findings)
        assert len(result) == 2

    def test_merges_cve_lists(self):
        findings = [
            RawFinding(title="vuln", host="1.2.3.4", port=80, scanner_source="a", cve_ids=["CVE-2024-0001"]),
            RawFinding(title="vuln", host="1.2.3.4", port=80, scanner_source="b", cve_ids=["CVE-2024-0001", "CVE-2024-0002"]),
        ]
        result = deduplicate(findings)
        assert len(result) == 1
        _, merged = result[0]
        assert "CVE-2024-0001" in merged.cve_ids
        assert "CVE-2024-0002" in merged.cve_ids

    def test_empty_list(self):
        assert deduplicate([]) == []

    def test_keeps_remediation_from_scanner_that_has_it(self):
        findings = [
            RawFinding(title="vuln", host="1.2.3.4", port=80, scanner_source="nmap"),
            RawFinding(title="vuln", host="1.2.3.4", port=80, scanner_source="zap", remediation="Upgrade to v2"),
        ]
        result = deduplicate(findings)
        _, merged = result[0]
        assert merged.remediation == "Upgrade to v2"

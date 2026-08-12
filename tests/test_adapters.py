"""Tests for scanner adapters — XML/JSON parsing logic."""

from app.adapters.nmap_adapter import NmapScanner
from app.adapters.nuclei_adapter import NucleiScanner
from app.models import Severity


class TestNmapParser:
    """Test Nmap XML parsing without running actual scans."""

    SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
    <nmaprun>
      <host>
        <address addr="93.184.216.34" addrtype="ipv4"/>
        <hostnames><hostname name="example.com" type="user"/></hostnames>
        <ports>
          <port protocol="tcp" portid="80">
            <state state="open"/>
            <service name="http" product="nginx" version="1.24.0"/>
          </port>
          <port protocol="tcp" portid="443">
            <state state="open"/>
            <service name="https" product="nginx" version="1.24.0"/>
          </port>
          <port protocol="tcp" portid="22">
            <state state="filtered"/>
            <service name="ssh"/>
          </port>
        </ports>
      </host>
    </nmaprun>"""

    def test_parses_open_ports(self):
        scanner = NmapScanner()
        findings = scanner._parse_xml(self.SAMPLE_XML)
        open_findings = [f for f in findings if "open" in (f.evidence or "")]
        assert len(open_findings) >= 2

    def test_extracts_service_info(self):
        scanner = NmapScanner()
        findings = scanner._parse_xml(self.SAMPLE_XML)
        http_finding = next(f for f in findings if f.port == 80)
        assert "nginx" in http_finding.title
        assert http_finding.host == "93.184.216.34"
        assert http_finding.protocol == "tcp"

    def test_correct_severity_for_filtered(self):
        scanner = NmapScanner()
        findings = scanner._parse_xml(self.SAMPLE_XML)
        ssh_finding = next(f for f in findings if f.port == 22)
        assert ssh_finding.severity == Severity.LOW

    def test_empty_xml(self):
        scanner = NmapScanner()
        findings = scanner._parse_xml("<nmaprun></nmaprun>")
        assert findings == []

    def test_malformed_xml(self):
        scanner = NmapScanner()
        findings = scanner._parse_xml("not xml at all")
        assert findings == []


class TestNucleiParser:
    """Test Nuclei JSONL parsing."""

    SAMPLE_JSONL = """\
{"template-id":"ssl-issuer","info":{"name":"SSL Certificate Issuer","severity":"info","tags":["ssl"],"description":"Detects the SSL certificate issuer."},"host":"https://example.com","matched-at":"https://example.com:443"}
{"template-id":"cve-2024-1234","info":{"name":"Critical RCE","severity":"critical","tags":["cve","rce"],"description":"Remote code execution","classification":{"cve-id":["CVE-2024-1234"]},"reference":["https://nvd.nist.gov/vuln/detail/CVE-2024-1234"],"remediation":"Upgrade to latest version"},"host":"https://example.com","matched-at":"https://example.com/api","port":443}
"""

    def test_parses_findings(self):
        scanner = NucleiScanner()
        findings = scanner._parse_jsonl(self.SAMPLE_JSONL)
        assert len(findings) == 2

    def test_severity_mapping(self):
        scanner = NucleiScanner()
        findings = scanner._parse_jsonl(self.SAMPLE_JSONL)
        info_finding = next(f for f in findings if f.title == "SSL Certificate Issuer")
        assert info_finding.severity == Severity.INFO
        crit_finding = next(f for f in findings if f.title == "Critical RCE")
        assert crit_finding.severity == Severity.CRITICAL

    def test_cve_extraction(self):
        scanner = NucleiScanner()
        findings = scanner._parse_jsonl(self.SAMPLE_JSONL)
        crit = next(f for f in findings if f.severity == Severity.CRITICAL)
        assert "CVE-2024-1234" in crit.cve_ids

    def test_remediation_extracted(self):
        scanner = NucleiScanner()
        findings = scanner._parse_jsonl(self.SAMPLE_JSONL)
        crit = next(f for f in findings if f.severity == Severity.CRITICAL)
        assert crit.remediation == "Upgrade to latest version"

    def test_empty_input(self):
        scanner = NucleiScanner()
        assert scanner._parse_jsonl("") == []

    def test_invalid_json(self):
        scanner = NucleiScanner()
        findings = scanner._parse_jsonl("not json\nalso not json")
        assert findings == []

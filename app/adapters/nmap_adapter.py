"""Nmap scanner adapter — subprocess execution + XML parsing."""

import asyncio
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from app.adapters.base import BaseScanner, RawFinding
from app.config import settings
from app.core.exceptions import ScannerError, ScannerNotFoundError, ScannerTimeoutError
from app.models import Severity

# Map Nmap port states to severity
_STATE_SEVERITY = {
    "open": Severity.INFO,
    "filtered": Severity.LOW,
    "open|filtered": Severity.LOW,
}

# Known risky services
_RISKY_SERVICES: dict[str, Severity] = {
    "telnet": Severity.HIGH,
    "ftp": Severity.MEDIUM,
    "smb": Severity.MEDIUM,
    "microsoft-ds": Severity.MEDIUM,
    "netbios-ssn": Severity.MEDIUM,
    "rexec": Severity.HIGH,
    "rlogin": Severity.HIGH,
    "rsh": Severity.HIGH,
    "vnc": Severity.MEDIUM,
    "rdp": Severity.MEDIUM,
    "ms-wbt-server": Severity.MEDIUM,
    "mysql": Severity.MEDIUM,
    "postgresql": Severity.MEDIUM,
    "mongodb": Severity.HIGH,
    "redis": Severity.HIGH,
    "memcached": Severity.HIGH,
    "elasticsearch": Severity.HIGH,
}


class NmapScanner(BaseScanner):
    name = "nmap"

    async def is_available(self) -> bool:
        return shutil.which("nmap") is not None

    async def get_version(self) -> str | None:
        try:
            proc = await asyncio.create_subprocess_exec(
                "nmap", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            for line in stdout.decode().splitlines():
                if "Nmap version" in line or "nmap version" in line.lower():
                    return line.strip()
        except FileNotFoundError:
            return None
        return None

    async def run(self, target: str, **options: object) -> list[RawFinding]:
        if not await self.is_available():
            raise ScannerNotFoundError(
                "nmap", "Nmap is not installed. Install via: apt install nmap / brew install nmap"
            )

        with tempfile.TemporaryDirectory(prefix="cerberops_nmap_") as tmp:
            xml_path = Path(tmp) / "scan.xml"
            cmd = self._build_command(target, str(xml_path), **options)

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=settings.nmap_timeout
                )
            except TimeoutError as exc:
                proc.kill()
                raise ScannerTimeoutError(
                    "nmap", f"Scan timed out after {settings.nmap_timeout}s"
                ) from exc
            except FileNotFoundError as exc:
                raise ScannerNotFoundError("nmap", "Nmap binary not found in PATH") from exc

            if proc.returncode != 0 and not xml_path.exists():
                raise ScannerError("nmap", f"Nmap failed: {stderr.decode()[:500]}")

            if not xml_path.exists():
                return []

            return self._parse_xml(xml_path.read_text())

    def _build_command(self, target: str, xml_path: str, **options: object) -> list[str]:
        """Build the nmap command with safe defaults."""
        # Strip URL scheme for nmap (it only takes hosts/IPs)
        host = target
        for prefix in ("https://", "http://", "ftp://"):
            if host.startswith(prefix):
                host = host[len(prefix):]
        host = host.rstrip("/").split("/")[0]

        ports = str(options.get("ports", "")) or "--top-ports 100"
        cmd = [
            "nmap",
            "-sV",                # Service/version detection
            "--open",             # Only show open ports
            "-T4",                # Aggressive timing
            "--host-timeout", "120s",
        ]
        if ports.startswith("--"):
            cmd.extend(ports.split())
        else:
            cmd.extend(["-p", ports])
        cmd.extend([
            "-oX", xml_path,      # XML output
            "--no-stylesheet",
            host,
        ])
        return cmd

    def _parse_xml(self, xml_content: str) -> list[RawFinding]:
        """Parse Nmap XML output into normalized findings."""
        findings: list[RawFinding] = []
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            return findings

        for host_el in root.findall(".//host"):
            addr_el = host_el.find("address")
            if addr_el is None:
                continue
            host_addr = addr_el.get("addr", "unknown")

            hostname = host_addr
            hostnames_el = host_el.find("hostnames/hostname")
            if hostnames_el is not None:
                hostname = hostnames_el.get("name", host_addr)

            for port_el in host_el.findall(".//port"):
                state_el = port_el.find("state")
                valid_states = ("open", "filtered", "open|filtered")
                if state_el is None or state_el.get("state") not in valid_states:
                    continue

                portid = port_el.get("portid", "0")
                protocol = port_el.get("protocol", "tcp")
                state = state_el.get("state", "unknown")

                service_el = port_el.find("service")
                has_svc = service_el is not None
                service_name = service_el.get("name", "unknown") if has_svc else "unknown"
                service_product = service_el.get("product", "") if has_svc else ""
                service_version = service_el.get("version", "") if has_svc else ""

                version_str = f"{service_product} {service_version}".strip()
                default_sev = _STATE_SEVERITY.get(state, Severity.INFO)
                severity = _RISKY_SERVICES.get(service_name, default_sev)

                title = f"Open port {portid}/{protocol} — {service_name}"
                if version_str:
                    title += f" ({version_str})"

                description = (
                    f"Port {portid}/{protocol} is {state} on {hostname} ({host_addr}). "
                    f"Service: {service_name}"
                )
                if version_str:
                    description += f", Version: {version_str}"

                evidence_parts = [f"state={state}", f"service={service_name}"]
                if version_str:
                    evidence_parts.append(f"version={version_str}")

                # Parse NSE script output for vulnerabilities
                cve_ids: list[str] = []
                for script_el in port_el.findall("script"):
                    script_output = script_el.get("output", "")
                    if "CVE-" in script_output:
                        import re
                        cve_ids.extend(re.findall(r"CVE-\d{4}-\d{4,}", script_output))
                    evidence_parts.append(f"script:{script_el.get('id', '')}={script_output[:200]}")

                if cve_ids:
                    severity = Severity.HIGH

                findings.append(RawFinding(
                    title=title,
                    description=description,
                    severity=severity,
                    host=host_addr,
                    port=int(portid),
                    protocol=protocol,
                    evidence="; ".join(evidence_parts),
                    scanner_source="nmap",
                    cve_ids=cve_ids,
                ))

        return findings

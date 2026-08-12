"""Nuclei scanner adapter — subprocess execution + JSONL parsing."""

import asyncio
import json
import shutil
import tempfile
from pathlib import Path

from app.adapters.base import BaseScanner, RawFinding
from app.config import settings
from app.core.exceptions import ScannerError, ScannerNotFoundError, ScannerTimeoutError
from app.models import Severity

_NUCLEI_SEVERITY_MAP: dict[str, Severity] = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
    "info": Severity.INFO,
    "unknown": Severity.INFO,
}


class NucleiScanner(BaseScanner):
    name = "nuclei"

    async def is_available(self) -> bool:
        return shutil.which("nuclei") is not None

    async def get_version(self) -> str | None:
        try:
            proc = await asyncio.create_subprocess_exec(
                "nuclei", "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            output = (stdout or stderr).decode()
            for line in output.splitlines():
                if "nuclei" in line.lower():
                    return line.strip()
        except FileNotFoundError:
            return None
        return None

    async def run(self, target: str, **options: object) -> list[RawFinding]:
        if not await self.is_available():
            raise ScannerNotFoundError(
                "nuclei",
                "Nuclei is not installed. Install via: "
                "go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
            )

        with tempfile.TemporaryDirectory(prefix="cerberops_nuclei_") as tmp:
            output_path = Path(tmp) / "results.jsonl"
            cmd = self._build_command(target, str(output_path), **options)

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=settings.nuclei_timeout
                )
            except TimeoutError as exc:
                proc.kill()
                raise ScannerTimeoutError(
                    "nuclei", f"Scan timed out after {settings.nuclei_timeout}s"
                ) from exc
            except FileNotFoundError as exc:
                raise ScannerNotFoundError(
                    "nuclei", "Nuclei binary not found in PATH"
                ) from exc

            if not output_path.exists():
                # Nuclei exits 0 even if no results — check stderr for real errors
                err = stderr.decode()[:500] if stderr else ""
                if proc.returncode != 0:
                    raise ScannerError("nuclei", f"Nuclei failed (exit {proc.returncode}): {err}")
                return []

            return self._parse_jsonl(output_path.read_text())

    def _build_command(self, target: str, output_path: str, **options: object) -> list[str]:
        severity_filter = str(options.get("severity", "")) or "critical,high,medium,low,info"
        cmd = [
            "nuclei",
            "-u", target,
            "-jsonl",
            "-o", output_path,
            "-silent",
            "-severity", severity_filter,
            "-no-color",
            "-omit-raw",
        ]

        # Optionally limit templates
        templates = options.get("templates")
        if templates and isinstance(templates, str):
            cmd.extend(["-t", templates])

        # AI Smart Recon: narrow the template set to detected technologies
        tags = options.get("tags")
        if tags and isinstance(tags, list) and tags:
            cmd.extend(["-tags", ",".join(str(t) for t in tags)])

        return cmd

    def _parse_jsonl(self, content: str) -> list[RawFinding]:
        """Parse Nuclei JSONL output into normalized findings."""
        findings: list[RawFinding] = []

        for line in content.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                result = json.loads(line)
            except json.JSONDecodeError:
                continue

            info = result.get("info", {})
            severity_str = info.get("severity", "info").lower()
            severity = _NUCLEI_SEVERITY_MAP.get(severity_str, Severity.INFO)

            # Extract CVEs from classification
            classification = info.get("classification", {})
            cve_ids = classification.get("cve-id") or []
            if isinstance(cve_ids, str):
                cve_ids = [cve_ids]

            # References
            reference = info.get("reference") or []
            if isinstance(reference, str):
                reference = [reference]

            # Host & URL
            host = result.get("host", result.get("ip", ""))
            matched_url = result.get("matched-at", result.get("matched_at", ""))
            port = result.get("port")

            title = info.get("name", result.get("template-id", "Unknown"))
            template_id = result.get("template-id", result.get("templateID", ""))

            description_parts = []
            if info.get("description"):
                description_parts.append(info["description"])
            if template_id:
                description_parts.append(f"Template: {template_id}")
            if info.get("tags"):
                tags = info["tags"]
                if isinstance(tags, list):
                    tags = ", ".join(tags)
                description_parts.append(f"Tags: {tags}")

            # Evidence
            evidence_parts = []
            if result.get("matcher-name"):
                evidence_parts.append(f"matcher={result['matcher-name']}")
            if result.get("extracted-results"):
                evidence_parts.append(f"extracted={result['extracted-results']}")
            if result.get("curl-command"):
                evidence_parts.append(f"curl={result['curl-command'][:200]}")

            findings.append(RawFinding(
                title=title,
                description="\n".join(description_parts),
                severity=severity,
                host=host,
                port=int(port) if port else None,
                url=matched_url or None,
                evidence="; ".join(evidence_parts) if evidence_parts else None,
                scanner_source="nuclei",
                cve_ids=cve_ids,
                reference_urls=reference,
                remediation=info.get("remediation"),
            ))

        return findings

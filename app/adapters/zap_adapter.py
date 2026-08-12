"""OWASP ZAP scanner adapter — REST API integration."""

import asyncio

import httpx

from app.adapters.base import BaseScanner, RawFinding
from app.config import settings
from app.core.exceptions import ScannerError, ScannerTimeoutError
from app.models import Severity

_ZAP_RISK_MAP: dict[str, Severity] = {
    "0": Severity.INFO,
    "1": Severity.LOW,
    "2": Severity.MEDIUM,
    "3": Severity.HIGH,
}

_ZAP_CONFIDENCE = {"0": "False Positive", "1": "Low", "2": "Medium", "3": "High", "4": "Confirmed"}


class ZapScanner(BaseScanner):
    name = "zap"

    def __init__(self) -> None:
        self._base_url = settings.zap_api_url.rstrip("/")
        self._api_key = settings.zap_api_key

    def _params(self, **extra: str) -> dict[str, str]:
        params = {}
        if self._api_key:
            params["apikey"] = self._api_key
        params.update(extra)
        return params

    async def is_available(self) -> bool:
        try:
            url = f"{self._base_url}/JSON/core/view/version/"
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(url, params=self._params())
                return r.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def get_version(self) -> str | None:
        try:
            url = f"{self._base_url}/JSON/core/view/version/"
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(url, params=self._params())
                if r.status_code == 200:
                    return r.json().get("version")
        except Exception:
            return None
        return None

    async def run(self, target: str, **options: object) -> list[RawFinding]:
        if not await self.is_available():
            raise ScannerError(
                "zap",
                f"ZAP is not reachable at {self._base_url}. "
                "Start ZAP in daemon mode: docker run -d -p 8080:8080 "
                "zaproxy/zap-stable zap.sh -daemon -port 8080",
            )

        timeout = settings.zap_timeout
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=30.0)) as client:
            # 1. Start spider
            await self._spider(client, target, timeout)

            # 2. Start active scan
            await self._active_scan(client, target, timeout)

            # 3. Collect alerts
            return await self._get_alerts(client, target)

    async def _spider(self, client: httpx.AsyncClient, target: str, timeout: int) -> None:
        """Run ZAP spider on the target URL."""
        r = await client.get(
            f"{self._base_url}/JSON/spider/action/scan/",
            params=self._params(url=target, maxChildren="10", recurse="true"),
        )
        if r.status_code != 200:
            raise ScannerError("zap", f"Failed to start spider: {r.text[:300]}")

        scan_id = r.json().get("scan", "0")
        elapsed = 0
        poll_interval = 5

        while elapsed < timeout // 2:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            status_r = await client.get(
                f"{self._base_url}/JSON/spider/view/status/",
                params=self._params(scanId=str(scan_id)),
            )
            if status_r.status_code == 200 and status_r.json().get("status", "0") == "100":
                break
        else:
            raise ScannerTimeoutError("zap", f"Spider timed out after {timeout // 2}s")

    async def _active_scan(self, client: httpx.AsyncClient, target: str, timeout: int) -> None:
        """Run ZAP active scan."""
        r = await client.get(
            f"{self._base_url}/JSON/ascan/action/scan/",
            params=self._params(url=target, recurse="true"),
        )
        if r.status_code != 200:
            raise ScannerError("zap", f"Failed to start active scan: {r.text[:300]}")

        scan_id = r.json().get("scan", "0")
        elapsed = 0
        poll_interval = 10

        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            status_r = await client.get(
                f"{self._base_url}/JSON/ascan/view/status/",
                params=self._params(scanId=str(scan_id)),
            )
            if status_r.status_code == 200 and status_r.json().get("status", "0") == "100":
                break
        else:
            raise ScannerTimeoutError("zap", f"Active scan timed out after {timeout}s")

    async def _get_alerts(self, client: httpx.AsyncClient, target: str) -> list[RawFinding]:
        """Fetch all alerts from ZAP and convert to normalized findings."""
        r = await client.get(
            f"{self._base_url}/JSON/alert/view/alerts/",
            params=self._params(baseurl=target, start="0", count="500"),
        )
        if r.status_code != 200:
            raise ScannerError("zap", f"Failed to fetch alerts: {r.text[:300]}")

        alerts = r.json().get("alerts", [])
        findings: list[RawFinding] = []

        for alert in alerts:
            risk = str(alert.get("riskcode", "0"))
            severity = _ZAP_RISK_MAP.get(risk, Severity.INFO)
            confidence = _ZAP_CONFIDENCE.get(str(alert.get("confidence", "0")), "Unknown")

            cve_ids: list[str] = []
            cwe_id = alert.get("cweid", "")
            reference = alert.get("reference", "")
            ref_urls = [u.strip() for u in reference.split("\n") if u.strip().startswith("http")]

            # Extract port from URL
            url = alert.get("url", "")
            port = None
            if url:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                port = parsed.port

            evidence_parts = []
            if alert.get("evidence"):
                evidence_parts.append(f"evidence={alert['evidence'][:300]}")
            if alert.get("param"):
                evidence_parts.append(f"param={alert['param']}")
            if alert.get("attack"):
                evidence_parts.append(f"attack={alert['attack'][:200]}")
            evidence_parts.append(f"confidence={confidence}")
            if cwe_id and cwe_id != "-1":
                evidence_parts.append(f"CWE-{cwe_id}")

            desc = alert.get("desc", "")
            desc = desc.replace("<p>", "").replace("</p>", "\n").strip()
            alert_url = alert.get("url", "")
            host_val = alert_url.split("/")[2] if "/" in alert_url else target
            solution = alert.get("solution", "")
            solution = solution.replace("<p>", "").replace("</p>", "\n").strip()

            findings.append(RawFinding(
                title=alert.get("name", alert.get("alert", "Unknown")),
                description=desc,
                severity=severity,
                host=host_val,
                port=port,
                url=url or None,
                evidence="; ".join(evidence_parts) or None,
                scanner_source="zap",
                cve_ids=cve_ids,
                reference_urls=ref_urls,
                remediation=solution or None,
            ))

        return findings

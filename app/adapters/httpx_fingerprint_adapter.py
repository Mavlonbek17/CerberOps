"""Tech fingerprinting adapter — wraps ProjectDiscovery's `httpx` CLI tool.

Note: this is the Go-based ProjectDiscovery CLI binary, NOT the Python
`httpx` pip package used elsewhere in this codebase for async HTTP calls.
"""

import asyncio
import json
import logging
import shutil

logger = logging.getLogger(__name__)


class HttpxFingerprintRunner:
    name = "httpx_fingerprint"

    async def is_available(self) -> bool:
        return shutil.which("httpx") is not None

    async def run(self, hosts: list[str], timeout: int = 60) -> list[dict]:
        """Fingerprint each host. Returns list of dicts:
        {url, status_code, title, tech: [...]}."""
        if not hosts or not await self.is_available():
            return []
        input_data = "\n".join(hosts).encode()
        try:
            proc = await asyncio.create_subprocess_exec(
                "httpx", "-silent", "-json", "-tech-detect", "-title",
                "-status-code", "-timeout", "10",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(input=input_data), timeout=timeout)
        except (TimeoutError, Exception):
            logger.warning("httpx fingerprint failed or timed out")
            return []

        results: list[dict] = []
        for line in stdout.decode(errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                results.append({
                    "url": data.get("url", ""),
                    "status_code": data.get("status_code"),
                    "title": data.get("title"),
                    "tech": data.get("tech", []),
                })
            except json.JSONDecodeError:
                continue
        return results

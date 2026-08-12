"""Subfinder adapter — passive subdomain enumeration via ProjectDiscovery's subfinder."""

import asyncio
import json
import logging
import shutil

logger = logging.getLogger(__name__)


class SubfinderRunner:
    name = "subfinder"

    async def is_available(self) -> bool:
        return shutil.which("subfinder") is not None

    async def run(self, domain: str, max_results: int = 15, timeout: int = 60) -> list[str]:
        """Return a list of discovered subdomains (capped at max_results)."""
        if not await self.is_available():
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "subfinder", "-d", domain, "-silent", "-json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except (TimeoutError, Exception):
            logger.warning("subfinder failed or timed out for %s", domain)
            return []

        subdomains: list[str] = []
        for line in stdout.decode(errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                host = data.get("host")
                if host and host not in subdomains:
                    subdomains.append(host)
            except json.JSONDecodeError:
                continue
            if len(subdomains) >= max_results:
                break
        return subdomains

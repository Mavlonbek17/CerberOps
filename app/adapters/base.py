"""Abstract base class for scanner adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.models import Severity


@dataclass
class RawFinding:
    """Intermediate finding produced by a scanner adapter before normalization."""

    title: str
    description: str = ""
    severity: Severity = Severity.INFO
    host: str = ""
    port: int | None = None
    protocol: str | None = None
    url: str | None = None
    evidence: str | None = None
    scanner_source: str = ""
    cve_ids: list[str] = field(default_factory=list)
    reference_urls: list[str] = field(default_factory=list)
    remediation: str | None = None


class BaseScanner(ABC):
    """Interface every scanner adapter must implement."""

    name: str = "base"

    @abstractmethod
    async def is_available(self) -> bool:
        """Return True if the scanner binary/service is reachable."""

    @abstractmethod
    async def run(self, target: str, **options: object) -> list[RawFinding]:
        """Execute a scan against the target and return normalized findings."""

    @abstractmethod
    async def get_version(self) -> str | None:
        """Return the scanner version string, or None if unavailable."""

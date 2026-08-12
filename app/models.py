"""SQLModel database models."""

import enum
import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Column, Enum, Field, Relationship, SQLModel

# ── Enums ─────────────────────────────────────────────────────────

class ScanStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScannerType(str, enum.Enum):
    NMAP = "nmap"
    NUCLEI = "nuclei"
    ZAP = "zap"


# ── Helpers ───────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return uuid.uuid4().hex


# ── Models ────────────────────────────────────────────────────────

class ScanJob(SQLModel, table=True):
    __tablename__ = "scan_jobs"

    id: str = Field(default_factory=_new_id, primary_key=True, max_length=32)
    target: str = Field(index=True, max_length=2048)
    status: ScanStatus = Field(
        default=ScanStatus.QUEUED,
        sa_column=Column(Enum(ScanStatus), nullable=False, default=ScanStatus.QUEUED),
    )
    scanners: str = Field(default="nmap,nuclei,zap", max_length=128)
    allow_internal: bool = Field(default=False)
    progress: int = Field(default=0)
    error_message: str | None = Field(default=None, max_length=4096)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    completed_at: datetime | None = Field(default=None)

    findings: list["Finding"] = Relationship(back_populates="scan_job")
    report: Optional["Report"] = Relationship(back_populates="scan_job")


class Finding(SQLModel, table=True):
    __tablename__ = "findings"

    id: str = Field(default_factory=_new_id, primary_key=True, max_length=32)
    scan_job_id: str = Field(foreign_key="scan_jobs.id", index=True, max_length=32)
    fingerprint: str = Field(index=True, max_length=64)

    title: str = Field(max_length=1024)
    description: str = Field(default="")
    severity: Severity = Field(
        sa_column=Column(Enum(Severity), nullable=False, default=Severity.INFO),
    )
    host: str = Field(max_length=2048)
    port: int | None = Field(default=None)
    protocol: str | None = Field(default=None, max_length=32)
    url: str | None = Field(default=None, max_length=4096)
    evidence: str | None = Field(default=None)
    scanner_source: str = Field(max_length=64)
    scanner_sources: str = Field(default="", max_length=256)
    cve_ids: str | None = Field(default=None, max_length=1024)
    reference_urls: str | None = Field(default=None)
    remediation: str | None = Field(default=None)
    is_duplicate: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)

    scan_job: Optional["ScanJob"] = Relationship(back_populates="findings")


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: str = Field(default_factory=_new_id, primary_key=True, max_length=32)
    scan_job_id: str = Field(foreign_key="scan_jobs.id", unique=True, index=True, max_length=32)

    executive_summary: str = Field(default="")
    technical_details: str = Field(default="")
    remediation_plan: str = Field(default="")
    ai_model_used: str = Field(default="", max_length=128)
    generated_at: datetime = Field(default_factory=_utcnow)

    scan_job: Optional["ScanJob"] = Relationship(back_populates="report")

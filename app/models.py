"""SQLModel database models."""

import enum
import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime
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


class AiVerdict(str, enum.Enum):
    UNREVIEWED = "unreviewed"
    CONFIRMED = "confirmed"
    LIKELY_FALSE_POSITIVE = "likely_false_positive"


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
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # ── AI Smart Recon ───────────────────────────────────────────
    smart_recon: bool = Field(default=True)
    recon_summary: str | None = Field(default=None)
    ai_scan_plan: str | None = Field(default=None)

    # ── Labels ────────────────────────────────────────────────────
    tags: str | None = Field(default=None, max_length=512)  # comma-separated

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
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    # ── CVSS ──────────────────────────────────────────────────────
    cvss_score: float | None = Field(default=None)
    cvss_vector: str | None = Field(default=None, max_length=256)

    # ── MITRE ATT&CK / Compliance / Baseline ──────────────────────
    mitre_techniques: str | None = Field(default=None, max_length=256)  # comma-separated ATT&CK IDs e.g. "T1190,T1078"
    owasp_category: str | None = Field(default=None, max_length=128)
    is_new: bool = Field(default=True)  # baseline: True if not seen in previous completed scan of same target

    # ── AI False Positive Triage ─────────────────────────────────
    ai_verdict: AiVerdict = Field(
        default=AiVerdict.UNREVIEWED,
        sa_column=Column(Enum(AiVerdict), nullable=False, default=AiVerdict.UNREVIEWED),
    )
    ai_triage_notes: str | None = Field(default=None)

    # ── Autonomous PoC Generator ──────────────────────────────────
    poc_code: str | None = Field(default=None)
    poc_explanation: str | None = Field(default=None)
    poc_model_used: str | None = Field(default=None, max_length=128)
    poc_generated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    scan_job: Optional["ScanJob"] = Relationship(back_populates="findings")


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: str = Field(default_factory=_new_id, primary_key=True, max_length=32)
    scan_job_id: str = Field(foreign_key="scan_jobs.id", unique=True, index=True, max_length=32)

    executive_summary: str = Field(default="")
    technical_details: str = Field(default="")
    remediation_plan: str = Field(default="")
    ai_model_used: str = Field(default="", max_length=128)
    generated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    threat_narrative: str | None = Field(default=None)

    scan_job: Optional["ScanJob"] = Relationship(back_populates="report")


class ScheduledScan(SQLModel, table=True):
    __tablename__ = "scheduled_scans"

    id: str = Field(default_factory=_new_id, primary_key=True, max_length=32)
    target: str = Field(index=True, max_length=2048)
    scanners: str = Field(default="nmap,nuclei", max_length=128)
    tags: str | None = Field(default=None, max_length=512)
    schedule: str = Field(default="daily", max_length=32)  # daily, weekly, monthly
    enabled: bool = Field(default=True)
    allow_internal: bool = Field(default=False)
    smart_recon: bool = Field(default=True)
    last_run_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    next_run_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class NotificationConfig(SQLModel, table=True):
    __tablename__ = "notification_configs"

    id: str = Field(default_factory=_new_id, primary_key=True, max_length=32)
    name: str = Field(max_length=128)
    type: str = Field(max_length=32)  # "slack", "webhook", "email"
    config: str = Field(default="{}", max_length=4096)  # JSON
    events: str = Field(default="scan_complete,critical_found", max_length=256)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Asset(SQLModel, table=True):
    __tablename__ = "assets"
    id: str = Field(default_factory=_new_id, primary_key=True, max_length=32)
    target: str = Field(index=True, unique=True, max_length=2048)
    tech_stack: str | None = Field(default=None, max_length=1024)  # comma-separated
    open_ports: str | None = Field(default=None, max_length=512)  # comma-separated port numbers seen historically
    first_seen: datetime = Field(default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
    last_scanned: datetime = Field(default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
    scan_count: int = Field(default=0)


class Subdomain(SQLModel, table=True):
    __tablename__ = "subdomains"
    id: str = Field(default_factory=_new_id, primary_key=True, max_length=32)
    asset_id: str = Field(foreign_key="assets.id", index=True, max_length=32)
    subdomain: str = Field(index=True, max_length=512)
    ip_address: str | None = Field(default=None, max_length=64)
    is_alive: bool = Field(default=False)
    status_code: int | None = Field(default=None)
    title: str | None = Field(default=None, max_length=512)
    tech: str | None = Field(default=None, max_length=512)  # comma-separated
    discovered_at: datetime = Field(default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))


class CveEnrichment(SQLModel, table=True):
    __tablename__ = "cve_enrichment"
    cve_id: str = Field(primary_key=True, max_length=32)
    description: str = Field(default="")
    cvss_score: float | None = Field(default=None)
    cvss_vector: str | None = Field(default=None, max_length=256)
    epss_score: float | None = Field(default=None)
    published_date: str | None = Field(default=None, max_length=32)
    reference_urls: str | None = Field(default=None)  # newline-separated
    fetched_at: datetime = Field(default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))

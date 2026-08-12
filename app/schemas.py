"""Pydantic request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import AiVerdict, ScanStatus, Severity  # noqa: F401

# ── Requests ──────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    """Request body for POST /api/v1/scan."""

    target: str = Field(
        ...,
        description="Target URL or IP address to scan",
        examples=["https://example.com", "192.168.1.1"],
    )
    scanners: list[str] = Field(
        default=["nmap", "nuclei", "zap"],
        description="Scanners to run",
    )
    allow_internal: bool = Field(
        default=False,
        description="Allow scanning RFC1918 / loopback addresses (use for testing only)",
    )
    smart_recon: bool = Field(
        default=True,
        description="Fingerprint the target first and let local AI narrow scanner "
        "templates/ports before running the full scan (faster, less noisy)",
    )
    tags: list[str] = Field(default=[], description="Optional labels for this scan")


# ── Responses ─────────────────────────────────────────────────────

class ScanCreated(BaseModel):
    """Response for 202 Accepted after starting a scan."""

    job_id: str
    status: ScanStatus
    message: str = "Scan queued successfully"


class FindingOut(BaseModel):
    id: str
    title: str
    description: str
    severity: Severity
    host: str
    port: int | None = None
    protocol: str | None = None
    url: str | None = None
    evidence: str | None = None
    scanner_source: str
    scanner_sources: list[str] = []
    cve_ids: list[str] = []
    reference_urls: list[str] = []
    remediation: str | None = None
    is_duplicate: bool = False
    created_at: datetime
    ai_verdict: AiVerdict = AiVerdict.UNREVIEWED
    ai_triage_notes: str | None = None
    has_poc: bool = False
    cvss_score: float | None = None
    cvss_vector: str | None = None


class ScanDetail(BaseModel):
    """Full scan job details with findings."""

    id: str
    target: str
    status: ScanStatus
    scanners: list[str]
    progress: int
    error_message: str | None = None
    findings_count: int = 0
    severity_counts: dict[str, int] = {}
    findings: list[FindingOut] = []
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    smart_recon: bool = True
    recon_summary: str | None = None
    ai_scan_plan: str | None = None
    tags: list[str] = []


class ScanSummary(BaseModel):
    """Lightweight scan info for list endpoints."""

    id: str
    target: str
    status: ScanStatus
    scanners: list[str]
    findings_count: int = 0
    created_at: datetime
    tags: list[str] = []


class ReportOut(BaseModel):
    """AI-generated remediation report."""

    id: str
    scan_job_id: str
    executive_summary: str
    technical_details: str
    remediation_plan: str
    ai_model_used: str
    generated_at: datetime


class HealthCheck(BaseModel):
    status: str = "healthy"
    version: str
    scanners: dict[str, bool] = {}
    ollama_available: bool = False
    database: bool = False


class PocOut(BaseModel):
    """Autonomous proof-of-concept verification script for a finding."""

    finding_id: str
    poc_code: str
    poc_explanation: str
    ai_model_used: str
    generated_at: datetime


class ChatMessageIn(BaseModel):
    role: str = Field(description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    """Request body for POST /api/v1/scan/{job_id}/chat."""

    message: str = Field(..., description="The user's question about this scan")
    history: list[ChatMessageIn] = Field(
        default=[], description="Prior turns in this conversation, oldest first"
    )


class ChatResponse(BaseModel):
    response: str
    ai_model_used: str


class SetupResponse(BaseModel):
    api_key: str
    message: str = "Setup complete. Save this API key — it will not be shown again."


class ErrorResponse(BaseModel):
    detail: str


# ── Scheduler ─────────────────────────────────────────────────────

class ScheduledScanCreate(BaseModel):
    target: str
    scanners: list[str] = ["nmap", "nuclei"]
    tags: list[str] = []
    schedule: str = "daily"
    enabled: bool = True
    allow_internal: bool = False
    smart_recon: bool = True


class ScheduledScanOut(BaseModel):
    id: str
    target: str
    scanners: list[str]
    tags: list[str]
    schedule: str
    enabled: bool
    allow_internal: bool
    smart_recon: bool
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    created_at: datetime


# ── Notifications ─────────────────────────────────────────────────

class NotificationConfigCreate(BaseModel):
    name: str
    type: str  # slack, webhook, email
    config: dict = {}
    events: list[str] = ["scan_complete", "critical_found"]
    enabled: bool = True


class NotificationConfigOut(BaseModel):
    id: str
    name: str
    type: str
    config: dict
    events: list[str]
    enabled: bool
    created_at: datetime

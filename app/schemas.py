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
    mitre_techniques: list[str] = []
    owasp_category: str | None = None
    is_new: bool = True


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
    threat_narrative: str | None = None


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


# ── Asset Intelligence / MITRE / Compliance / CVE Enrichment ──────

class SubdomainOut(BaseModel):
    subdomain: str
    ip_address: str | None = None
    is_alive: bool
    status_code: int | None = None
    title: str | None = None
    tech: list[str] = []
    discovered_at: datetime


class AssetSummary(BaseModel):
    id: str
    target: str
    tech_stack: list[str] = []
    subdomain_count: int = 0
    scan_count: int = 0
    first_seen: datetime
    last_scanned: datetime


class AssetDetail(BaseModel):
    id: str
    target: str
    tech_stack: list[str] = []
    open_ports: list[str] = []
    subdomains: list[SubdomainOut] = []
    scan_count: int = 0
    first_seen: datetime
    last_scanned: datetime


class BaselineOut(BaseModel):
    has_baseline: bool
    previous_scan_id: str | None = None
    new_findings: list[FindingOut] = []
    resolved_findings: list[dict] = []  # {title, severity, host}
    unchanged_count: int = 0


class MitreTechnique(BaseModel):
    technique_id: str
    technique_name: str
    tactic: str
    finding_ids: list[str] = []
    finding_count: int = 0


class MitreOut(BaseModel):
    techniques: list[MitreTechnique] = []


class ComplianceItem(BaseModel):
    framework_id: str
    description: str
    finding_count: int = 0
    max_severity: str = "info"


class ComplianceOut(BaseModel):
    owasp_top10: list[ComplianceItem] = []
    pci_dss: list[ComplianceItem] = []
    nist_800_53: list[ComplianceItem] = []
    iso_27001: list[ComplianceItem] = []


class CveEnrichmentOut(BaseModel):
    cve_id: str
    description: str
    cvss_score: float | None = None
    cvss_vector: str | None = None
    epss_score: float | None = None
    published_date: str | None = None
    reference_urls: list[str] = []


class VerifyResult(BaseModel):
    finding_id: str
    verified: bool
    method: str
    details: str
    verified_at: datetime

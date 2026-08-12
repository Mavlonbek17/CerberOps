"""Tests for data models and schemas."""

from app.models import ScanJob, ScanStatus, Severity, _new_id
from app.schemas import ScanRequest


class TestModels:
    def test_new_id_uniqueness(self):
        ids = {_new_id() for _ in range(100)}
        assert len(ids) == 100

    def test_scan_job_defaults(self):
        job = ScanJob(target="https://example.com")
        assert job.status == ScanStatus.QUEUED
        assert job.progress == 0
        assert job.scanners == "nmap,nuclei,zap"
        assert job.allow_internal is False
        assert job.id  # has an ID

    def test_finding_severity_values(self):
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"

    def test_scan_status_values(self):
        assert ScanStatus.QUEUED.value == "queued"
        assert ScanStatus.RUNNING.value == "running"
        assert ScanStatus.COMPLETED.value == "completed"
        assert ScanStatus.FAILED.value == "failed"


class TestSchemas:
    def test_scan_request_defaults(self):
        req = ScanRequest(target="https://example.com")
        assert req.scanners == ["nmap", "nuclei", "zap"]
        assert req.allow_internal is False

    def test_scan_request_custom_scanners(self):
        req = ScanRequest(target="https://example.com", scanners=["nmap"])
        assert req.scanners == ["nmap"]

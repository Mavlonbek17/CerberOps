"""Tests for scope validation."""

import pytest

from app.core.exceptions import ScopeValidationError
from app.services.scope_validator import validate_target


class TestScopeValidator:
    def test_valid_public_url(self):
        result = validate_target("https://example.com")
        assert result == "https://example.com"

    def test_adds_scheme_to_bare_domain(self):
        result = validate_target("example.com")
        assert result == "https://example.com"

    def test_preserves_existing_scheme(self):
        result = validate_target("http://example.com")
        assert result == "http://example.com"

    def test_rejects_empty_target(self):
        with pytest.raises(ScopeValidationError, match="cannot be empty"):
            validate_target("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ScopeValidationError, match="cannot be empty"):
            validate_target("   ")

    def test_rejects_loopback_ipv4(self):
        with pytest.raises(ScopeValidationError, match="private/internal"):
            validate_target("127.0.0.1")

    def test_rejects_rfc1918_10(self):
        with pytest.raises(ScopeValidationError, match="private/internal"):
            validate_target("10.0.0.1")

    def test_rejects_rfc1918_172(self):
        with pytest.raises(ScopeValidationError, match="private/internal"):
            validate_target("172.16.0.1")

    def test_rejects_rfc1918_192(self):
        with pytest.raises(ScopeValidationError, match="private/internal"):
            validate_target("192.168.1.1")

    def test_allows_internal_when_flagged(self):
        result = validate_target("192.168.1.1", allow_internal=True)
        assert result == "192.168.1.1"

    def test_rejects_loopback_in_url(self):
        with pytest.raises(ScopeValidationError, match="private/internal"):
            validate_target("http://127.0.0.1:8080")

    def test_allows_internal_url_when_flagged(self):
        result = validate_target("http://192.168.1.1:8080", allow_internal=True)
        assert result == "http://192.168.1.1:8080"

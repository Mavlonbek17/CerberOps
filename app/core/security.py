"""API key generation and validation."""

import secrets
from pathlib import Path

from app.config import settings

_KEY_LENGTH = 48
_KEY_FILE = Path(".cerberops_api_key")


def generate_api_key() -> str:
    """Generate a cryptographically secure API key."""
    return f"co_{secrets.token_urlsafe(_KEY_LENGTH)}"


def get_or_create_api_key() -> str:
    """Return the configured API key, generating one on first run."""
    if settings.api_key:
        return settings.api_key

    if _KEY_FILE.exists():
        stored = _KEY_FILE.read_text().strip()
        if stored:
            return stored

    key = generate_api_key()
    _KEY_FILE.write_text(key + "\n")
    _KEY_FILE.chmod(0o600)
    return key


def verify_api_key(provided: str) -> bool:
    """Constant-time comparison of the provided key against the stored key."""
    expected = get_or_create_api_key()
    return secrets.compare_digest(provided, expected)

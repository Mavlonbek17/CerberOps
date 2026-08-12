"""Custom exception hierarchy for CerberOps."""


class CerberOpsError(Exception):
    """Base exception for all CerberOps errors."""


class ScopeValidationError(CerberOpsError):
    """Target is outside the allowed scan scope."""


class ScannerError(CerberOpsError):
    """A scanner failed to execute or returned an error."""

    def __init__(self, scanner: str, message: str):
        self.scanner = scanner
        super().__init__(f"[{scanner}] {message}")


class ScannerTimeoutError(ScannerError):
    """A scanner exceeded its time limit."""


class ScannerNotFoundError(ScannerError):
    """A required scanner binary is not installed."""


class OllamaError(CerberOpsError):
    """Failed to communicate with the Ollama API."""


class AuthenticationError(CerberOpsError):
    """Invalid or missing API key."""

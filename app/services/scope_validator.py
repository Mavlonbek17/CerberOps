"""Strict scope validation for scan targets."""

import ipaddress
import re
import socket
from urllib.parse import urlparse

from app.config import settings
from app.core.exceptions import ScopeValidationError

# RFC1918 + loopback + link-local networks
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

_DOMAIN_RE = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*\.[A-Za-z]{2,}$"
)


def _is_private_ip(ip_str: str) -> bool:
    """Check whether an IP falls within a private/reserved range."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return any(addr in net for net in _PRIVATE_NETWORKS)


def _resolve_host(hostname: str) -> str | None:
    """Resolve a hostname to its first IP address."""
    try:
        return socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)[0][4][0]
    except (socket.gaierror, IndexError):
        return None


def _extract_host(target: str) -> str:
    """Extract the hostname or IP from a target string."""
    if "://" in target:
        parsed = urlparse(target)
        host = parsed.hostname or ""
    else:
        host = target.split("/")[0].split(":")[0]
    return host.strip().lower()


def validate_target(target: str, *, allow_internal: bool = False) -> str:
    """Validate and normalize a scan target.

    Returns the cleaned target string or raises ScopeValidationError.
    """
    if not target or not target.strip():
        raise ScopeValidationError("Target cannot be empty")

    target = target.strip()
    host = _extract_host(target)

    if not host:
        raise ScopeValidationError(f"Could not extract host from target: {target}")

    # Check if it's a raw IP
    try:
        ip = ipaddress.ip_address(host)
        ip_str = str(ip)
    except ValueError:
        # It's a hostname — validate format and resolve
        if not _DOMAIN_RE.match(host):
            raise ScopeValidationError(
                f"Invalid hostname format: {host}. "
                "Must be a valid domain (e.g., example.com) or IP address."
            ) from None
        ip_str = _resolve_host(host)
        if not ip_str:
            raise ScopeValidationError(
                f"Could not resolve hostname: {host}"
            ) from None

    # Block private/internal targets unless explicitly allowed
    if _is_private_ip(ip_str) and not (allow_internal or settings.allow_internal_targets):
        raise ScopeValidationError(
            f"Target {host} ({ip_str}) is a private/internal address. "
            "Set allow_internal=true to scan internal networks (testing only)."
        )

    # Ensure URL has a scheme for web scanners
    if "://" not in target:
        try:
            ipaddress.ip_address(target)
            return target
        except ValueError:
            pass
        return f"https://{target}"

    return target

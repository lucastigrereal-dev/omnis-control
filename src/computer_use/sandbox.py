"""SecuritySandbox — safety guardrails for Computer Use agents."""
from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


BLOCKED_DOMAINS = [
    "banco", "bank", "bradesco", "itau", "santander", "nubank",
    "paypal", "stripe", "mercadopago", "picpay",
    "gmail.com", "outlook.com", "hotmail.com", "yahoo.com",
    "gov.br", "receita.fazenda", "caixa.gov",
]

BLOCKED_ACTIONS = [
    "delete", "remove", "unlink", "drop", "truncate",
    "rm -rf", "format", "wipe",
]

ALLOWED_PATHS = [
    os.path.normpath(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control"))),
    os.path.normpath(os.getenv("PUBLISHER_OS_DIR", os.path.expanduser("~/publisher-os"))),
    os.path.normpath(os.getenv("DAILY_PROPHET_DIR", os.path.expanduser("~/daily-prophet-hotels"))),
    "/tmp",
    "./",
    "exports/",
    "output/",
]

_ALLOWED_SCHEMES = frozenset({"http", "https"})
_BLOCKED_SCHEMES = frozenset({
    "file", "data", "javascript", "about", "chrome", "vbscript", "blob", "ftp",
})
_LOOPBACK_HOSTS = frozenset({"localhost", "0.0.0.0", "127.0.0.1", "::1", "ip6-localhost"})
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_private_ip(hostname: str) -> bool:
    try:
        addr = ipaddress.ip_address(hostname)
        return any(addr in net for net in _PRIVATE_NETWORKS)
    except ValueError:
        return False


@dataclass
class SandboxViolation(Exception):
    rule: str
    detail: str
    timestamp: str = field(default_factory=_now_iso)

    def __str__(self):
        return f"[SANDBOX VIOLATION] {self.rule}: {self.detail}"

    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


class SecuritySandbox:
    """Validates all Computer Use actions before execution."""

    def __init__(self, strict: bool = True):
        self.strict = strict
        self.violations: list[SandboxViolation] = []
        self.allowed_actions: list[dict] = []

    def validate_url(self, url: str) -> bool:
        """Block dangerous URLs: bad schemes, loopback, private IPs, blocked domains."""
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        if scheme not in _ALLOWED_SCHEMES:
            v = SandboxViolation(
                rule="blocked_scheme",
                detail=f"URL scheme '{scheme}' is not allowed (only http/https)",
            )
            self.violations.append(v)
            if self.strict:
                raise v
            return False

        host = parsed.hostname or ""
        if host.lower() in _LOOPBACK_HOSTS:
            v = SandboxViolation(
                rule="blocked_loopback",
                detail=f"URL host '{host}' is a loopback address",
            )
            self.violations.append(v)
            if self.strict:
                raise v
            return False

        if _is_private_ip(host):
            v = SandboxViolation(
                rule="blocked_private_ip",
                detail=f"URL host '{host}' is a private/internal IP address",
            )
            self.violations.append(v)
            if self.strict:
                raise v
            return False

        url_lower = url.lower()
        for domain in BLOCKED_DOMAINS:
            if domain in url_lower:
                v = SandboxViolation(
                    rule="blocked_domain",
                    detail=f"URL '{url}' matches blocked domain pattern '{domain}'",
                )
                self.violations.append(v)
                if self.strict:
                    raise v
                return False

        return True

    def validate_action(self, action: str) -> bool:
        """Block destructive actions."""
        action_lower = action.lower()
        for blocked in BLOCKED_ACTIONS:
            if blocked in action_lower:
                v = SandboxViolation(
                    rule="blocked_action",
                    detail=f"Action '{action}' matches blocked pattern '{blocked}'",
                )
                self.violations.append(v)
                if self.strict:
                    raise v
                return False
        return True

    def validate_path(self, path: str) -> bool:
        """Only allow writes to approved directories."""
        path_abs = path.replace("\\", "/")
        for allowed in ALLOWED_PATHS:
            if path_abs.startswith(allowed.replace("\\", "/")):
                return True
        v = SandboxViolation(
            rule="blocked_path",
            detail=f"Path '{path}' is not in allowed directories",
        )
        self.violations.append(v)
        if self.strict:
            raise v
        return False

    def preflight(self, url: str = "", action: str = "", path: str = "") -> bool:
        """Run all validations before executing a computer use action."""
        checks = []
        if url:
            checks.append(self.validate_url(url))
        if action:
            checks.append(self.validate_action(action))
        if path:
            checks.append(self.validate_path(path))
        return all(checks)

    def record_allowed(self, action: str, detail: str = "") -> None:
        self.allowed_actions.append({
            "action": action,
            "detail": detail,
            "timestamp": _now_iso(),
        })

    @property
    def is_clean(self) -> bool:
        return len(self.violations) == 0

    @property
    def summary(self) -> str:
        return (
            f"Sandbox: {len(self.allowed_actions)} allowed, "
            f"{len(self.violations)} violations"
        )

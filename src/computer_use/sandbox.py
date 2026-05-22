"""SecuritySandbox — safety guardrails for Computer Use agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


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
    "C:\\Users\\lucas\\omnis-control",
    "C:\\Users\\lucas\\publisher-os",
    "C:\\Users\\lucas\\daily-prophet-hotels",
    "/tmp",
    "./",
    "exports/",
    "output/",
]


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
        """Block banking, email, government domains."""
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

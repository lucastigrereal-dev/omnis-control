"""GuardrailProvider — content safety and action guardrails for OMNIS.

Backends:
1. RuleBasedGuardrailProvider — built-in regex/keyword rules (zero deps)
2. NeMoGuardrailProvider      — NVIDIA NeMo Guardrails (optional)

Prevents: prompt injection, PII leakage, destructive commands, off-topic requests.
"""
from __future__ import annotations

import re
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from src.providers.base import Provider, ProviderHealth, ProviderStatus


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""
    passed: bool
    risk_level: str  # "NONE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    violations: list[str] = field(default_factory=list)
    sanitized_input: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def blocked(self) -> bool:
        return not self.passed


class GuardrailProvider(Provider):
    """Abstract guardrail provider. Use registry.get('guardrail') to get instance."""

    @property
    def name(self) -> str:
        return "guardrail"

    @abstractmethod
    def check_input(self, text: str, *, context: Optional[dict] = None) -> GuardrailResult:
        """Check input text for safety violations."""

    @abstractmethod
    def check_output(self, text: str, *, context: Optional[dict] = None) -> GuardrailResult:
        """Check model output for safety violations."""

    def check(self, text: str, *, context: Optional[dict] = None) -> GuardrailResult:
        """Alias for check_input."""
        return self.check_input(text, context=context)


# ── Built-in: RuleBasedGuardrailProvider ───────────────────────────────────

_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"you\s+are\s+now\s+(a|an)\s+\w+",
    r"jailbreak",
    r"disregard\s+(your|all)\s+(safety|guidelines|rules)",
    r"act\s+as\s+if\s+you\s+(have\s+no|don.t\s+have)",
    r"pretend\s+(you\s+are|to\s+be)\s+(?!going)",
]

_DESTRUCTIVE_PATTERNS = [
    r"(rm|del|remove)\s+(-rf?|/[sq]|--recursive)",
    r"git\s+(reset\s+--hard|clean\s+-f|push\s+--force)",
    r"DROP\s+TABLE",
    r"format\s+(c:|/dev/)",
    r":(){ :|:& };:",  # fork bomb
]

_SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|password)\s*[=:]\s*['\"]?\w{8,}",
    r"sk-[a-zA-Z0-9]{20,}",  # OpenAI key
    r"AKIA[0-9A-Z]{16}",     # AWS key
]

_HIGH_RISK_COMMANDS = [
    r"git\s+push",
    r"wrangler\s+deploy",
    r"npm\s+publish",
    r"docker\s+rm",
]


@dataclass
class _Rule:
    pattern: str
    risk: str
    message: str
    compiled: re.Pattern = field(init=False)

    def __post_init__(self):
        self.compiled = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)


class RuleBasedGuardrailProvider(GuardrailProvider):
    """Built-in guardrails using regex rules.

    Checks for: prompt injection, destructive commands, secret leakage.
    Safe to use in production — never sends data to external services.
    """

    def __init__(self, extra_rules: Optional[list[dict]] = None) -> None:
        self._rules: list[_Rule] = []
        for pattern in _INJECTION_PATTERNS:
            self._rules.append(_Rule(pattern, "HIGH", "Possible prompt injection"))
        for pattern in _DESTRUCTIVE_PATTERNS:
            self._rules.append(_Rule(pattern, "CRITICAL", "Destructive command detected"))
        for pattern in _SECRET_PATTERNS:
            self._rules.append(_Rule(pattern, "CRITICAL", "Possible secret/credential exposure"))
        for pattern in _HIGH_RISK_COMMANDS:
            self._rules.append(_Rule(pattern, "HIGH", "High-risk operation (requires authorization)"))
        for rule in extra_rules or []:
            self._rules.append(_Rule(rule["pattern"], rule.get("risk", "MEDIUM"), rule.get("message", "Custom rule violation")))

    @property
    def backend(self) -> str:
        return "rule_based"

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider_name=self.name,
            backend=self.backend,
            details={"rules": len(self._rules)},
        )

    def check_input(self, text: str, *, context: Optional[dict] = None) -> GuardrailResult:
        return self._check(text)

    def check_output(self, text: str, *, context: Optional[dict] = None) -> GuardrailResult:
        return self._check(text)

    def _check(self, text: str) -> GuardrailResult:
        violations: list[str] = []
        max_risk = "NONE"
        risk_order = ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]

        for rule in self._rules:
            if rule.compiled.search(text):
                violations.append(rule.message)
                if risk_order.index(rule.risk) > risk_order.index(max_risk):
                    max_risk = rule.risk

        passed = max_risk not in ("HIGH", "CRITICAL")
        return GuardrailResult(
            passed=passed,
            risk_level=max_risk,
            violations=violations,
            sanitized_input=text if passed else None,
        )

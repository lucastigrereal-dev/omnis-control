"""W169 — KRATOS Bridge Permission Gate: controls which OMNIS modules can send cockpit payloads."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .models import KratosPayload, PayloadType, _new_id, _now_iso


class Permission(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    AUDIT_ONLY = "AUDIT_ONLY"   # log but don't deliver


# ---------------------------------------------------------------------------
# Rule
# ---------------------------------------------------------------------------

@dataclass
class PermissionRule:
    rule_id: str = field(default_factory=lambda: _new_id("prule"))
    source_module: str = "*"               # glob-style: "*" = any
    payload_types: list[str] = field(default_factory=list)  # empty = any type
    permission: Permission = Permission.ALLOW
    reason: str = ""

    def matches(self, payload: KratosPayload) -> bool:
        module_match = self.source_module == "*" or payload.source_module == self.source_module
        type_match = not self.payload_types or payload.payload_type.value in self.payload_types
        return module_match and type_match

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "source_module": self.source_module,
            "payload_types": self.payload_types,
            "permission": self.permission.value,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PermissionRule":
        return cls(
            rule_id=data.get("rule_id", _new_id("prule")),
            source_module=data.get("source_module", "*"),
            payload_types=data.get("payload_types", []),
            permission=Permission(data.get("permission", "ALLOW")),
            reason=data.get("reason", ""),
        )

    @classmethod
    def allow(cls, module: str, payload_types: Optional[list[str]] = None) -> "PermissionRule":
        return cls(source_module=module, payload_types=payload_types or [], permission=Permission.ALLOW)

    @classmethod
    def deny(cls, module: str, payload_types: Optional[list[str]] = None, reason: str = "") -> "PermissionRule":
        return cls(source_module=module, payload_types=payload_types or [], permission=Permission.DENY, reason=reason)

    @classmethod
    def audit_only(cls, module: str) -> "PermissionRule":
        return cls(source_module=module, permission=Permission.AUDIT_ONLY)


# ---------------------------------------------------------------------------
# Gate result
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    result_id: str = field(default_factory=lambda: _new_id("gr"))
    payload_id: str = ""
    permission: Permission = Permission.ALLOW
    matched_rule_id: str = ""
    reason: str = ""
    checked_at: str = field(default_factory=_now_iso)

    @property
    def allowed(self) -> bool:
        return self.permission == Permission.ALLOW

    @property
    def audit_only(self) -> bool:
        return self.permission == Permission.AUDIT_ONLY

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "payload_id": self.payload_id,
            "permission": self.permission.value,
            "matched_rule_id": self.matched_rule_id,
            "reason": self.reason,
            "allowed": self.allowed,
            "checked_at": self.checked_at,
        }


# ---------------------------------------------------------------------------
# Permission gate
# ---------------------------------------------------------------------------

_DEFAULT_RULES: list[PermissionRule] = [
    # KRATOS module itself is blocked from sending ALERT (avoid loops)
    PermissionRule.deny("kratos", payload_types=["ALERT"], reason="anti-loop"),
    # Everything else allowed by default
    PermissionRule.allow("*"),
]


class KratosPermissionGate:
    """First-match rule engine controlling cockpit payload delivery."""

    def __init__(
        self,
        rules: Optional[list[PermissionRule]] = None,
        default_permission: Permission = Permission.ALLOW,
    ) -> None:
        self._rules = rules if rules is not None else list(_DEFAULT_RULES)
        self._default = default_permission
        self._audit_log: list[GateResult] = []

    # ------------------------------------------------------------------
    def check(self, payload: KratosPayload) -> GateResult:
        result = GateResult(payload_id=payload.payload_id)
        for rule in self._rules:
            if rule.matches(payload):
                result.permission = rule.permission
                result.matched_rule_id = rule.rule_id
                result.reason = rule.reason
                break
        else:
            result.permission = self._default
            result.reason = "default"
        self._audit_log.append(result)
        return result

    def check_many(self, payloads: list[KratosPayload]) -> list[GateResult]:
        return [self.check(p) for p in payloads]

    # ------------------------------------------------------------------
    def add_rule(self, rule: PermissionRule, position: int = 0) -> None:
        """Insert rule at position (0 = highest priority)."""
        self._rules.insert(position, rule)

    def remove_rule(self, rule_id: str) -> bool:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.rule_id != rule_id]
        return len(self._rules) < before

    def rules(self) -> list[PermissionRule]:
        return list(self._rules)

    # ------------------------------------------------------------------
    def audit_log(self) -> list[GateResult]:
        return list(self._audit_log)

    def stats(self) -> dict:
        total = len(self._audit_log)
        allowed = sum(1 for r in self._audit_log if r.allowed)
        denied = sum(1 for r in self._audit_log if r.permission == Permission.DENY)
        audit_only = sum(1 for r in self._audit_log if r.audit_only)
        return {
            "total_checks": total,
            "allowed": allowed,
            "denied": denied,
            "audit_only": audit_only,
            "rules": len(self._rules),
        }

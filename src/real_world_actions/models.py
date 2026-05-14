"""P27 Real World Actions — core models."""
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# ── Risk levels ───────────────────────────────────────────────────
RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_CRITICAL = "critical"
RISK_LEVELS = [RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL]

# ── Action types ──────────────────────────────────────────────────
ACTION_READ = "read"
ACTION_WRITE = "write"
ACTION_SEND = "send"
ACTION_DEPLOY = "deploy"
ACTION_FINANCIAL = "financial"
ACTION_DELETE = "delete"
ACTION_TYPES = [ACTION_READ, ACTION_WRITE, ACTION_SEND, ACTION_DEPLOY, ACTION_FINANCIAL, ACTION_DELETE]

# Action type → default risk level
ACTION_TYPE_RISK_MAP = {
    ACTION_READ: RISK_LOW,
    ACTION_WRITE: RISK_MEDIUM,
    ACTION_SEND: RISK_HIGH,
    ACTION_DEPLOY: RISK_CRITICAL,
    ACTION_FINANCIAL: RISK_CRITICAL,
    ACTION_DELETE: RISK_CRITICAL,
}

# Risks that require approval
APPROVAL_REQUIRED_RISKS = {RISK_HIGH, RISK_CRITICAL}

# ── Result statuses ───────────────────────────────────────────────
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_DRY_RUN = "dry_run"
STATUS_BLOCKED = "blocked"
STATUS_TIMEOUT = "timeout"
STATUS_PARTIAL = "partial"
STATUS_PENDING_APPROVAL = "pending_approval"
STATUS_DENIED = "denied"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


# ── Rate / Retry configs ──────────────────────────────────────────

@dataclass
class RateLimit:
    max_per_hour: int = 60
    max_per_day: int = 1000
    concurrent_max: int = 3

    def to_dict(self) -> dict:
        return {"max_per_hour": self.max_per_hour, "max_per_day": self.max_per_day, "concurrent_max": self.concurrent_max}

    @classmethod
    def from_dict(cls, d: dict) -> "RateLimit":
        return cls(max_per_hour=d.get("max_per_hour", 60), max_per_day=d.get("max_per_day", 1000), concurrent_max=d.get("concurrent_max", 3))


@dataclass
class RetryPolicy:
    max_retries: int = 3
    backoff_seconds: float = 2.0
    backoff_multiplier: float = 2.0

    def to_dict(self) -> dict:
        return {"max_retries": self.max_retries, "backoff_seconds": self.backoff_seconds, "backoff_multiplier": self.backoff_multiplier}

    @classmethod
    def from_dict(cls, d: dict) -> "RetryPolicy":
        return cls(max_retries=d.get("max_retries", 3), backoff_seconds=d.get("backoff_seconds", 2.0), backoff_multiplier=d.get("backoff_multiplier", 2.0))


# ── ActionDefinition ──────────────────────────────────────────────

@dataclass
class ActionDefinition:
    action_id: str
    name: str
    provider: str
    action_type: str = ACTION_READ
    risk_level: str = RISK_LOW
    requires_approval: bool = False
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)
    rate_limit: RateLimit = field(default_factory=RateLimit)
    timeout_seconds: int = 30
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    enabled: bool = True
    description: str = ""
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, name: str, provider: str, action_type: str = ACTION_READ,
            risk_level: Optional[str] = None, description: str = "",
            timeout_seconds: int = 30, max_retries: int = 3,
            input_schema: Optional[dict] = None, output_schema: Optional[dict] = None) -> "ActionDefinition":
        if risk_level is None:
            risk_level = ACTION_TYPE_RISK_MAP.get(action_type, RISK_LOW)
        return cls(
            action_id=_short_id("rwa"),
            name=name,
            provider=provider,
            action_type=action_type,
            risk_level=risk_level,
            requires_approval=risk_level in APPROVAL_REQUIRED_RISKS,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            timeout_seconds=timeout_seconds,
            retry_policy=RetryPolicy(max_retries=max_retries),
            description=description,
        )

    def to_dict(self) -> dict:
        return {
            "action_id": self.action_id, "name": self.name, "provider": self.provider,
            "action_type": self.action_type, "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
            "input_schema": self.input_schema, "output_schema": self.output_schema,
            "rate_limit": self.rate_limit.to_dict(),
            "timeout_seconds": self.timeout_seconds,
            "retry_policy": self.retry_policy.to_dict(),
            "enabled": self.enabled, "description": self.description, "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ActionDefinition":
        rl_data = d.get("rate_limit", {})
        rp_data = d.get("retry_policy", {})
        return cls(
            action_id=d.get("action_id", ""), name=d.get("name", ""), provider=d.get("provider", ""),
            action_type=d.get("action_type", ACTION_READ), risk_level=d.get("risk_level", RISK_LOW),
            requires_approval=d.get("requires_approval", False),
            input_schema=d.get("input_schema", {}), output_schema=d.get("output_schema", {}),
            rate_limit=RateLimit.from_dict(rl_data) if isinstance(rl_data, dict) else RateLimit(),
            timeout_seconds=d.get("timeout_seconds", 30),
            retry_policy=RetryPolicy.from_dict(rp_data) if isinstance(rp_data, dict) else RetryPolicy(),
            enabled=d.get("enabled", True), description=d.get("description", ""),
            created_at=d.get("created_at", ""),
        )

    @property
    def is_critical(self) -> bool:
        return self.risk_level == RISK_CRITICAL

    @property
    def is_risky(self) -> bool:
        return self.risk_level in APPROVAL_REQUIRED_RISKS


# ── ActionRequest ─────────────────────────────────────────────────

@dataclass
class ActionRequest:
    request_id: str
    action_id: str
    params: dict = field(default_factory=dict)
    dry_run: bool = True
    mission_id: str = ""
    step_id: str = ""
    approved_by: str = ""
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, action_id: str, params: Optional[dict] = None,
            dry_run: bool = True, mission_id: str = "", step_id: str = "") -> "ActionRequest":
        return cls(
            request_id=_short_id("rwq"), action_id=action_id,
            params=params or {}, dry_run=dry_run,
            mission_id=mission_id, step_id=step_id,
        )

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id, "action_id": self.action_id,
            "params": self.params, "dry_run": self.dry_run,
            "mission_id": self.mission_id, "step_id": self.step_id,
            "approved_by": self.approved_by, "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ActionRequest":
        return cls(
            request_id=d.get("request_id", ""), action_id=d.get("action_id", ""),
            params=d.get("params", {}), dry_run=d.get("dry_run", True),
            mission_id=d.get("mission_id", ""), step_id=d.get("step_id", ""),
            approved_by=d.get("approved_by", ""), created_at=d.get("created_at", ""),
        )


# ── ActionResult ──────────────────────────────────────────────────

@dataclass
class ActionResult:
    result_id: str
    request_id: str
    status: str = STATUS_DRY_RUN
    output: dict = field(default_factory=dict)
    error: str = ""
    audit_event_id: str = ""
    latency_ms: int = 0
    retry_count: int = 0
    executed_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, request_id: str, status: str = STATUS_DRY_RUN,
            output: Optional[dict] = None, error: str = "",
            latency_ms: int = 0, retry_count: int = 0) -> "ActionResult":
        return cls(
            result_id=_short_id("rwr"), request_id=request_id,
            status=status, output=output or {}, error=error,
            latency_ms=latency_ms, retry_count=retry_count,
        )

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id, "request_id": self.request_id,
            "status": self.status, "output": self.output, "error": self.error,
            "audit_event_id": self.audit_event_id,
            "latency_ms": self.latency_ms, "retry_count": self.retry_count,
            "executed_at": self.executed_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ActionResult":
        return cls(
            result_id=d.get("result_id", ""), request_id=d.get("request_id", ""),
            status=d.get("status", STATUS_DRY_RUN), output=d.get("output", {}),
            error=d.get("error", ""), audit_event_id=d.get("audit_event_id", ""),
            latency_ms=d.get("latency_ms", 0), retry_count=d.get("retry_count", 0),
            executed_at=d.get("executed_at", ""),
        )

    @property
    def is_success(self) -> bool:
        return self.status == STATUS_SUCCESS

    @property
    def is_terminal(self) -> bool:
        return self.status in (STATUS_SUCCESS, STATUS_FAILED, STATUS_DENIED, STATUS_TIMEOUT)

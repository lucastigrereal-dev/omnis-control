"""P27 ActionSandbox — validation, rate enforcement, blocking."""
from typing import Optional

from src.real_world_actions.models import (
    ActionDefinition, ActionRequest, ActionResult,
    STATUS_BLOCKED, STATUS_DRY_RUN,
)
from src.real_world_actions.errors import (
    ActionBlockedError, RateLimitError, InvalidParamsError, UnknownActionError,
)
from src.real_world_actions.registry import ActionRegistry
from src.real_world_actions.rate_limiter import RateLimiter


class ActionSandbox:
    """Blocks unsafe actions; validates inputs; enforces rate limits."""

    def __init__(self, registry: ActionRegistry, rate_limiter: Optional[RateLimiter] = None):
        self.registry = registry
        self.rate_limiter = rate_limiter or RateLimiter()

    # ── Validation ────────────────────────────────────────────────

    def validate(self, action: ActionDefinition, params: dict) -> list[str]:
        """Validate params against action.input_schema. Returns list of errors (empty = ok)."""
        errors: list[str] = []
        schema = action.input_schema
        if not schema:
            return errors

        required = schema.get("required", [])
        for field in required:
            if field not in params or params[field] is None:
                errors.append(f"Missing required field: {field}")

        properties = schema.get("properties", {})
        for field, prop_schema in properties.items():
            if field not in params:
                continue
            val = params[field]
            expected_type = prop_schema.get("type", "")
            if expected_type == "string" and not isinstance(val, str):
                errors.append(f"Field '{field}' expected string, got {type(val).__name__}")
            elif expected_type == "number" and not isinstance(val, (int, float)):
                errors.append(f"Field '{field}' expected number, got {type(val).__name__}")
            elif expected_type == "boolean" and not isinstance(val, bool):
                errors.append(f"Field '{field}' expected boolean, got {type(val).__name__}")

        return errors

    # ── Blocking ──────────────────────────────────────────────────

    def is_allowed(self, action: ActionDefinition) -> bool:
        """Check if action can run. Returns False if disabled or provider is blocked."""
        if not action.enabled:
            return False
        return True

    def check_rate(self, action: ActionDefinition) -> bool:
        """Check if action is within rate limits."""
        return self.rate_limiter.check(action.provider, action.name, action.rate_limit)

    # ── Pre-flight ────────────────────────────────────────────────

    def preflight(self, action_name: str, params: dict) -> ActionResult:
        """Run all checks without executing. Returns ActionResult with validation info."""
        action = self.registry.find(action_name)

        if not self.is_allowed(action):
            return ActionResult.new(
                "", status=STATUS_BLOCKED,
                error=f"Action '{action_name}' is disabled or blocked",
            )

        errors = self.validate(action, params)
        within_rate = self.check_rate(action)

        return ActionResult.new(
            "", status=STATUS_DRY_RUN,
            output={
                "action": action.name,
                "provider": action.provider,
                "params": params,
                "validation_errors": errors,
                "would_execute": len(errors) == 0 and within_rate,
                "requires_approval": action.requires_approval,
                "risk_level": action.risk_level,
                "within_rate_limit": within_rate,
            },
        )

    # ── Dry-run preview ───────────────────────────────────────────

    def preview(self, action: ActionDefinition, params: dict) -> dict:
        """Generate dry-run preview — shows what WOULD happen."""
        errors = self.validate(action, params)
        within_rate = self.check_rate(action)
        return {
            "action": action.name,
            "provider": action.provider,
            "action_type": action.action_type,
            "risk_level": action.risk_level,
            "requires_approval": action.requires_approval,
            "params": params,
            "validation_errors": errors,
            "would_execute": len(errors) == 0 and within_rate,
            "within_rate_limit": within_rate,
            "timeout_seconds": action.timeout_seconds,
            "retry_policy": action.retry_policy.to_dict(),
        }

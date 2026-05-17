"""W146 — n8n Safety Gate (validates workflows before execution)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import AutomationWorkflow, _now_iso


@dataclass
class SafetyCheckResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "checked_at": self.checked_at,
        }


class N8nSafetyGate:
    """Validates AutomationWorkflow against safety rules before n8n export/trigger."""

    MAX_STEPS = 20
    FORBIDDEN_STEP_NAMES = {"delete_all", "drop_table", "rm_rf", "force_push"}
    FORBIDDEN_CONFIG_KEYS = {"api_key", "password", "secret", "token"}

    def check(self, workflow: AutomationWorkflow) -> SafetyCheckResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not workflow.name or not workflow.name.strip():
            errors.append("Workflow must have a non-empty name")

        if not workflow.trigger:
            errors.append("Workflow must have a trigger")

        if len(workflow.steps) > self.MAX_STEPS:
            errors.append(f"Too many steps ({len(workflow.steps)} > {self.MAX_STEPS})")

        if len(workflow.steps) == 0:
            warnings.append("Workflow has no steps — trigger only")

        for step in workflow.steps:
            if step.name.lower() in self.FORBIDDEN_STEP_NAMES:
                errors.append(f"Forbidden step name: {step.name!r}")
            for key in step.config:
                if key.lower() in self.FORBIDDEN_CONFIG_KEYS:
                    errors.append(f"Forbidden config key in step '{step.name}': {key!r}")

        for key in workflow.trigger.config:
            if key.lower() in self.FORBIDDEN_CONFIG_KEYS:
                errors.append(f"Forbidden config key in trigger: {key!r}")

        if not workflow.active:
            warnings.append("Workflow is inactive — trigger will be no-op")

        return SafetyCheckResult(passed=len(errors) == 0, errors=errors, warnings=warnings)

    def assert_safe(self, workflow: AutomationWorkflow) -> None:
        result = self.check(workflow)
        if not result.passed:
            raise ValueError(f"Safety gate failed: {result.errors}")

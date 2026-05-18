"""WorkflowProvider — workflow orchestration abstraction for OMNIS.

Backends:
1. SequentialWorkflowProvider — built-in, executes steps in order (no deps)
2. LangGraphProvider          — stateful graphs with checkpointing (optional)

Replaces: mission_orchestrator, runtime_orchestrator, autonomous_execution (partially)
"""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from src.providers.base import Provider, ProviderHealth, ProviderStatus


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    id: str
    name: str
    fn: Callable[[dict[str, Any]], Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    workflow_id: str
    status: str  # "completed" | "failed" | "partial"
    steps_completed: int
    steps_total: int
    outputs: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.status == "completed"


class WorkflowProvider(Provider):
    """Abstract workflow provider. Use registry.get('workflow') to get instance."""

    @property
    def name(self) -> str:
        return "workflow"

    @abstractmethod
    def execute(
        self,
        steps: list[WorkflowStep],
        *,
        initial_state: Optional[dict[str, Any]] = None,
        dry_run: bool = True,
    ) -> WorkflowResult:
        """Execute a list of steps. dry_run=True skips actual side effects."""


# ── Built-in fallback: SequentialWorkflowProvider ─────────────────────────

class SequentialWorkflowProvider(WorkflowProvider):
    """Executes steps sequentially, passing state between them.

    Zero dependencies. dry_run=True records steps without executing fn.
    Replaces the pattern used across mission_orchestrator and runtime_orchestrator.
    """

    @property
    def backend(self) -> str:
        return "sequential"

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider_name=self.name,
            backend=self.backend,
        )

    def execute(
        self,
        steps: list[WorkflowStep],
        *,
        initial_state: Optional[dict[str, Any]] = None,
        dry_run: bool = True,
    ) -> WorkflowResult:
        import uuid
        workflow_id = str(uuid.uuid4())
        state = dict(initial_state or {})
        outputs: dict[str, Any] = {}
        errors: list[str] = []
        completed = 0

        for step in steps:
            if dry_run:
                outputs[step.id] = {"dry_run": True, "step": step.name}
                completed += 1
                continue
            try:
                result = step.fn(state)
                outputs[step.id] = result
                if isinstance(result, dict):
                    state.update(result)
                completed += 1
            except Exception as e:
                errors.append(f"{step.id}: {e}")
                break

        status = "completed" if completed == len(steps) else ("partial" if completed > 0 else "failed")
        return WorkflowResult(
            workflow_id=workflow_id,
            status=status,
            steps_completed=completed,
            steps_total=len(steps),
            outputs=outputs,
            errors=errors,
        )

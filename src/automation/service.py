"""P12 Automation service — WorkflowPlanner, spec exporter, validator."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from src.automation.models import (
    AutomationWorkflow,
    AutomationStep,
    AutomationRunPlan,
    RUN_PLANNED,
)
from src.automation.errors import (
    CycleDetectedError,
    UnresolvedDependencyError,
    EmptyWorkflowError,
    WorkflowValidationError,
    PlanError,
)

# ── n8n node type mapping ──────────────────────────────────────────────
_N8N_TYPE_MAP = {
    "http_request": "n8n-nodes-base.httpRequest",
    "transform": "n8n-nodes-base.function",
    "filter": "n8n-nodes-base.if",
    "merge": "n8n-nodes-base.merge",
    "delay": "n8n-nodes-base.wait",
    "notify": "n8n-nodes-base.emailSend",
}

_N8N_TRIGGER_MAP = {
    "webhook": "n8n-nodes-base.webhook",
    "schedule": "n8n-nodes-base.scheduleTrigger",
    "manual": "n8n-nodes-base.manualTrigger",
    "mission_completed": "n8n-nodes-base.webhook",
}


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


# ── Topological sort (Kahn's algorithm) ────────────────────────────────

def _topological_sort(steps: list[AutomationStep]) -> list[str]:
    """Return step IDs in topological order. Raises on cycles or missing deps."""
    step_ids = {s.step_id for s in steps}
    in_degree: dict[str, int] = {}
    adj: dict[str, list[str]] = {}

    for s in steps:
        if s.step_id not in in_degree:
            in_degree[s.step_id] = 0
        adj.setdefault(s.step_id, [])

    for s in steps:
        for dep in s.depends_on:
            if dep not in step_ids:
                raise UnresolvedDependencyError(
                    f"Step {s.step_id!r} depends on {dep!r}, but it does not exist"
                )
            adj.setdefault(dep, []).append(s.step_id)
            in_degree[s.step_id] = in_degree.get(s.step_id, 0) + 1

    queue: deque[str] = deque(sid for sid, deg in in_degree.items() if deg == 0)
    sorted_ids: list[str] = []

    while queue:
        sid = queue.popleft()
        sorted_ids.append(sid)
        for neighbor in adj.get(sid, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_ids) != len(steps):
        remaining = set(step_ids) - set(sorted_ids)
        raise CycleDetectedError(f"Cycle detected involving steps: {sorted(remaining)}")

    return sorted_ids


# ── WorkflowPlanner ─────────────────────────────────────────────────────

class WorkflowPlanner:
    """Deterministic planner: resolves dependencies → run plan."""

    def plan(self, workflow: AutomationWorkflow, dry_run: bool = True) -> AutomationRunPlan:
        if not workflow.steps:
            raise PlanError(f"Workflow {workflow.workflow_id!r} has no steps to plan")

        try:
            sorted_ids = _topological_sort(workflow.steps)
        except (CycleDetectedError, UnresolvedDependencyError):
            raise
        except Exception as exc:
            raise PlanError(f"Failed to plan workflow {workflow.workflow_id!r}: {exc}") from exc

        return AutomationRunPlan.new(
            workflow_id=workflow.workflow_id,
            steps_to_execute=sorted_ids,
            dry_run=dry_run,
        )


# ── n8n spec exporter ──────────────────────────────────────────────────

def _make_connection(target_node_id: str) -> dict:
    return {"node": target_node_id, "type": "main", "index": 0}


def export_n8n_spec(workflow: AutomationWorkflow) -> dict:
    """Export a workflow as an n8n-compatible JSON spec (dry-run, no API call)."""
    trigger_node = {
        "id": workflow.trigger.trigger_id,
        "name": f"Trigger: {workflow.trigger.trigger_type}",
        "type": _N8N_TRIGGER_MAP.get(workflow.trigger.trigger_type, "n8n-nodes-base.webhook"),
        "position": [0, 0],
        "parameters": workflow.trigger.config,
    }

    step_nodes = []
    for i, step in enumerate(workflow.steps):
        node = {
            "id": step.step_id,
            "name": step.name,
            "type": _N8N_TYPE_MAP.get(step.step_type, "n8n-nodes-base.noOp"),
            "position": [250 + (i * 300), 300],
            "parameters": step.config,
        }
        step_nodes.append(node)

    n8n_connections: dict[str, dict] = {}

    for step in workflow.steps:
        if step.depends_on:
            for dep in step.depends_on:
                n8n_connections.setdefault(dep, {"main": []})
                n8n_connections[dep]["main"].append([_make_connection(step.step_id)])
        else:
            tid = workflow.trigger.trigger_id
            n8n_connections.setdefault(tid, {"main": []})
            n8n_connections[tid]["main"].append([_make_connection(step.step_id)])

    return {
        "name": workflow.name,
        "nodes": [trigger_node] + step_nodes,
        "connections": n8n_connections,
        "active": workflow.active,
        "settings": {},
        "versionId": "1.0.0-dryrun",
        "id": workflow.workflow_id,
        "meta": {
            "description": workflow.description,
            "dry_run": True,
            "exporter": "P12-automation-skeleton",
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
        },
    }


# ── Workflow validator ──────────────────────────────────────────────────

def validate_workflow(workflow: AutomationWorkflow) -> ValidationResult:
    """Validate workflow structure. Returns ValidationResult with errors and warnings."""
    errors: list[str] = []
    warnings: list[str] = []

    if not workflow.name.strip():
        errors.append("Workflow name is empty")

    if not workflow.steps:
        errors.append("Workflow has no steps")
    else:
        step_ids = {s.step_id for s in workflow.steps}
        positions: dict[int, list[str]] = {}

        for step in workflow.steps:
            if not step.name.strip():
                errors.append(f"Step {step.step_id!r} has empty name")

            for dep in step.depends_on:
                if dep not in step_ids:
                    errors.append(f"Step {step.step_id!r} depends on non-existent step {dep!r}")

            positions.setdefault(step.position, []).append(step.step_id)

        for pos, ids in positions.items():
            if len(ids) > 1:
                warnings.append(f"Multiple steps at position {pos}: {ids}")

        try:
            _topological_sort(workflow.steps)
        except CycleDetectedError as exc:
            errors.append(str(exc))
        except UnresolvedDependencyError as exc:
            errors.append(str(exc))

    if not workflow.trigger.enabled:
        warnings.append("Trigger is disabled; workflow will not auto-execute")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )

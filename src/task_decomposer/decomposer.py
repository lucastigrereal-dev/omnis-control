"""Task Decomposer — deterministic task generation from a SquadPlan."""
from __future__ import annotations

from datetime import datetime, timezone

from src.task_decomposer.models import (
    SquadTask,
    TaskPlan,
    TASK_STATUS_PLANNED,
    _make_task_id,
    _make_plan_id,
)
from src.task_decomposer.errors import CyclicDependencyError

# Role ordering — lower index = runs earlier
_ROLE_ORDER = [
    "marketing_strategist",
    "sales_strategist",
    "app_architect",
    "copywriter",
    "visual_director",
    "video_planner",
    "operations_manager",
    "qa_auditor",
]

# Explicit before→after dependency pairs
_ROLE_DEPENDENCIES: dict[str, list[str]] = {
    "copywriter": ["marketing_strategist", "sales_strategist"],
    "visual_director": ["copywriter", "marketing_strategist"],
    "video_planner": ["marketing_strategist", "copywriter"],
    "qa_auditor": ["copywriter", "visual_director", "video_planner", "app_architect", "operations_manager"],
}

# Role → task template
_ROLE_TASK_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "marketing_strategist": ("Define campaign strategy", "Map audience, objectives and content pillars", "strategy_brief"),
    "copywriter": ("Write content copy", "Write captions, CTAs and scripts per brief", "caption"),
    "visual_director": ("Define visual direction", "Create visual brief and creative direction", "visual_brief"),
    "video_planner": ("Create video plan", "Define shot list, hooks and video structure", "video_plan"),
    "sales_strategist": ("Create sales pitch", "Map objections and build offer logic", "pitch"),
    "app_architect": ("Define app architecture", "Scope entities, write technical spec and data model", "technical_spec"),
    "qa_auditor": ("QA review", "Validate all outputs, check risks and score quality", "quality_report"),
    "operations_manager": ("Create SOP", "Document workflow, define next actions and checklist", "sop"),
}


def _sort_roles(role_ids: list[str]) -> list[str]:
    ordered = [r for r in _ROLE_ORDER if r in role_ids]
    remainder = [r for r in role_ids if r not in _ROLE_ORDER]
    return ordered + remainder


def _resolve_deps(task_id_by_role: dict[str, str], role_id: str, present_roles: set[str]) -> list[str]:
    deps = _ROLE_DEPENDENCIES.get(role_id, [])
    return [task_id_by_role[dep] for dep in deps if dep in present_roles]


def _detect_cycle(graph: dict[str, list[str]]) -> bool:
    visited: set[str] = set()
    rec_stack: set[str] = set()

    def dfs(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.discard(node)
        return False

    for node in list(graph.keys()):
        if node not in visited:
            if dfs(node):
                return True
    return False


def decompose_squad(squad_plan) -> TaskPlan:
    """Generate a TaskPlan from a SquadPlan. Deterministic, no LLM."""
    role_ids = [r.role_id for r in squad_plan.roles]
    sorted_roles = _sort_roles(role_ids)
    present_roles = set(sorted_roles)

    # First pass: assign task IDs
    task_id_by_role: dict[str, str] = {rid: _make_task_id() for rid in sorted_roles}

    # Second pass: build tasks with dependencies
    tasks: list[SquadTask] = []
    dep_graph: dict[str, list[str]] = {}

    for role_id in sorted_roles:
        task_id = task_id_by_role[role_id]
        template = _ROLE_TASK_TEMPLATES.get(role_id)
        if template:
            title, desc, output = template
        else:
            title = f"Task for {role_id}"
            desc = f"Execute responsibilities of {role_id}"
            output = "output"

        depends = _resolve_deps(task_id_by_role, role_id, present_roles)
        dep_graph[task_id] = depends

        tasks.append(SquadTask(
            task_id=task_id,
            role_id=role_id,
            title=title,
            description=desc,
            expected_output=output,
            depends_on=depends,
            status=TASK_STATUS_PLANNED,
        ))

    if _detect_cycle(dep_graph):
        raise CyclicDependencyError("Cyclic dependency detected in task plan")

    return TaskPlan(
        task_plan_id=_make_plan_id(),
        squad_id=squad_plan.squad_id,
        request=squad_plan.request,
        tasks=tasks,
        dependency_graph=dep_graph,
        risk_level=squad_plan.risk_level,
        approval_required=squad_plan.approval_required,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

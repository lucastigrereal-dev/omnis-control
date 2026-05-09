"""Squad Execution Planner — creates dry-run execution plans."""
from __future__ import annotations

from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad
from src.squad_execution.models import SquadExecutionPlan


def plan_squad_run(request: str) -> SquadExecutionPlan:
    """Create a SquadExecutionPlan for the given request. Dry-run only."""
    squad = compose_squad(request)
    task_plan = decompose_squad(squad)
    return SquadExecutionPlan.from_plans(squad, task_plan)

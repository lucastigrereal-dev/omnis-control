"""plan_node — converte missão em plano de steps."""
from __future__ import annotations

from ..mission_state import MissionGraphState


def plan_node(state: MissionGraphState) -> dict:
    """Gera lista de steps para a missão.

    Tenta usar src.missions.task_decomposition (TaskDecomposition.create_default)
    se disponível. Fallback: plano mínimo com 3 steps genéricos.
    """
    try:
        from src.missions.task_decomposition import TaskDecomposition  # noqa: PLC0415

        decomposition = TaskDecomposition.create_default(state["mission_id"])
        steps = [
            {
                "name": task.id,
                "type": task.type.value,
                "description": task.description,
                "order": idx,
                "depends_on": list(task.depends_on),
            }
            for idx, task in enumerate(decomposition.tasks)
        ]
        if steps:
            return {"steps": steps}
    except Exception:
        pass

    # Fallback: 3 generic steps
    return {
        "steps": [
            {"name": "validate_input", "order": 0},
            {"name": "execute_main", "order": 1},
            {"name": "finalize_output", "order": 2},
        ]
    }

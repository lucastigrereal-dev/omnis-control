"""plan_node — converte missão em plano de steps."""
from __future__ import annotations

from ..mission_state import MissionGraphState


def plan_node(state: MissionGraphState) -> dict:
    """Gera lista de steps para a missão.

    Tenta usar src.missions.task_decomposition (TaskDecomposition.create_default)
    se disponível. Fallback: plano mínimo com 3 steps genéricos.

    Após gerar os steps, consulta AuroraPriority para calcular o score da missão.
    Aurora errors degradam gracefully — aurora_priority_score permanece 0.
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
            result = {"steps": steps}
            return _add_aurora_priority(state, result)
    except Exception:
        pass

    # Fallback: 3 generic steps
    result = {
        "steps": [
            {"name": "validate_input", "order": 0},
            {"name": "execute_main", "order": 1},
            {"name": "finalize_output", "order": 2},
        ]
    }
    return _add_aurora_priority(state, result)


def _add_aurora_priority(state: MissionGraphState, result: dict) -> dict:
    """Consulta AuroraPriority e adiciona aurora_priority_score ao resultado.

    Graceful degradation: se Aurora falhar, retorna result sem alterar o score.
    """
    try:
        from src.aurora.priority import AuroraPriority  # noqa: PLC0415

        scorer = AuroraPriority()
        description = str(result.get("steps", state.get("steps", [])))
        pendencia = f"{state['mission_id']} {description}"
        report = scorer.rank([pendencia])
        if report.items:
            result = {**result, "aurora_priority_score": report.items[0].score}
    except Exception:
        pass  # graceful degradation: Aurora indisponível, score permanece 0

    return result

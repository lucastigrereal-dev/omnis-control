from __future__ import annotations
from typing import Optional
from .mission_state import MissionGraphState, initial_state


def run_mission_graph(
    mission_id: str,
    use_langgraph: bool = False,
    max_retries: int = 3,
    mission_brief: Optional[dict] = None,
    config: Optional[dict] = None,
) -> MissionGraphState:
    """Execute a mission via LangGraph (opt-in).

    use_langgraph=False (default): raises NotImplementedError indicating
    that the existing runtime should be used instead.

    Args:
        mission_id: Unique identifier for the mission.
        use_langgraph: Must be True to use the LangGraph runtime.
        max_retries: Maximum retry attempts per node.
        mission_brief: Optional dict with mission context (e.g. titulo, setor).
        config: Optional LangGraph config dict.
    """
    if not use_langgraph:
        raise NotImplementedError(
            "LangGraph runtime é opt-in. Passe use_langgraph=True para usar. "
            "Para o runtime existente, use src/missions/runtime.py"
        )
    from .mission_graph import compile_mission_graph  # noqa: PLC0415
    state = initial_state(mission_id, max_retries=max_retries, brief=mission_brief)
    graph = compile_mission_graph()
    cfg = config or {}
    final = graph.invoke(state, cfg)
    return final


def resume_mission_graph(
    mission_id: str,
    checkpoint_id: str,
    use_langgraph: bool = False,
    config: Optional[dict] = None,
) -> MissionGraphState:
    """Resume a mission from a checkpoint.

    Checkpoint store will be implemented in D1.2.
    """
    if not use_langgraph:
        raise NotImplementedError(
            "LangGraph runtime é opt-in. Passe use_langgraph=True para usar."
        )
    from .mission_graph import compile_mission_graph  # noqa: PLC0415
    # Stub resume — checkpoint_store to be implemented in D1.2
    state = initial_state(mission_id)
    state["run_checkpoint_id"] = checkpoint_id
    graph = compile_mission_graph()
    cfg = config or {}
    final = graph.invoke(state, cfg)
    return final

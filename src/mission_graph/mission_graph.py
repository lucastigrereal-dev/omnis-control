"""D1 — LangGraph StateGraph skeleton for mission execution.

Import guard: langgraph is imported lazily to allow the module to be loaded
even when the langchain_core.messages.utils stub has not been injected yet.
The build_mission_graph() and compile_mission_graph() functions trigger the
real import at call-time; tests must inject the sys.modules stub before
calling these functions (see tests/mission_graph/conftest.py).
"""
from __future__ import annotations

from .mission_state import MissionGraphState
from .nodes.validate_node import validate_node, route_after_validate
from .nodes.plan_node import plan_node
from .nodes.execute_node import execute_node, route_after_execute
from .nodes.checkpoint_node import checkpoint_node
from .nodes.finalize_node import finalize_node
from src.sectors.marketing.graph_node import marketing_sector_node


def _route_after_plan(state: MissionGraphState) -> str:
    """Rota condicional após o nó plan: marketing → marketing_sector, default → execute."""
    brief = state.get("brief") or {}
    if brief.get("sector") == "marketing":
        return "marketing_sector"
    return "execute"


def build_mission_graph():
    """Build and return a StateGraph for mission execution.

    Imports langgraph at call-time so that the sys.modules stub for
    langchain_core.messages.utils can be injected beforehand by tests.
    """
    from langgraph.graph import StateGraph, END  # noqa: PLC0415

    g = StateGraph(MissionGraphState)
    g.add_node("validate", validate_node)
    g.add_node("plan", plan_node)
    g.add_node("execute", execute_node)
    g.add_node("checkpoint", checkpoint_node)
    g.add_node("finalize", finalize_node)
    g.add_node("marketing_sector", marketing_sector_node)

    g.set_entry_point("validate")
    g.add_conditional_edges("validate", route_after_validate, {
        "execute": "plan",
        "fail": "finalize",
    })
    g.add_conditional_edges("plan", _route_after_plan, {
        "execute": "execute",
        "marketing_sector": "marketing_sector",
    })
    g.add_conditional_edges("execute", route_after_execute, {
        "retry": "execute",
        "checkpoint": "checkpoint",
        "fail": "finalize",
    })
    g.add_edge("marketing_sector", "checkpoint")
    g.add_edge("checkpoint", "finalize")
    g.add_edge("finalize", END)

    return g


def compile_mission_graph():
    """Build and compile the mission graph."""
    return build_mission_graph().compile()

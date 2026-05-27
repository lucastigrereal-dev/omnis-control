"""graph_node — nó do grafo LangGraph para o setor de marketing."""
from __future__ import annotations

from src.mission_graph.mission_state import MissionGraphState
from src.sectors.marketing.router import MarketingRouter
from src.sectors.marketing.mission_types import MarketingMissionInput


def marketing_sector_node(state: MissionGraphState) -> dict:
    """Nó do grafo: roteia missões de marketing."""
    mission_data = state.get("brief", {})
    if not mission_data.get("goal"):
        return {"error": "brief.goal obrigatório para marketing_sector_node"}

    try:
        inp = MarketingMissionInput(
            type="content_production",
            squad=mission_data.get("squad", "instagram"),
            priority=mission_data.get("priority", "P2"),
            goal=mission_data["goal"],
            deadline=mission_data.get("deadline", "2099-12-31"),
            inputs=mission_data,
            model=mission_data.get("model", "haiku"),
        )
        router = MarketingRouter()
        result = router.execute(inp)
        return {
            "artifacts": [*state.get("artifacts", []), result.model_dump()],
            "cost_usd": state.get("cost_usd", 0.0) + result.cost_usd,
            "token_count": state.get("token_count", 0) + result.tokens_used,
        }
    except Exception as exc:
        return {"error": f"marketing_sector_node: {exc}"}

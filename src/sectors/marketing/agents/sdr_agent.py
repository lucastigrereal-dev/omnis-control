"""SDRAgent — stub para qualificação de leads comerciais."""
from __future__ import annotations

from src.sectors.marketing.agents.base import BaseMarketingAgent
from src.sectors.marketing.mission_types import MarketingMissionInput


class SDRAgent(BaseMarketingAgent):
    """Agente SDR (Sales Development Representative).

    Stub: simula qualificação de lead sem chamada LLM.
    """

    def execute_mission(self, input: MarketingMissionInput) -> dict:
        return {
            "status": "done",
            "output": f"SDRAgent qualificou lead para: {input.goal}",
            "cost_usd": 0.001,
            "tokens_used": 100,
        }

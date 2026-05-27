"""Squad Growth — ContentAgent + SDRAgent em paralelo."""
from src.sectors.marketing.agents.content_agent import ContentAgent
from src.sectors.marketing.agents.sdr_agent import SDRAgent

SQUAD_GROWTH_CONFIG = {
    "name": "Squad Growth",
    "parallel": [ContentAgent, SDRAgent],
    "sequential": [],
    "model": "haiku",
    "estimated_cost_usd": 0.008,
}

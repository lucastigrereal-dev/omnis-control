"""Squad Comercial — SDRAgent → ContentAgent em sequência."""
from src.sectors.marketing.agents.sdr_agent import SDRAgent
from src.sectors.marketing.agents.content_agent import ContentAgent

SQUAD_COMERCIAL_CONFIG = {
    "name": "Squad Comercial",
    "parallel": [],
    "sequential": [SDRAgent, ContentAgent],
    "model": "haiku",
    "estimated_cost_usd": 0.005,
}

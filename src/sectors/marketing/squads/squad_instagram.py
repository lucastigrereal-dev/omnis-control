"""Squad Instagram — ContentAgent em paralelo."""
from src.sectors.marketing.agents.content_agent import ContentAgent
from src.sectors.marketing.agents.sdr_agent import SDRAgent

SQUAD_INSTAGRAM_CONFIG = {
    "name": "Squad Instagram",
    "parallel": [ContentAgent],      # conteúdo
    "sequential": [],                 # nada sequencial por ora
    "model": "haiku",
    "estimated_cost_usd": 0.005,
}

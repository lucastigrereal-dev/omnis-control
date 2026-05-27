"""Tipos de missão do setor de marketing — enums e dataclasses de entrada/saída."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class MarketingMissionType(str, Enum):
    CONTENT_PRODUCTION = "content_production"
    LEAD_PROCESSING = "lead_processing"
    WEEKLY_REVIEW = "weekly_review"
    CAMPAIGN_STRATEGY = "campaign_strategy"


@dataclass
class MarketingMissionInput:
    """Dados de entrada para uma missão de marketing."""
    type: str
    squad: str  # "instagram" | "comercial" | "growth"
    priority: str  # "P1" | "P2" | "P3"
    goal: str
    deadline: str
    inputs: dict = field(default_factory=dict)
    model: str = "haiku"  # "haiku" | "sonnet" — NUNCA opus
    page: Optional[str] = None

    def __post_init__(self) -> None:
        if self.model == "opus":
            raise ValueError("Modelo opus não é permitido no setor de marketing.")


@dataclass
class MarketingMissionOutput:
    """Dados de saída de uma missão de marketing."""
    mission_id: str
    status: str  # "done" | "blocked" | "escalated"
    outputs: list[dict] = field(default_factory=list)
    cost_usd: float = 0.0
    tokens_used: int = 0

    def model_dump(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "status": self.status,
            "outputs": self.outputs,
            "cost_usd": self.cost_usd,
            "tokens_used": self.tokens_used,
        }

"""Cost Tracking Contract — adapter interface for mission cost estimation/tracking."""
from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict


class CostEstimate(BaseModel):
    """Estimated vs actual cost for a mission."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mission_id: str = ""
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    currency: str = "USD"
    source: str = "mock"


class CostTracker(ABC):
    """Abstract interface for cost tracking adapters."""

    @abstractmethod
    def estimate(self, mission_id: str, task_count: int, estimated_tokens: int) -> CostEstimate: ...

    @abstractmethod
    def actual(self, mission_id: str) -> CostEstimate: ...


class MockCostTracker(CostTracker):
    """Mock cost tracker — always returns zero cost for testing and offline dev."""

    def estimate(self, mission_id: str, task_count: int, estimated_tokens: int) -> CostEstimate:
        return CostEstimate(
            mission_id=mission_id,
            estimated_cost=0.0,
            actual_cost=0.0,
            source="mock",
        )

    def actual(self, mission_id: str) -> CostEstimate:
        return CostEstimate(
            mission_id=mission_id,
            estimated_cost=0.0,
            actual_cost=0.0,
            source="mock",
        )

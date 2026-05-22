"""MissionPackage — wraps contract + plan + memory + cost + events."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.missions.models import MissionContract
from src.missions.task_decomposition import TaskDecomposition
from src.missions.memory_lookup import MemoryContext
from src.missions.cost_tracker import CostEstimate


class MissionPackage(BaseModel):
    """Aggregated mission package bringing together all M6.x concerns."""

    model_config = ConfigDict(extra="forbid")

    contract: MissionContract
    plan: TaskDecomposition = Field(default_factory=TaskDecomposition)
    memory: MemoryContext = Field(default_factory=MemoryContext)
    cost: CostEstimate = Field(default_factory=CostEstimate)
    event_count: int = 0

    def summary(self) -> dict:
        return {
            "mission_id": self.contract.mission_id or self.contract.content_hash(),
            "title": self.contract.title,
            "status": self.contract.priority.value if hasattr(self.contract.priority, "value") else "unknown",
            "priority": self.contract.priority.value if hasattr(self.contract.priority, "value") else "unknown",
            "task_count": len(self.plan.tasks),
            "memory_source": self.memory.source,
            "cost_estimate": self.cost.estimated_cost,
            "event_count": self.event_count,
        }

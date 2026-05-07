"""Metrics Spine models — Pydantic v2. P0.9."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class MetricEvent(BaseModel):
    """Evento atomico de metrica — uma observacao pontual."""

    model_config = ConfigDict(extra="forbid")

    metric_id: str = ""
    timestamp: str = ""
    mission_id: str = ""
    run_id: str = ""
    tool_id: str = ""
    event_type: str = ""
    name: str
    value: float = 0.0
    unit: str = ""
    status: str = ""
    duration_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if "metric_id" not in data or not data["metric_id"]:
            data["metric_id"] = uuid.uuid4().hex[:12]
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = now
        super().__init__(**data)


class RunSummary(BaseModel):
    """Resumo agregado de uma execucao de pipeline/missao."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    mission_id: str = ""
    started_at: str = ""
    finished_at: str = ""
    status: str = "running"
    duration_ms: float = 0.0
    events_count: int = 0
    tools_used: List[str] = Field(default_factory=list)
    artifacts_count: int = 0
    warnings_count: int = 0
    retries_count: int = 0
    checkpoints_count: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    def __init__(self, **data):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if "started_at" not in data or not data["started_at"]:
            data["started_at"] = now
        super().__init__(**data)

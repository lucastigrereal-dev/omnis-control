"""Models for Execution Graph Lite."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class StepStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


def _make_graph_id() -> str:
    raw = os.urandom(8)
    return "graph_" + hashlib.sha256(raw).hexdigest()[:8]


def _make_step_id() -> str:
    raw = os.urandom(4)
    return "step_" + hashlib.sha256(raw).hexdigest()[:6]


@dataclass
class StepNode:
    step_id: str
    task_id: str
    role_id: str
    title: str
    description: str
    expected_output: str
    depends_on: list[str]  # step_ids
    status: StepStatus = StepStatus.PENDING
    estimated_duration: str = "5min"
    assigned_role: str = ""

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "task_id": self.task_id,
            "role_id": self.role_id,
            "title": self.title,
            "description": self.description,
            "expected_output": self.expected_output,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "estimated_duration": self.estimated_duration,
            "assigned_role": self.assigned_role,
        }


@dataclass
class ExecutionGraph:
    graph_id: str
    request: str
    squad_id: str
    task_plan_id: str
    nodes: list[StepNode]
    edges: list[tuple[str, str]]  # (from_step_id, to_step_id)
    topological_order: list[str]  # step_ids in execution order
    created_at: str

    @property
    def node_map(self) -> dict[str, StepNode]:
        return {n.step_id: n for n in self.nodes}

    def to_dict(self) -> dict:
        return {
            "graph_id": self.graph_id,
            "request": self.request,
            "squad_id": self.squad_id,
            "task_plan_id": self.task_plan_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [list(e) for e in self.edges],
            "topological_order": self.topological_order,
            "created_at": self.created_at,
        }

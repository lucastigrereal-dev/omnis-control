"""Models for Task Decomposer."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

TASK_STATUS_PLANNED = "planned"
TASK_STATUS_BLOCKED = "blocked"
TASK_STATUS_READY = "ready"
TASK_STATUS_DONE_FUTURE = "done_future"


def _make_task_id() -> str:
    raw = os.urandom(4)
    return "task_" + hashlib.sha256(raw).hexdigest()[:6]


def _make_plan_id() -> str:
    raw = os.urandom(8)
    return "tplan_" + hashlib.sha256(raw).hexdigest()[:8]


@dataclass
class SquadTask:
    task_id: str
    role_id: str
    title: str
    description: str
    expected_output: str
    depends_on: list[str]
    status: str = TASK_STATUS_PLANNED

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "role_id": self.role_id,
            "title": self.title,
            "description": self.description,
            "expected_output": self.expected_output,
            "depends_on": self.depends_on,
            "status": self.status,
        }


@dataclass
class TaskPlan:
    task_plan_id: str
    squad_id: str
    request: str
    tasks: list[SquadTask]
    dependency_graph: dict[str, list[str]]
    risk_level: str
    approval_required: bool
    created_at: str

    def to_dict(self) -> dict:
        return {
            "task_plan_id": self.task_plan_id,
            "squad_id": self.squad_id,
            "request": self.request,
            "tasks": [t.to_dict() for t in self.tasks],
            "dependency_graph": self.dependency_graph,
            "risk_level": self.risk_level,
            "approval_required": self.approval_required,
            "created_at": self.created_at,
        }

    @classmethod
    def from_squad(cls, squad_plan) -> "TaskPlan":
        from src.task_decomposer.decomposer import decompose_squad
        return decompose_squad(squad_plan)

"""Parallel Runner data models."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class RunnerTask:
    task_id: str
    name: str
    args: list = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)
    timeout: float = 30.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> RunnerTask:
        return cls(
            task_id=d["task_id"],
            name=d["name"],
            args=d.get("args", []),
            kwargs=d.get("kwargs", {}),
            timeout=d.get("timeout", 30.0),
        )


@dataclass
class RunnerResult:
    task_id: str
    name: str
    success: bool
    result: Any = None
    error: str = ""
    duration: float = 0.0
    status: RunStatus = RunStatus.PENDING
    started_at: str = ""
    finished_at: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> RunnerResult:
        return cls(
            task_id=d["task_id"],
            name=d["name"],
            success=d.get("success", False),
            result=d.get("result"),
            error=d.get("error", ""),
            duration=d.get("duration", 0.0),
            status=RunStatus(d.get("status", "pending")),
            started_at=d.get("started_at", ""),
            finished_at=d.get("finished_at", ""),
        )


@dataclass
class RunBatch:
    batch_id: str
    tasks: list[RunnerTask] = field(default_factory=list)
    results: list[RunnerResult] = field(default_factory=list)
    status: RunStatus = RunStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    finished_at: str = ""

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.success and r.status != RunStatus.PENDING)

    @property
    def total_duration(self) -> float:
        return sum(r.duration for r in self.results)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        d["results"] = [r.to_dict() for r in self.results]
        d["tasks"] = [t.to_dict() for t in self.tasks]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> RunBatch:
        return cls(
            batch_id=d["batch_id"],
            tasks=[RunnerTask.from_dict(t) for t in d.get("tasks", [])],
            results=[RunnerResult.from_dict(r) for r in d.get("results", [])],
            status=RunStatus(d.get("status", "pending")),
            created_at=d.get("created_at", ""),
            finished_at=d.get("finished_at", ""),
        )

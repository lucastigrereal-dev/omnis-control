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


RUN_STATUS_RUNNING = "running"
RUN_STATUS_DONE = "done"
RUN_STATUS_FAILED = "failed"


def _make_graph_id() -> str:
    raw = os.urandom(8)
    return "graph_" + hashlib.sha256(raw).hexdigest()[:8]


def _make_step_id() -> str:
    raw = os.urandom(4)
    return "step_" + hashlib.sha256(raw).hexdigest()[:6]


def _make_run_id() -> str:
    raw = os.urandom(8)
    return "grun_" + hashlib.sha256(raw).hexdigest()[:8]


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

    @classmethod
    def from_dict(cls, d: dict) -> "StepNode":
        return cls(
            step_id=d["step_id"],
            task_id=d["task_id"],
            role_id=d["role_id"],
            title=d["title"],
            description=d["description"],
            expected_output=d["expected_output"],
            depends_on=list(d.get("depends_on", [])),
            status=StepStatus(d.get("status", "pending")),
            estimated_duration=d.get("estimated_duration", "5min"),
            assigned_role=d.get("assigned_role", ""),
        )


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

    @classmethod
    def from_dict(cls, d: dict) -> "ExecutionGraph":
        return cls(
            graph_id=d["graph_id"],
            request=d["request"],
            squad_id=d["squad_id"],
            task_plan_id=d["task_plan_id"],
            nodes=[StepNode.from_dict(n) for n in d["nodes"]],
            edges=[tuple(e) for e in d["edges"]],
            topological_order=list(d.get("topological_order", [])),
            created_at=d.get("created_at", ""),
        )


@dataclass
class StepRunLog:
    """A single event during step execution."""
    step_id: str
    role_id: str
    status: str  # StepStatus value
    message: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "role_id": self.role_id,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp,
        }


RUN_STATUS_BLOCKED = "blocked_pending_approval"
RUN_STATUS_SHADOW = "shadow"


@dataclass
class ShadowConfig:
    """Per-node dry_run control for gradual shadow→real transition.

    Each node starts with dry_run=True (shadow). As nodes are validated,
    their dry_run flag is removed, allowing real execution.
    """

    node_dry_run: dict[str, bool] = field(default_factory=dict)
    shadow_mode: bool = True
    replay_trace_enabled: bool = True
    real_nodes: set[str] = field(default_factory=set)

    def is_dry_run(self, step_id: str) -> bool:
        """Check if a specific node is still in dry_run (shadow) mode."""
        if not self.shadow_mode:
            return False
        if step_id in self.real_nodes:
            return False
        return self.node_dry_run.get(step_id, True)

    def promote_to_real(self, step_id: str) -> None:
        """Promote a single node from shadow to real execution."""
        self.real_nodes.add(step_id)
        self.node_dry_run[step_id] = False

    def promote_all(self) -> None:
        """Promote all nodes to real execution (exit shadow mode)."""
        self.shadow_mode = False

    def remaining_shadow_nodes(self, graph: "ExecutionGraph") -> set[str]:
        """Return set of step_ids still in shadow mode."""
        return {n.step_id for n in graph.nodes if self.is_dry_run(n.step_id)}

    def to_dict(self) -> dict:
        return {
            "node_dry_run": self.node_dry_run,
            "shadow_mode": self.shadow_mode,
            "replay_trace_enabled": self.replay_trace_enabled,
            "real_nodes": sorted(self.real_nodes),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ShadowConfig":
        return cls(
            node_dry_run=d.get("node_dry_run", {}),
            shadow_mode=d.get("shadow_mode", True),
            replay_trace_enabled=d.get("replay_trace_enabled", True),
            real_nodes=set(d.get("real_nodes", [])),
        )


@dataclass
class StepRun:
    """Complete dry-run execution of a graph."""
    graph_run_id: str
    graph_id: str
    request: str
    status: str  # running | done | failed | blocked_pending_approval
    step_states: dict[str, str]  # step_id → status
    logs: list[StepRunLog]
    started_at: str
    finished_at: str
    graph_snapshot: dict | None = None  # graph.to_dict() for resume/replay
    approval_id: str | None = None  # linked approval request
    approval_required: bool = False  # whether approval was checked

    @classmethod
    def blocked(
        cls,
        graph: "ExecutionGraph",
        reason: str = "",
        approval_id: str | None = None,
        approval_required: bool = False,
    ) -> "StepRun":
        """Create a blocked StepRun (approval pending or rejected)."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        log = StepRunLog(
            step_id="",
            role_id="",
            status=RUN_STATUS_BLOCKED,
            message=reason,
            timestamp=now,
        )
        return cls(
            graph_run_id=_make_run_id(),
            graph_id=graph.graph_id,
            request=graph.request,
            status=RUN_STATUS_BLOCKED,
            step_states={},
            logs=[log],
            started_at=now,
            finished_at=now,
            graph_snapshot=graph.to_dict(),
            approval_id=approval_id,
            approval_required=approval_required,
        )

    def to_dict(self) -> dict:
        return {
            "graph_run_id": self.graph_run_id,
            "graph_id": self.graph_id,
            "request": self.request,
            "status": self.status,
            "step_states": self.step_states,
            "logs": [l.to_dict() for l in self.logs],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "graph_snapshot": self.graph_snapshot,
            "approval_id": self.approval_id,
            "approval_required": self.approval_required,
        }

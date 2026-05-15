"""Rollback plan for execution graph — compensation on failure."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RollbackStatus(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class RollbackAction:
    action_id: str
    step_id: str
    description: str
    target: str  # what artifact/resource to undo
    status: RollbackStatus = RollbackStatus.PENDING

    def to_dict(self) -> dict:
        return {
            "action_id": self.action_id,
            "step_id": self.step_id,
            "description": self.description,
            "target": self.target,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RollbackAction":
        return cls(
            action_id=d["action_id"],
            step_id=d["step_id"],
            description=d.get("description", ""),
            target=d.get("target", ""),
            status=RollbackStatus(d.get("status", "pending")),
        )


@dataclass
class RollbackPlan:
    plan_id: str
    graph_run_id: str
    actions: list[RollbackAction] = field(default_factory=list)
    executed_at: str = ""

    def add_action(self, action: RollbackAction) -> None:
        self.actions.append(action)

    def actions_for_step(self, step_id: str) -> list[RollbackAction]:
        return [a for a in self.actions if a.step_id == step_id]

    def pending_actions(self) -> list[RollbackAction]:
        return [a for a in self.actions if a.status == RollbackStatus.PENDING]

    def execute_dry(self, completed_step_ids: set[str]) -> list[dict]:
        """Simulate executing rollback for completed steps. Returns log entries.

        In dry-run mode, rollback runs backwards through completed steps.
        Only steps that actually completed (DONE) get rolled back.
        """
        log: list[dict] = []

        # Rollback only actions whose step completed
        for action in self.actions:
            if action.step_id not in completed_step_ids:
                action.status = RollbackStatus.SKIPPED
                log.append({
                    "action_id": action.action_id,
                    "step_id": action.step_id,
                    "status": "skipped",
                    "message": f"Rollback skipped — step {action.step_id} was not completed",
                })
                continue

            action.status = RollbackStatus.EXECUTED
            log.append({
                "action_id": action.action_id,
                "step_id": action.step_id,
                "status": "executed",
                "message": f"Rollback executed: {action.description} (target: {action.target})",
            })

        return log

    def is_empty(self) -> bool:
        return len(self.actions) == 0

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "graph_run_id": self.graph_run_id,
            "actions": [a.to_dict() for a in self.actions],
            "executed_at": self.executed_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RollbackPlan":
        return cls(
            plan_id=d["plan_id"],
            graph_run_id=d.get("graph_run_id", ""),
            actions=[RollbackAction.from_dict(a) for a in d.get("actions", [])],
            executed_at=d.get("executed_at", ""),
        )

    @classmethod
    def build_for_graph(cls, plan_id: str, graph_run_id: str, graph) -> "RollbackPlan":
        """Build a rollback plan from graph nodes — one undo action per step."""
        plan = cls(plan_id=plan_id, graph_run_id=graph_run_id)
        for i, node in enumerate(graph.nodes):
            action = RollbackAction(
                action_id=f"rb_{node.step_id}",
                step_id=node.step_id,
                description=f"Undo step '{node.title}'",
                target=node.expected_output,
            )
            plan.add_action(action)
        return plan

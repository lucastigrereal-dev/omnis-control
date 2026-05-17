"""W143 — n8n Workflow Bridge (mock-first, dry_run=True default)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import AutomationWorkflow, _now_iso, _new_id


N8N_NODE_TYPES = {
    "http_request": "n8n-nodes-base.httpRequest",
    "transform": "n8n-nodes-base.set",
    "filter": "n8n-nodes-base.if",
    "merge": "n8n-nodes-base.merge",
    "delay": "n8n-nodes-base.wait",
    "notify": "n8n-nodes-base.slack",
}

TRIGGER_NODE_TYPES = {
    "webhook": "n8n-nodes-base.webhook",
    "schedule": "n8n-nodes-base.scheduleTrigger",
    "manual": "n8n-nodes-base.manualTrigger",
    "mission_completed": "n8n-nodes-base.webhook",
}


@dataclass
class N8nWorkflowExport:
    """n8n-compatible workflow JSON export (dry-run safe)."""
    export_id: str
    workflow_id: str
    n8n_json: dict
    node_count: int
    dry_run: bool = True
    exported_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "export_id": self.export_id,
            "workflow_id": self.workflow_id,
            "n8n_json": self.n8n_json,
            "node_count": self.node_count,
            "dry_run": self.dry_run,
            "exported_at": self.exported_at,
        }


@dataclass
class N8nTriggerResult:
    """Mock result of triggering an n8n workflow execution."""
    result_id: str
    workflow_id: str
    execution_id: str
    status: str
    dry_run: bool = True
    triggered_at: str = field(default_factory=_now_iso)
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "status": self.status,
            "dry_run": self.dry_run,
            "triggered_at": self.triggered_at,
            "message": self.message,
        }


class N8nBridge:
    """Converts OMNIS AutomationWorkflow to n8n format and mocks trigger."""

    def export_workflow(self, workflow: AutomationWorkflow, dry_run: bool = True) -> N8nWorkflowExport:
        trigger_node = {
            "id": workflow.trigger.trigger_id,
            "name": f"Trigger ({workflow.trigger.trigger_type})",
            "type": TRIGGER_NODE_TYPES.get(workflow.trigger.trigger_type, "n8n-nodes-base.webhook"),
            "parameters": workflow.trigger.config,
            "position": [0, 0],
        }
        step_nodes = []
        for i, step in enumerate(workflow.steps):
            step_nodes.append({
                "id": step.step_id,
                "name": step.name,
                "type": N8N_NODE_TYPES.get(step.step_type, "n8n-nodes-base.set"),
                "parameters": step.config,
                "position": [(i + 1) * 200, 0],
            })
        connections = {}
        all_nodes = [trigger_node] + step_nodes
        for idx in range(len(all_nodes) - 1):
            src = all_nodes[idx]["name"]
            dst = all_nodes[idx + 1]["name"]
            connections[src] = {"main": [[{"node": dst, "type": "main", "index": 0}]]}

        n8n_json = {
            "name": workflow.name,
            "nodes": all_nodes,
            "connections": connections,
            "active": workflow.active,
            "settings": {},
            "tags": ["omnis", "auto-generated"],
        }
        return N8nWorkflowExport(
            export_id=_new_id("n8n_exp"),
            workflow_id=workflow.workflow_id,
            n8n_json=n8n_json,
            node_count=len(all_nodes),
            dry_run=dry_run,
        )

    def trigger_workflow(self, workflow: AutomationWorkflow, dry_run: bool = True) -> N8nTriggerResult:
        execution_id = _new_id("exec") if not dry_run else f"dry_{_new_id('exec')}"
        status = "simulated" if dry_run else "triggered"
        message = (
            f"[DRY-RUN] Would trigger n8n workflow '{workflow.name}' via {workflow.trigger.trigger_type}"
            if dry_run
            else f"Triggered n8n workflow '{workflow.name}'"
        )
        return N8nTriggerResult(
            result_id=_new_id("n8n_res"),
            workflow_id=workflow.workflow_id,
            execution_id=execution_id,
            status=status,
            dry_run=dry_run,
            message=message,
        )

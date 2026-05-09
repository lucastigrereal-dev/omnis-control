"""Execution Graph Builder — deterministic DAG from SquadPlan + TaskPlan."""
from __future__ import annotations

from datetime import datetime, timezone

from src.execution_graph.models import (
    ExecutionGraph,
    StepNode,
    StepStatus,
    _make_graph_id,
    _make_step_id,
)
from src.execution_graph.errors import GraphBuildError


_DURATION_BY_ROLE: dict[str, str] = {
    "marketing_strategist": "30min",
    "copywriter": "45min",
    "visual_director": "30min",
    "video_planner": "60min",
    "sales_strategist": "30min",
    "app_architect": "60min",
    "qa_auditor": "20min",
    "operations_manager": "25min",
}


def build_graph(squad_plan, task_plan) -> ExecutionGraph:
    """Build an ExecutionGraph from a SquadPlan and TaskPlan.

    Each SquadTask becomes a StepNode. Edges are derived from task dependencies.
    Topological order respects existing task order + dependency constraints.
    """
    if not task_plan.tasks:
        raise GraphBuildError("Cannot build graph: TaskPlan has no tasks")

    # Create step nodes
    nodes: list[StepNode] = []
    task_to_step: dict[str, str] = {}

    for task in task_plan.tasks:
        step_id = _make_step_id()
        task_to_step[task.task_id] = step_id

        duration = _DURATION_BY_ROLE.get(task.role_id, "10min")

        nodes.append(StepNode(
            step_id=step_id,
            task_id=task.task_id,
            role_id=task.role_id,
            title=task.title,
            description=task.description,
            expected_output=task.expected_output,
            depends_on=[],  # resolved in second pass
            status=StepStatus.PENDING,
            estimated_duration=duration,
            assigned_role=task.role_id,
        ))

    # Second pass: resolve step-level dependencies
    for node in nodes:
        task = _get_task_by_id(task_plan, node.task_id)
        if task:
            node.depends_on = [
                task_to_step[dep]
                for dep in task.depends_on
                if dep in task_to_step
            ]

    # Compute edges
    edges: list[tuple[str, str]] = []
    for node in nodes:
        for dep in node.depends_on:
            edges.append((dep, node.step_id))

    # Topological sort via Kahn's algorithm
    top_order = _topological_sort(nodes, edges)

    return ExecutionGraph(
        graph_id=_make_graph_id(),
        request=task_plan.request,
        squad_id=task_plan.squad_id,
        task_plan_id=task_plan.task_plan_id,
        nodes=nodes,
        edges=edges,
        topological_order=top_order,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _get_task_by_id(task_plan, task_id: str):
    for t in task_plan.tasks:
        if t.task_id == task_id:
            return t
    return None


def _topological_sort(nodes: list[StepNode], edges: list[tuple[str, str]]) -> list[str]:
    """Kahn's algorithm for topological ordering."""
    in_degree: dict[str, int] = {n.step_id: 0 for n in nodes}
    adj: dict[str, list[str]] = {n.step_id: [] for n in nodes}

    for src, dst in edges:
        adj[src].append(dst)
        in_degree[dst] = in_degree.get(dst, 0) + 1

    queue = [sid for sid, deg in in_degree.items() if deg == 0]
    result: list[str] = []

    while queue:
        node = queue.pop(0)
        result.append(node)
        for neighbor in adj.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(nodes):
        raise GraphBuildError("Graph contains a cycle — cannot compute topological order")

    return result

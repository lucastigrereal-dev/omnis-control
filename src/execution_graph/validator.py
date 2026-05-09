"""Execution Graph Validator — structural checks on DAGs."""
from __future__ import annotations


def validate_graph(graph) -> list[str]:
    """Validate an ExecutionGraph structure.

    Returns a list of issue strings. Empty list = valid graph.
    """
    issues: list[str] = []

    node_ids = {n.step_id for n in graph.nodes}

    if not graph.nodes:
        issues.append("Graph has no nodes")
        return issues

    # Check all edge endpoints reference real nodes
    for src, dst in graph.edges:
        if src not in node_ids:
            issues.append(f"Edge source '{src}' not found in nodes")
        if dst not in node_ids:
            issues.append(f"Edge target '{dst}' not found in nodes")

    # Check all depends_on reference real nodes
    for node in graph.nodes:
        for dep in node.depends_on:
            if dep not in node_ids:
                issues.append(f"Step '{node.step_id}' depends on unknown step '{dep}'")

    # Check topological order matches edges
    if graph.edges:
        order_idx = {sid: i for i, sid in enumerate(graph.topological_order)}
        for src, dst in graph.edges:
            if src in order_idx and dst in order_idx:
                if order_idx[src] >= order_idx[dst]:
                    issues.append(
                        f"Edge ({src} -> {dst}) violates topological order"
                    )

    # Check for duplicate step_ids
    seen = set()
    for node in graph.nodes:
        if node.step_id in seen:
            issues.append(f"Duplicate step_id: {node.step_id}")
        seen.add(node.step_id)

    # Check topological order contains all nodes
    top_set = set(graph.topological_order)
    if top_set != node_ids:
        missing = node_ids - top_set
        extra = top_set - node_ids
        if missing:
            issues.append(f"Topological order missing nodes: {missing}")
        if extra:
            issues.append(f"Topological order has unknown nodes: {extra}")

    return issues

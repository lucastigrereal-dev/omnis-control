"""Graph Replay / Resume — retomar ou re-executar runs interrompidos."""
from __future__ import annotations

from src.execution_graph.models import (
    ExecutionGraph,
    StepStatus,
    StepRun,
    _make_run_id,
)
from src.execution_graph.runner import run_graph_dry
from src.execution_graph.store import read_manifest, DEFAULT_STORE_ROOT


def resume_graph_run(run_id: str) -> StepRun | None:
    """Resume a previously failed/paused graph run.

    Loads the stored manifest, rebuilds the graph from snapshot,
    and re-executes only non-DONE steps.
    """
    run_dir = DEFAULT_STORE_ROOT / run_id
    manifest = read_manifest(run_dir)
    if manifest is None:
        return None

    graph_snapshot = manifest.get("graph_snapshot")
    if graph_snapshot is None:
        return None

    graph = ExecutionGraph.from_dict(graph_snapshot)
    step_states = manifest.get("step_states", {})

    # Collect already-done steps
    skip_done = {sid for sid, s in step_states.items() if s == StepStatus.DONE.value}

    # Re-run, skipping done steps, no failure injection
    return run_graph_dry(
        graph,
        skip_done=skip_done,
        include_snapshot=True,
    )


def replay_graph_run(run_id: str) -> StepRun | None:
    """Replay a graph run from scratch.

    Loads the stored manifest, rebuilds the graph from snapshot,
    and re-executes ALL steps fresh.
    """
    run_dir = DEFAULT_STORE_ROOT / run_id
    manifest = read_manifest(run_dir)
    if manifest is None:
        return None

    graph_snapshot = manifest.get("graph_snapshot")
    if graph_snapshot is None:
        return None

    graph = ExecutionGraph.from_dict(graph_snapshot)

    # Re-run everything fresh (no skip, no failure injection)
    return run_graph_dry(
        graph,
        include_snapshot=True,
    )

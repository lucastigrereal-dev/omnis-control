"""Graph Replay / Resume — retomar ou re-executar runs interrompidos com visibility hooks."""
from __future__ import annotations

from src.execution_graph.models import (
    ExecutionGraph,
    StepStatus,
    StepRun,
    _make_run_id,
)
from src.execution_graph.runner import run_graph_dry
from src.execution_graph.store import read_manifest, DEFAULT_STORE_ROOT
from src.execution_graph.events import EventLog, EventType, GraphEvent
from src.execution_graph.shadow import emit_replay_visibility


def resume_graph_run(
    run_id: str,
    event_log: EventLog | None = None,
) -> StepRun | None:
    """Resume a previously failed/paused graph run.

    Loads the stored manifest, rebuilds the graph from snapshot,
    and re-executes only non-DONE steps.

    Args:
        run_id: The graph run ID to resume.
        event_log: Optional EventLog for replay visibility hooks.
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

    skip_done = {sid for sid, s in step_states.items() if s == StepStatus.DONE.value}

    # Emit replay visibility hook
    if event_log is not None:
        emit_replay_visibility(
            event_log=event_log,
            graph_run_id=run_id,
            graph_id=graph.graph_id,
            mode="resume",
            step_states=step_states,
        )

    result = run_graph_dry(
        graph,
        skip_done=skip_done,
        include_snapshot=True,
    )

    # Emit completion
    if event_log is not None:
        event_log.append(GraphEvent(
            event_type=EventType.RESUME_COMPLETED,
            graph_run_id=run_id,
            graph_id=graph.graph_id,
            status=result.status,
            message=f"Resume completed — {len(result.step_states)} steps, status={result.status}",
            metadata={"step_states": result.step_states},
        ))

    return result


def replay_graph_run(
    run_id: str,
    event_log: EventLog | None = None,
) -> StepRun | None:
    """Replay a graph run from scratch.

    Loads the stored manifest, rebuilds the graph from snapshot,
    and re-executes ALL steps fresh.

    Args:
        run_id: The graph run ID to replay.
        event_log: Optional EventLog for replay visibility hooks.
    """
    run_dir = DEFAULT_STORE_ROOT / run_id
    manifest = read_manifest(run_dir)
    if manifest is None:
        return None

    graph_snapshot = manifest.get("graph_snapshot")
    if graph_snapshot is None:
        return None

    graph = ExecutionGraph.from_dict(graph_snapshot)

    # Emit replay visibility hook
    if event_log is not None:
        step_states = manifest.get("step_states", {})
        emit_replay_visibility(
            event_log=event_log,
            graph_run_id=run_id,
            graph_id=graph.graph_id,
            mode="replay",
            step_states=step_states,
        )

    result = run_graph_dry(
        graph,
        include_snapshot=True,
    )

    # Emit completion
    if event_log is not None:
        event_log.append(GraphEvent(
            event_type=EventType.REPLAY_COMPLETED,
            graph_run_id=run_id,
            graph_id=graph.graph_id,
            status=result.status,
            message=f"Replay completed — {len(result.step_states)} steps, status={result.status}",
            metadata={"step_states": result.step_states},
        ))

    return result

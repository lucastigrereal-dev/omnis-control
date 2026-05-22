"""Shadow Mode Orchestrator — gradual dry_run→real transition with per-node control."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.execution_graph.models import (
    ExecutionGraph,
    ShadowConfig,
    StepStatus,
    StepRun,
    StepRunLog,
    RUN_STATUS_SHADOW,
    _make_run_id,
)
from src.execution_graph.events import EventLog, EventType, GraphEvent
from src.execution_graph.runner import run_graph_dry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ShadowRunResult:
    """Result of a shadow mode graph execution."""
    shadow_run: StepRun
    shadow_config: ShadowConfig
    event_log: EventLog
    promoted_nodes: list[str] = field(default_factory=list)

    @property
    def all_done(self) -> bool:
        """True when all steps completed (status is done or shadow with no failures)."""
        if self.shadow_run.status not in ("done", RUN_STATUS_SHADOW):
            return False
        return all(
            s == "done"
            for s in self.shadow_run.step_states.values()
        )

    @property
    def shadow_node_count(self) -> int:
        return sum(
            1 for sid, dry in self.shadow_config.node_dry_run.items()
            if dry and sid not in self.shadow_config.real_nodes
        )


def run_shadow(
    graph: ExecutionGraph,
    config: ShadowConfig | None = None,
    fail_at: str | None = None,
    skip_done: set[str] | None = None,
    run_id: str | None = None,
) -> ShadowRunResult:
    """Execute a graph in shadow mode with per-node dry_run control.

    Shadow mode runs the graph as a dry-run simulation but tracks which
    nodes WOULD have executed for real (dry_run=False). This enables
    gradual transition from full shadow to full real execution.

    Replay visibility hooks are emitted automatically when replay_trace_enabled=True.
    """
    shadow_config = config or ShadowConfig()
    event_log = EventLog()
    promoted_nodes: list[str] = []

    graph_run_id = run_id or _make_run_id()

    # Emit shadow run started
    if shadow_config.replay_trace_enabled:
        event_log.append(GraphEvent(
            event_type=EventType.SHADOW_RUN_STARTED,
            graph_run_id=graph_run_id,
            graph_id=graph.graph_id,
            message=f"Shadow run started — {len(graph.nodes)} nodes, "
                    f"shadow_mode={shadow_config.shadow_mode}",
            metadata={
                "shadow_mode": shadow_config.shadow_mode,
                "real_nodes": sorted(shadow_config.real_nodes),
                "dry_run_map": {
                    sid: dry for sid, dry in shadow_config.node_dry_run.items()
                },
            },
        ))

    # Execute the graph in dry-run mode (always safe)
    shadow_run = run_graph_dry(
        graph,
        fail_at=fail_at,
        skip_done=skip_done,
        run_id=graph_run_id,
        include_snapshot=True,
    )

    skip_set = skip_done or set()

    # Post-process: annotate which steps were shadow vs real
    annotated_logs: list[StepRunLog] = []
    for entry in shadow_run.logs:
        step_id = entry.step_id
        if step_id and step_id not in skip_set and entry.status == StepStatus.DONE.value:
            if shadow_config.is_dry_run(step_id):
                # Node is still in shadow — annotate
                annotated_logs.append(StepRunLog(
                    step_id=step_id,
                    role_id=entry.role_id,
                    status=entry.status,
                    message=f"[SHADOW] {entry.message}",
                    timestamp=entry.timestamp,
                ))
            else:
                # Node is real — mark as promoted
                annotated_logs.append(StepRunLog(
                    step_id=step_id,
                    role_id=entry.role_id,
                    status=entry.status,
                    message=f"[REAL] {entry.message}",
                    timestamp=entry.timestamp,
                ))
        else:
            annotated_logs.append(entry)

    # Build shadow StepRun with annotated logs
    shadow_result = StepRun(
        graph_run_id=shadow_run.graph_run_id,
        graph_id=shadow_run.graph_id,
        request=shadow_run.request,
        status=RUN_STATUS_SHADOW if shadow_config.shadow_mode else shadow_run.status,
        step_states=shadow_run.step_states,
        logs=annotated_logs,
        started_at=shadow_run.started_at,
        finished_at=shadow_run.finished_at,
        graph_snapshot=shadow_run.graph_snapshot,
    )

    # Emit shadow run completed
    remaining = shadow_config.remaining_shadow_nodes(graph)
    if shadow_config.replay_trace_enabled:
        event_log.append(GraphEvent(
            event_type=EventType.SHADOW_RUN_COMPLETED,
            graph_run_id=graph_run_id,
            graph_id=graph.graph_id,
            status=shadow_result.status,
            message=f"Shadow run completed — {len(remaining)} nodes still in shadow, "
                    f"{len(shadow_config.real_nodes)} promoted to real",
            metadata={
                "remaining_shadow_nodes": sorted(remaining),
                "real_nodes": sorted(shadow_config.real_nodes),
                "promoted_this_run": promoted_nodes,
                "status": shadow_result.status,
            },
        ))

    return ShadowRunResult(
        shadow_run=shadow_result,
        shadow_config=shadow_config,
        event_log=event_log,
        promoted_nodes=promoted_nodes,
    )


def promote_node(
    graph: ExecutionGraph,
    config: ShadowConfig,
    step_id: str,
) -> ShadowConfig:
    """Promote a single node from shadow to real execution.

    Returns the updated config. Does not mutate the original.
    """
    if step_id not in graph.node_map:
        raise ValueError(f"Step '{step_id}' not found in graph '{graph.graph_id}'")

    config.promote_to_real(step_id)
    return config


def promote_all_nodes(config: ShadowConfig) -> ShadowConfig:
    """Exit shadow mode — promote all nodes to real execution."""
    config.promote_all()
    return config


def emit_replay_visibility(
    event_log: EventLog,
    graph_run_id: str,
    graph_id: str,
    mode: str,  # "replay" or "resume"
    step_states: dict[str, str],
) -> None:
    """Emit replay/resume visibility events for observability."""
    event_type = (
        EventType.REPLAY_STARTED if mode == "replay"
        else EventType.RESUME_STARTED
    )

    event_log.append(GraphEvent(
        event_type=event_type,
        graph_run_id=graph_run_id,
        graph_id=graph_id,
        message=f"{mode.capitalize()} started — {len(step_states)} steps from previous run",
        metadata={"mode": mode, "step_states": step_states},
    ))

"""Tests for Execution Graph Shadow Mode — gradual dry_run→real transition."""
from __future__ import annotations

import json

from src.execution_graph.models import (
    ExecutionGraph,
    StepNode,
    StepStatus,
    ShadowConfig,
    RUN_STATUS_SHADOW,
)
from src.execution_graph.builder import build_graph
from src.execution_graph.shadow import (
    run_shadow,
    promote_node,
    promote_all_nodes,
    ShadowRunResult,
    emit_replay_visibility,
)
from src.execution_graph.events import EventLog, EventType, GraphEvent
from src.execution_graph.replay import resume_graph_run, replay_graph_run
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad


def _make_graph(request: str = "post de viagem em natal") -> ExecutionGraph:
    squad = compose_squad(request)
    task_plan = decompose_squad(squad)
    return build_graph(squad, task_plan)


class TestShadowConfig:
    def test_default_all_shadow(self):
        cfg = ShadowConfig()
        assert cfg.shadow_mode is True
        assert cfg.is_dry_run("any_step") is True

    def test_promote_single_node(self):
        cfg = ShadowConfig()
        cfg.promote_to_real("step_0")
        assert cfg.is_dry_run("step_0") is False
        assert cfg.is_dry_run("step_1") is True

    def test_promote_all(self):
        cfg = ShadowConfig()
        cfg.promote_all()
        assert cfg.shadow_mode is False

    def test_remaining_shadow_nodes(self):
        graph = _make_graph()
        cfg = ShadowConfig()
        # Promote the first node
        first = graph.topological_order[0]
        cfg.promote_to_real(first)
        remaining = cfg.remaining_shadow_nodes(graph)
        assert first not in remaining
        assert len(remaining) == len(graph.nodes) - 1

    def test_roundtrip(self):
        cfg = ShadowConfig()
        cfg.promote_to_real("step_a")
        cfg.promote_to_real("step_c")
        d = cfg.to_dict()
        restored = ShadowConfig.from_dict(d)
        assert restored.shadow_mode == cfg.shadow_mode
        assert restored.real_nodes == cfg.real_nodes
        assert restored.is_dry_run("step_a") is False
        assert restored.is_dry_run("step_b") is True
        assert restored.is_dry_run("step_c") is False


class TestShadowRun:
    def test_full_shadow_run_succeeds(self):
        graph = _make_graph()
        result = run_shadow(graph)
        assert result.all_done
        assert result.shadow_run.status == RUN_STATUS_SHADOW
        assert len(result.shadow_run.logs) > 0

    def test_shadow_annotates_real_vs_shadow(self):
        graph = _make_graph()
        cfg = ShadowConfig()
        # Promote middle node
        middle = graph.topological_order[len(graph.topological_order) // 2]
        cfg.promote_to_real(middle)
        result = run_shadow(graph, config=cfg)
        messages = [log.message for log in result.shadow_run.logs]
        assert any("[REAL]" in m for m in messages), f"No [REAL] annotation in: {messages}"
        assert any("[SHADOW]" in m for m in messages), f"No [SHADOW] annotation in: {messages}"

    def test_shadow_emits_events(self):
        graph = _make_graph()
        result = run_shadow(graph)
        events = result.event_log.all()
        assert len(events) >= 2
        assert events[0].event_type == EventType.SHADOW_RUN_STARTED
        assert events[-1].event_type == EventType.SHADOW_RUN_COMPLETED

    def test_shadow_failure_propagates(self):
        graph = _make_graph()
        fail_step = graph.topological_order[1]
        result = run_shadow(graph, fail_at=fail_step)
        assert not result.all_done

    def test_shadow_with_all_real(self):
        graph = _make_graph()
        cfg = ShadowConfig()
        for sid in graph.topological_order:
            cfg.promote_to_real(sid)
        result = run_shadow(graph, config=cfg)
        completed = [
            log.message for log in result.shadow_run.logs
            if "completed" in log.message and log.status == StepStatus.DONE.value
        ]
        assert len(completed) > 0
        assert all("[REAL]" in m for m in completed)

    def test_shadow_reports_remaining_nodes(self):
        graph = _make_graph()
        cfg = ShadowConfig()
        first, last = graph.topological_order[0], graph.topological_order[-1]
        cfg.promote_to_real(first)
        cfg.promote_to_real(last)
        remaining = cfg.remaining_shadow_nodes(graph)
        assert first not in remaining
        assert last not in remaining
        assert len(remaining) == len(graph.nodes) - 2

    def test_promote_node_validation(self):
        graph = _make_graph()
        cfg = ShadowConfig()
        first = graph.topological_order[0]
        result = promote_node(graph, cfg, first)
        assert not result.is_dry_run(first)

    def test_promote_invalid_node(self):
        graph = _make_graph()
        cfg = ShadowConfig()
        try:
            promote_node(graph, cfg, "nonexistent_step")
            raise AssertionError("Expected ValueError for nonexistent step")
        except ValueError:
            pass


class TestReplayVisibilityHooks:
    def test_emit_replay_visibility_resume(self):
        log = EventLog()
        emit_replay_visibility(log, "run_1", "graph_1", "resume", {"step_0": "done"})
        events = log.all()
        assert len(events) == 1
        assert events[0].event_type == EventType.RESUME_STARTED
        assert events[0].metadata["mode"] == "resume"

    def test_emit_replay_visibility_replay(self):
        log = EventLog()
        emit_replay_visibility(log, "run_1", "graph_1", "replay", {"step_0": "done"})
        events = log.all()
        assert len(events) == 1
        assert events[0].event_type == EventType.REPLAY_STARTED
        assert events[0].metadata["mode"] == "replay"

    def test_replay_visibility_full_cycle(self):
        graph = _make_graph()
        log = EventLog()
        emit_replay_visibility(log, "run_1", graph.graph_id, "replay", {})
        log.append(GraphEvent(
            event_type=EventType.REPLAY_COMPLETED,
            graph_run_id="run_1",
            graph_id=graph.graph_id,
            status="done",
            message="Replay completed",
        ))
        events = log.all()
        assert events[0].event_type == EventType.REPLAY_STARTED
        assert events[-1].event_type == EventType.REPLAY_COMPLETED


class TestShadowModeIntegration:
    def test_gradual_promotion_workflow(self):
        """Simulate the gradual promotion workflow across multiple runs."""
        graph = _make_graph()
        nodes = graph.topological_order

        # Run 1: all shadow
        cfg = ShadowConfig()
        r1 = run_shadow(graph, config=cfg)
        remaining = r1.shadow_config.remaining_shadow_nodes(graph)
        assert len(remaining) == len(nodes)

        # Run 2: promote first 2 nodes
        cfg.promote_to_real(nodes[0])
        cfg.promote_to_real(nodes[1])
        r2 = run_shadow(graph, config=cfg)
        remaining = r2.shadow_config.remaining_shadow_nodes(graph)
        assert nodes[0] not in remaining
        assert nodes[1] not in remaining

        # Run 3: promote all
        cfg.promote_all()
        remaining = cfg.remaining_shadow_nodes(graph)
        assert remaining == set()

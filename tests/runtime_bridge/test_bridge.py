"""Tests for RuntimeBridge — graph StepRun → queue QueueItem."""
from __future__ import annotations

import pytest

from src.execution_graph.models import (
    ExecutionGraph,
    StepNode,
    StepRun,
    StepRunLog,
    StepStatus,
)
from src.execution_queue.models import (
    QueueItemStatus,
    QueueItem,
    QueueResult,
)
from src.execution_queue.queue import ExecutionQueue
from src.runtime_bridge.bridge import RuntimeBridge, _final_logs
from src.runtime_bridge.models import (
    BridgeResult,
    STATUS_MAP,
    map_step_status,
)
from src.runtime_bridge.errors import BridgeError, BridgeMappingError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_log(step_id: str, status: str, message: str = "") -> StepRunLog:
    return StepRunLog(
        step_id=step_id,
        role_id="qa_auditor",
        status=status,
        message=message or f"Step {step_id} {status}",
        timestamp="2026-05-16T10:00:00Z",
    )


def _make_step_run(graph_run_id: str, graph_id: str, logs: list[StepRunLog],
                   status: str = "done", request: str = "test request") -> StepRun:
    return StepRun(
        graph_run_id=graph_run_id,
        graph_id=graph_id,
        request=request,
        status=status,
        step_states={log.step_id: log.status for log in logs},
        logs=logs,
        started_at="2026-05-16T10:00:00Z",
        finished_at="2026-05-16T10:01:00Z",
    )


def _make_graph(graph_id: str = "g1", request: str = "test") -> ExecutionGraph:
    return ExecutionGraph(
        graph_id=graph_id,
        request=request,
        squad_id="squad_1",
        task_plan_id="tp_1",
        nodes=[
            StepNode(
                step_id="s1", task_id="t1", role_id="r1",
                title="Step 1", description="Desc 1",
                expected_output="Out 1", depends_on=[],
            ),
        ],
        edges=[],
        topological_order=["s1"],
        created_at="2026-05-16T10:00:00Z",
    )


@pytest.fixture
def queue():
    return ExecutionQueue(dry_run=True)


@pytest.fixture
def bridge(queue):
    return RuntimeBridge(queue, dry_run=True)


# ---------------------------------------------------------------------------
# Tests: status mapping
# ---------------------------------------------------------------------------

class TestStatusMapping:
    def test_done_maps_to_ready(self):
        assert map_step_status("done") == QueueItemStatus.READY

    def test_failed_maps_to_blocked(self):
        assert map_step_status("failed") == QueueItemStatus.BLOCKED

    def test_skipped_maps_to_blocked(self):
        assert map_step_status("skipped") == QueueItemStatus.BLOCKED

    def test_running_raises_valueerror(self):
        with pytest.raises(ValueError, match="non-final"):
            map_step_status("running")

    def test_pending_raises_valueerror(self):
        with pytest.raises(ValueError, match="non-final"):
            map_step_status("pending")

    def test_unknown_raises_bridge_mapping_error(self):
        with pytest.raises(BridgeMappingError, match="Cannot map"):
            map_step_status("not_a_real_status")

    def test_status_map_coverage(self):
        """Every final StepStatus has a mapping."""
        final_statuses = {StepStatus.DONE.value, StepStatus.FAILED.value, StepStatus.SKIPPED.value}
        for status in final_statuses:
            assert status in STATUS_MAP, f"Missing mapping for {status}"


# ---------------------------------------------------------------------------
# Tests: _final_logs
# ---------------------------------------------------------------------------

class TestFinalLogs:
    def test_single_done_log(self):
        logs = [_make_log("s1", "done")]
        sr = _make_step_run("gr1", "g1", logs)
        result = _final_logs(sr)
        assert len(result) == 1
        assert result[0].step_id == "s1"

    def test_multiple_logs_per_step_keeps_last(self):
        logs = [
            _make_log("s1", "running", "start"),
            _make_log("s1", "done", "finish"),
        ]
        sr = _make_step_run("gr1", "g1", logs)
        result = _final_logs(sr)
        done_logs = [r for r in result if r.step_id == "s1"]
        assert len(done_logs) == 1
        assert done_logs[0].status == "done"

    def test_mixed_steps(self):
        logs = [
            _make_log("s1", "running"),
            _make_log("s1", "done"),
            _make_log("s2", "running"),
            _make_log("s2", "failed", "error"),
        ]
        sr = _make_step_run("gr1", "g1", logs)
        result = _final_logs(sr)
        result_ids = {r.step_id for r in result}
        assert "s1" in result_ids
        assert "s2" in result_ids


# ---------------------------------------------------------------------------
# Tests: bridge()
# ---------------------------------------------------------------------------

class TestBridgeBasic:
    def test_all_done_steps_become_ready(self, bridge):
        logs = [
            _make_log("s1", "done", "completed"),
            _make_log("s2", "done", "completed"),
            _make_log("s3", "done", "completed"),
        ]
        sr = _make_step_run("gr1", "g1", logs)
        result = bridge.bridge(sr)

        assert result.graph_run_id == "gr1"
        assert result.items_ready == 3
        assert result.items_blocked == 0
        assert len(result.queue_items) == 3
        assert all(it.status == QueueItemStatus.READY for it in result.queue_items)
        assert len(result.mapping) == 3
        assert result.errors == []

    def test_failed_step_becomes_blocked(self, bridge):
        logs = [
            _make_log("s1", "failed", "injected failure"),
        ]
        sr = _make_step_run("gr1", "g1", logs)
        result = bridge.bridge(sr)

        assert result.items_ready == 0
        assert result.items_blocked == 1
        assert result.queue_items[0].status == QueueItemStatus.BLOCKED
        assert "injected failure" in result.queue_items[0].errors[0]

    def test_skipped_step_becomes_blocked(self, bridge):
        logs = [
            _make_log("s1", "skipped", "upstream failed"),
        ]
        sr = _make_step_run("gr1", "g1", logs)
        result = bridge.bridge(sr)

        assert result.queue_items[0].status == QueueItemStatus.BLOCKED
        assert result.items_blocked == 1

    def test_empty_step_run(self, bridge):
        sr = _make_step_run("gr1", "g1", [])
        result = bridge.bridge(sr)
        assert result.queue_items == []
        assert result.mapping == {}
        assert result.items_ready == 0
        assert result.items_blocked == 0

    def test_blocked_step_run(self, bridge):
        graph = _make_graph()
        sr = StepRun.blocked(graph, reason="approval needed")
        result = bridge.bridge(sr)

        assert result.items_blocked == 1
        assert result.queue_items[0].status == QueueItemStatus.BLOCKED
        assert result.queue_items[0].requires_approval is True

    def test_custom_risk_level(self, bridge):
        logs = [_make_log("s1", "done")]
        sr = _make_step_run("gr1", "g1", logs)
        result = bridge.bridge(sr, risk_level="HIGH")
        assert result.queue_items[0].risk_level == "HIGH"

    def test_requires_approval_flag(self, bridge):
        logs = [_make_log("s1", "done")]
        sr = _make_step_run("gr1", "g1", logs)
        result = bridge.bridge(sr, requires_approval=True)
        assert result.queue_items[0].requires_approval is True

    def test_non_final_status_filtered(self, bridge):
        logs = [
            _make_log("s1", "running", "in progress"),
        ]
        sr = _make_step_run("gr1", "g1", logs, status="running")
        result = bridge.bridge(sr)
        assert len(result.queue_items) == 0

    def test_mapping_step_id_to_item_id(self, bridge):
        logs = [
            _make_log("step_a", "done"),
            _make_log("step_b", "done"),
        ]
        sr = _make_step_run("gr1", "g1", logs)
        result = bridge.bridge(sr)

        assert result.mapping["step_a"] == result.queue_items[0].item_id
        assert result.mapping["step_b"] == result.queue_items[1].item_id


# ---------------------------------------------------------------------------
# Tests: bridge_and_validate
# ---------------------------------------------------------------------------

class TestBridgeAndValidate:
    def test_validate_with_dry_run_required(self, bridge, queue):
        logs = [_make_log("s1", "done")]
        sr = _make_step_run("gr1", "g1", logs)
        result = bridge.bridge_and_validate(sr)

        item = result.queue_items[0]
        # dry_run_required=True → queue.validate() → DRY_RUN
        assert item.status == QueueItemStatus.DRY_RUN

    def test_validate_with_approval_required(self, bridge, queue):
        logs = [_make_log("s1", "done")]
        sr = _make_step_run("gr1", "g1", logs)
        result = bridge.bridge_and_validate(sr, requires_approval=True)

        item = result.queue_items[0]
        # requires_approval=True → queue.validate() → WAITING_APPROVAL
        assert item.status == QueueItemStatus.WAITING_APPROVAL

    def test_blocked_items_skipped_in_validate(self, bridge, queue):
        logs = [_make_log("s1", "failed", "error")]
        sr = _make_step_run("gr1", "g1", logs)
        result = bridge.bridge_and_validate(sr)

        item = result.queue_items[0]
        assert item.status == QueueItemStatus.BLOCKED


# ---------------------------------------------------------------------------
# Tests: bridge_and_run
# ---------------------------------------------------------------------------

class TestBridgeAndRun:
    def test_dry_run_does_not_call_queue_run(self, bridge, queue):
        logs = [_make_log("s1", "done")]
        sr = _make_step_run("gr1", "g1", logs)
        result = bridge.bridge_and_run(sr)

        # With dry_run=True, queue.run() should never be called
        # dry_run_required=True → validate → DRY_RUN
        item = result.queue_items[0]
        assert item.status == QueueItemStatus.DRY_RUN

    def test_bridge_and_run_with_real_flag(self, queue):
        bridge_real = RuntimeBridge(queue, dry_run=False)
        logs = [_make_log("s1", "done")]
        sr = _make_step_run("gr1", "g1", logs)
        result = bridge_real.bridge_and_run(sr)

        # dry_run=False on bridge → dry_run_required=False → validate → READY → run → DONE
        item = result.queue_items[0]
        assert item.status == QueueItemStatus.DONE


# ---------------------------------------------------------------------------
# Tests: BridgeResult serialization
# ---------------------------------------------------------------------------

class TestBridgeResultRoundTrip:
    def test_to_dict_and_from_dict(self):
        item = QueueItem(
            item_id="eqi_test",
            contract_id="g1",
            title="test step",
            risk_level="MEDIUM",
            requires_approval=False,
            dry_run_required=True,
            status=QueueItemStatus.READY,
        )
        original = BridgeResult(
            graph_run_id="gr1",
            queue_items=[item],
            mapping={"s1": "eqi_test"},
            items_blocked=0,
            items_ready=1,
            errors=[],
        )

        d = original.to_dict()
        restored = BridgeResult.from_dict(d)

        assert restored.graph_run_id == original.graph_run_id
        assert restored.items_ready == original.items_ready
        assert restored.items_blocked == original.items_blocked
        assert restored.mapping == original.mapping
        assert len(restored.queue_items) == 1
        assert restored.queue_items[0].item_id == item.item_id

    def test_to_dict_empty(self):
        result = BridgeResult(graph_run_id="gr_empty")
        d = result.to_dict()
        restored = BridgeResult.from_dict(d)
        assert restored.queue_items == []
        assert restored.graph_run_id == "gr_empty"

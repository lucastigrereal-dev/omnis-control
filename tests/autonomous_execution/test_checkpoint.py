"""Tests for P23 Checkpoint Manager."""
import pytest

from src.autonomous_execution.checkpoint import CheckpointManager
from src.autonomous_execution.models import (
    ACTION_DELETE,
    ACTION_DEPLOY,
    ACTION_FINANCIAL,
    ACTION_READ,
    ACTION_SEND,
    ACTION_WRITE,
    AutonomousConfig,
    AutonomousResult,
)


class TestCheckpointManager:
    @pytest.fixture
    def cfg(self):
        return AutonomousConfig.new()

    @pytest.fixture
    def mgr(self, cfg):
        return CheckpointManager(cfg)

    def test_is_checkpoint_action_send(self, mgr):
        assert mgr.is_checkpoint_action(ACTION_SEND) is True

    def test_is_checkpoint_action_deploy(self, mgr):
        assert mgr.is_checkpoint_action(ACTION_DEPLOY) is True

    def test_is_checkpoint_action_delete(self, mgr):
        assert mgr.is_checkpoint_action(ACTION_DELETE) is True

    def test_is_checkpoint_action_financial(self, mgr):
        assert mgr.is_checkpoint_action(ACTION_FINANCIAL) is True

    def test_is_checkpoint_action_read(self, mgr):
        assert mgr.is_checkpoint_action(ACTION_READ) is False

    def test_is_checkpoint_action_write(self, mgr):
        assert mgr.is_checkpoint_action(ACTION_WRITE) is False

    def test_is_checkpoint_action_unknown(self, mgr):
        assert mgr.is_checkpoint_action("unknown_action") is False

    def test_request_approval_returns_dict(self, mgr):
        decision = mgr.request_approval("step_1", ACTION_SEND)
        assert decision["step_id"] == "step_1"
        assert decision["action"] == ACTION_SEND
        assert decision["requires_human"] is True
        assert decision["approved"] is False

    def test_request_approval_with_context(self, mgr):
        ctx = {"hotel": "Hotel Teste", "preco": 990}
        decision = mgr.request_approval("step_2", ACTION_FINANCIAL, context=ctx)
        assert decision["context"] == ctx

    def test_get_pending_checkpoints_empty(self, mgr):
        result = AutonomousResult.new(plan_id="plan_abc")
        assert mgr.get_pending_checkpoints(result) == []

    def test_get_pending_checkpoints_after_hits(self, mgr):
        result = AutonomousResult.new(plan_id="plan_abc")
        mgr.record_checkpoint_hit(result, "step_1")
        mgr.record_checkpoint_hit(result, "step_3")
        pending = mgr.get_pending_checkpoints(result)
        assert "step_1" in pending
        assert "step_3" in pending

    def test_record_checkpoint_hit_no_duplicates(self, mgr):
        result = AutonomousResult.new(plan_id="plan_abc")
        mgr.record_checkpoint_hit(result, "step_1")
        mgr.record_checkpoint_hit(result, "step_1")
        assert result.checkpoints_hit == ["step_1"]

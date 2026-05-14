"""Tests for P23 Recovery Manager."""
import pytest

from src.autonomous_execution.errors import RecoveryError
from src.autonomous_execution.models import AutonomousConfig, AutonomousResult, AutonomousState
from src.autonomous_execution.recovery import RecoveryManager


class TestRecoveryManager:
    @pytest.fixture
    def cfg(self):
        return AutonomousConfig.new()

    @pytest.fixture
    def mgr(self, cfg):
        return RecoveryManager(cfg)

    def test_should_retry_first_attempt(self, mgr):
        assert mgr.should_retry("step_1", 1) is True

    def test_should_retry_second_attempt(self, mgr):
        assert mgr.should_retry("step_1", 2) is True

    def test_should_retry_third_attempt_at_max(self, mgr):
        assert mgr.should_retry("step_1", 3) is False

    def test_should_retry_exceeds_max(self, mgr):
        assert mgr.should_retry("step_1", 4) is False

    def test_backoff_first_attempt(self, mgr):
        assert mgr.backoff_seconds(1) == 5

    def test_backoff_second_attempt(self, mgr):
        assert mgr.backoff_seconds(2) == 10

    def test_backoff_third_attempt(self, mgr):
        assert mgr.backoff_seconds(3) == 15

    def test_can_resume_from_checkpoint(self, mgr):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.PAUSED_CHECKPOINT)
        assert mgr.can_resume(result) is True

    def test_can_resume_from_error(self, mgr):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.PAUSED_ERROR)
        assert mgr.can_resume(result) is True

    def test_can_resume_from_timeout(self, mgr):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.PAUSED_TIMEOUT)
        assert mgr.can_resume(result) is True

    def test_can_resume_completed_false(self, mgr):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.COMPLETED)
        assert mgr.can_resume(result) is False

    def test_can_resume_failed_false(self, mgr):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.FAILED)
        assert mgr.can_resume(result) is False

    def test_can_resume_running_false(self, mgr):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.RUNNING)
        assert mgr.can_resume(result) is False

    def test_get_resume_point_returns_steps_executed(self, mgr):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.PAUSED_CHECKPOINT)
        result.steps_executed = 4
        assert mgr.get_resume_point(result) == 4

    def test_get_resume_point_from_terminal_raises(self, mgr):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.COMPLETED)
        with pytest.raises(RecoveryError):
            mgr.get_resume_point(result)

    def test_get_retry_summary_will_retry(self, mgr):
        s = mgr.get_retry_summary("step_1", 1, ValueError("boom"))
        assert s["step_id"] == "step_1"
        assert s["attempt"] == 1
        assert s["will_retry"] is True
        assert s["backoff_seconds"] == 5
        assert "boom" in s["error"]

    def test_get_retry_summary_wont_retry(self, mgr):
        s = mgr.get_retry_summary("step_x", 4)
        assert s["will_retry"] is False
        assert s["backoff_seconds"] == 0

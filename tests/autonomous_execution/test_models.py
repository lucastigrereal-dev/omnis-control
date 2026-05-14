"""Tests for P23 Autonomous Execution models."""
import pytest

from src.autonomous_execution.errors import (
    AutonomousError,
    CheckpointError,
    CircuitBreakerError,
    ExecutionError,
    RecoveryError,
    TimeoutError,
)
from src.autonomous_execution.models import (
    ACTION_CONFIGURE,
    ACTION_DELETE,
    ACTION_DEPLOY,
    ACTION_FINANCIAL,
    ACTION_READ,
    ACTION_SEND,
    ACTION_WRITE,
    CHECKPOINT_ACTIONS,
    PAUSED_STATES,
    TERMINAL_AUTONOMOUS_STATES,
    AutonomousConfig,
    AutonomousResult,
    AutonomousState,
)


# ── CHECKPOINT_ACTIONS ────────────────────────────────────────────────────────

def test_checkpoint_read_is_false():
    assert CHECKPOINT_ACTIONS[ACTION_READ] is False


def test_checkpoint_write_is_false():
    assert CHECKPOINT_ACTIONS[ACTION_WRITE] is False


def test_checkpoint_send_is_true():
    assert CHECKPOINT_ACTIONS[ACTION_SEND] is True


def test_checkpoint_deploy_is_true():
    assert CHECKPOINT_ACTIONS[ACTION_DEPLOY] is True


def test_checkpoint_delete_is_true():
    assert CHECKPOINT_ACTIONS[ACTION_DELETE] is True


def test_checkpoint_financial_is_true():
    assert CHECKPOINT_ACTIONS[ACTION_FINANCIAL] is True


def test_checkpoint_configure_is_false():
    assert CHECKPOINT_ACTIONS[ACTION_CONFIGURE] is False


# ── AutonomousState ───────────────────────────────────────────────────────────

def test_idle_state():
    assert AutonomousState.IDLE.value == "idle"


def test_running_state():
    assert AutonomousState.RUNNING.value == "running"


def test_paused_checkpoint_state():
    assert AutonomousState.PAUSED_CHECKPOINT.value == "paused_checkpoint"


def test_terminal_states_include_completed():
    assert AutonomousState.COMPLETED in TERMINAL_AUTONOMOUS_STATES


def test_terminal_states_include_failed():
    assert AutonomousState.FAILED in TERMINAL_AUTONOMOUS_STATES


def test_terminal_states_include_cancelled():
    assert AutonomousState.CANCELLED in TERMINAL_AUTONOMOUS_STATES


def test_running_not_in_terminal():
    assert AutonomousState.RUNNING not in TERMINAL_AUTONOMOUS_STATES


def test_paused_states_include_checkpoint():
    assert AutonomousState.PAUSED_CHECKPOINT in PAUSED_STATES


def test_paused_states_include_error():
    assert AutonomousState.PAUSED_ERROR in PAUSED_STATES


def test_paused_states_include_timeout():
    assert AutonomousState.PAUSED_TIMEOUT in PAUSED_STATES


# ── AutonomousConfig ──────────────────────────────────────────────────────────

class TestAutonomousConfig:
    def test_new_creates_with_defaults(self):
        cfg = AutonomousConfig.new()
        assert cfg.config_id.startswith("aut_")
        assert len(cfg.config_id) == 12  # "aut_" + 8 hex chars
        assert cfg.max_retries_per_step == 3
        assert cfg.retry_backoff_seconds == 5
        assert cfg.step_timeout_seconds == 300
        assert cfg.mission_timeout_seconds == 1800
        assert cfg.circuit_breaker_threshold == 3
        assert cfg.dry_run is True
        assert cfg.notify_on_checkpoint is True
        assert cfg.notify_on_completion is True

    def test_new_dry_run_false(self):
        cfg = AutonomousConfig.new(dry_run=False)
        assert cfg.dry_run is False

    def test_load_creates_config(self):
        cfg = AutonomousConfig.load()
        assert isinstance(cfg, AutonomousConfig)
        assert cfg.config_id.startswith("aut_")

    def test_is_checkpoint_action_send(self):
        cfg = AutonomousConfig.new()
        assert cfg.is_checkpoint_action(ACTION_SEND) is True

    def test_is_checkpoint_action_read(self):
        cfg = AutonomousConfig.new()
        assert cfg.is_checkpoint_action(ACTION_READ) is False

    def test_is_checkpoint_action_unknown(self):
        cfg = AutonomousConfig.new()
        assert cfg.is_checkpoint_action("unknown_action") is False

    def test_is_checkpoint_action_custom_mapping(self):
        cfg = AutonomousConfig.new()
        cfg.checkpoint_actions = {"my_action": True}
        assert cfg.is_checkpoint_action("my_action") is True

    def test_to_dict(self):
        cfg = AutonomousConfig.new()
        d = cfg.to_dict()
        assert d["config_id"] == cfg.config_id
        assert d["dry_run"] is True
        assert d["max_retries_per_step"] == 3
        assert "step_timeout_seconds" in d
        assert "checkpoint_actions" in d

    def test_from_dict_roundtrip(self):
        cfg = AutonomousConfig.new()
        cfg2 = AutonomousConfig.from_dict(cfg.to_dict())
        assert cfg2.config_id == cfg.config_id
        assert cfg2.max_retries_per_step == cfg.max_retries_per_step
        assert cfg2.dry_run == cfg.dry_run

    def test_custom_values_persist(self):
        cfg = AutonomousConfig(
            config_id="aut_test",
            max_retries_per_step=5,
            step_timeout_seconds=600,
            circuit_breaker_threshold=5,
        )
        assert cfg.max_retries_per_step == 5
        assert cfg.step_timeout_seconds == 600
        assert cfg.circuit_breaker_threshold == 5


# ── AutonomousResult ──────────────────────────────────────────────────────────

class TestAutonomousResult:
    def test_new_creates_idle(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        assert r.run_id.startswith("aut_")
        assert r.plan_id == "plan_abc"
        assert r.status == AutonomousState.IDLE.value
        assert r.steps_executed == 0
        assert r.steps_succeeded == 0
        assert r.steps_failed == 0
        assert r.steps_skipped == 0
        assert r.checkpoints_hit == []
        assert r.errors == []
        assert r.warnings == []
        assert r.trace_events == []

    def test_transition_to_running(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.transition(AutonomousState.RUNNING)
        assert r.status == "running"
        assert r.completed_at is None

    def test_transition_to_completed(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.transition(AutonomousState.COMPLETED)
        assert r.status == "completed"
        assert r.completed_at is not None

    def test_transition_to_failed(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.transition(AutonomousState.FAILED)
        assert r.status == "failed"
        assert r.completed_at is not None

    def test_transition_to_cancelled(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.transition(AutonomousState.CANCELLED)
        assert r.status == "cancelled"
        assert r.completed_at is not None

    def test_transition_to_paused_does_not_set_completed_at(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.transition(AutonomousState.PAUSED_CHECKPOINT)
        assert r.status == "paused_checkpoint"
        assert r.completed_at is None

    def test_is_terminal_completed(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.transition(AutonomousState.COMPLETED)
        assert r.is_terminal is True

    def test_is_terminal_running(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.transition(AutonomousState.RUNNING)
        assert r.is_terminal is False

    def test_is_paused_checkpoint(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.transition(AutonomousState.PAUSED_CHECKPOINT)
        assert r.is_paused is True

    def test_is_paused_running(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.transition(AutonomousState.RUNNING)
        assert r.is_paused is False

    def test_is_running(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.transition(AutonomousState.RUNNING)
        assert r.is_running is True

    def test_is_running_false_when_paused(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.transition(AutonomousState.PAUSED_ERROR)
        assert r.is_running is False

    def test_success_rate_all_success(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.steps_succeeded = 10
        r.steps_failed = 0
        assert r.success_rate == 1.0

    def test_success_rate_all_failed(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.steps_succeeded = 0
        r.steps_failed = 5
        assert r.success_rate == 0.0

    def test_success_rate_mixed(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.steps_succeeded = 7
        r.steps_failed = 3
        assert r.success_rate == 0.7

    def test_success_rate_zero_total(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.steps_succeeded = 0
        r.steps_failed = 0
        assert r.success_rate == 0.0

    def test_to_dict(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.transition(AutonomousState.RUNNING)
        d = r.to_dict()
        assert d["run_id"] == r.run_id
        assert d["plan_id"] == "plan_abc"
        assert d["status"] == "running"
        assert "trace_events" in d

    def test_from_dict_roundtrip(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.steps_succeeded = 5
        r.steps_failed = 2
        r.checkpoints_hit = ["step_1", "step_3"]
        r2 = AutonomousResult.from_dict(r.to_dict())
        assert r2.run_id == r.run_id
        assert r2.status == r.status
        assert r2.steps_succeeded == 5
        assert r2.steps_failed == 2
        assert r2.checkpoints_hit == ["step_1", "step_3"]

    def test_checkpoints_hit_accumulates(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        r.checkpoints_hit.append("checkpoint_1")
        r.checkpoints_hit.append("checkpoint_2")
        assert len(r.checkpoints_hit) == 2

    def test_elapsed_seconds_default_zero(self):
        r = AutonomousResult.new(plan_id="plan_abc")
        assert r.elapsed_seconds == 0.0


# ── Errors ────────────────────────────────────────────────────────────────────

class TestErrors:
    def test_autonomous_error_is_exception(self):
        with pytest.raises(AutonomousError):
            raise AutonomousError("base error")

    def test_checkpoint_error_extends_base(self):
        with pytest.raises(AutonomousError):
            raise CheckpointError("checkpoint required")

    def test_circuit_breaker_error_extends_base(self):
        with pytest.raises(AutonomousError):
            raise CircuitBreakerError("breaker open")

    def test_timeout_error_extends_base(self):
        with pytest.raises(AutonomousError):
            raise TimeoutError("timed out")

    def test_recovery_error_extends_base(self):
        with pytest.raises(AutonomousError):
            raise RecoveryError("recovery failed")

    def test_execution_error_extends_base(self):
        with pytest.raises(AutonomousError):
            raise ExecutionError("execution failed")

    def test_errors_are_exceptions(self):
        for cls in [CheckpointError, CircuitBreakerError, TimeoutError, RecoveryError, ExecutionError]:
            assert issubclass(cls, Exception)

    def test_errors_are_autonomous_errors(self):
        for cls in [CheckpointError, CircuitBreakerError, TimeoutError, RecoveryError, ExecutionError]:
            assert issubclass(cls, AutonomousError)

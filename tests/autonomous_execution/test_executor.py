"""Tests for P23 Autonomous Executor core."""
import pytest

from src.autonomous_execution.errors import (
    CircuitBreakerError,
    ExecutionError,
    TimeoutError,
)
from src.autonomous_execution.executor import AutonomousExecutor
from src.autonomous_execution.models import (
    ACTION_DELETE,
    ACTION_DEPLOY,
    ACTION_FINANCIAL,
    ACTION_READ,
    ACTION_SEND,
    ACTION_WRITE,
    AutonomousConfig,
    AutonomousResult,
    AutonomousState,
)
from src.omnis_supreme.models import SupremePlan, SupremeStep


def _make_plan(steps_spec: list[tuple[str, str]]) -> SupremePlan:
    """Helper: cria plan com steps de (module_ref, operation)."""
    steps = [SupremeStep.new(m, op) for m, op in steps_spec]
    return SupremePlan.new(mission_id="mission_1", steps=steps)


class TestAutonomousExecutorInit:
    def test_creates_with_default_config(self):
        ex = AutonomousExecutor()
        assert ex.config is not None
        assert ex.config.dry_run is True

    def test_creates_with_custom_config(self):
        cfg = AutonomousConfig.new(dry_run=False)
        ex = AutonomousExecutor(cfg)
        assert ex.config.dry_run is False

    def test_has_all_managers(self):
        ex = AutonomousExecutor()
        assert ex.checkpoint_mgr is not None
        assert ex.circuit_breaker is not None
        assert ex.recovery is not None


class TestShouldCheckpoint:
    @pytest.fixture
    def ex(self):
        return AutonomousExecutor()

    def test_send_is_checkpoint(self, ex):
        step = SupremeStep.new("mailgun", ACTION_SEND)
        assert ex.should_checkpoint(step) is True

    def test_deploy_is_checkpoint(self, ex):
        step = SupremeStep.new("vercel", ACTION_DEPLOY)
        assert ex.should_checkpoint(step) is True

    def test_delete_is_checkpoint(self, ex):
        step = SupremeStep.new("supabase", ACTION_DELETE)
        assert ex.should_checkpoint(step) is True

    def test_financial_is_checkpoint(self, ex):
        step = SupremeStep.new("stripe", ACTION_FINANCIAL)
        assert ex.should_checkpoint(step) is True

    def test_read_is_not_checkpoint(self, ex):
        step = SupremeStep.new("akasha", ACTION_READ)
        assert ex.should_checkpoint(step) is False

    def test_write_is_not_checkpoint(self, ex):
        step = SupremeStep.new("gringotts", ACTION_WRITE)
        assert ex.should_checkpoint(step) is False


class TestDryRunExecution:
    @pytest.fixture
    def ex(self):
        return AutonomousExecutor()

    def test_dry_run_completes_all_steps(self, ex):
        plan = _make_plan([
            ("akasha", ACTION_READ),
            ("gringotts", ACTION_WRITE),
            ("akasha", ACTION_READ),
        ])
        result = ex.execute(plan)
        assert result.status == AutonomousState.COMPLETED.value
        assert result.steps_executed == 3
        assert result.steps_succeeded == 3
        assert result.steps_failed == 0
        assert result.elapsed_seconds >= 0.0
        assert result.completed_at is not None

    def test_dry_run_registers_trace_events(self, ex):
        plan = _make_plan([("akasha", ACTION_READ)])
        result = ex.execute(plan)
        assert len(result.trace_events) == 1
        assert result.trace_events[0]["status"] == "success"

    def test_dry_run_simulated_output_in_result(self, ex):
        plan = _make_plan([("akasha", ACTION_READ)])
        result = ex.execute(plan)
        evt = result.trace_events[0]["result"]
        assert evt["dry_run"] is True
        assert evt["status"] == "simulated"

    def test_dry_run_passes_through_checkpoints(self, ex):
        """Em dry_run, checkpoints nao pausam — registram e continuam."""
        plan = _make_plan([
            ("akasha", ACTION_READ),
            ("mailgun", ACTION_SEND),
            ("stripe", ACTION_FINANCIAL),
            ("akasha", ACTION_READ),
        ])
        result = ex.execute(plan)
        assert result.status == AutonomousState.COMPLETED.value
        assert result.steps_executed == 4
        assert result.steps_succeeded == 4
        assert len(result.checkpoints_hit) == 2
        assert "mailgun" not in "".join(result.checkpoints_hit)

    def test_dry_run_empty_plan(self, ex):
        plan = _make_plan([])
        result = ex.execute(plan)
        assert result.status == AutonomousState.COMPLETED.value
        assert result.steps_executed == 0
        assert result.success_rate == 0.0


class TestPauseAtCheckpoint:
    def test_pause_records_checkpoint_and_transitions(self):
        ex = AutonomousExecutor()
        step = SupremeStep.new("mailgun", ACTION_SEND)
        result = AutonomousResult.new(plan_id="plan_abc")
        result = ex.pause_at_checkpoint(step, result)
        assert result.status == AutonomousState.PAUSED_CHECKPOINT.value
        assert "step_1" in result.checkpoints_hit or len(result.checkpoints_hit) > 0


class TestResumeAndCancel:
    @pytest.fixture
    def ex(self):
        return AutonomousExecutor()

    def test_resume_from_paused_checkpoint(self, ex):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.PAUSED_CHECKPOINT)
        assert ex.resume(result) is True
        assert result.status == AutonomousState.RESUMING.value

    def test_resume_from_paused_error(self, ex):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.PAUSED_ERROR)
        assert ex.resume(result) is True

    def test_resume_from_terminal_fails(self, ex):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.COMPLETED)
        assert ex.resume(result) is False

    def test_cancel_transitions_and_resets_breaker(self, ex):
        result = AutonomousResult.new(plan_id="plan_abc")
        ex.circuit_breaker.record_failure("s1")
        ex.cancel(result)
        assert result.status == AutonomousState.CANCELLED.value
        assert ex.circuit_breaker.failure_count == 0


class TestStepRunnerInjection:
    def test_set_and_use_step_runner(self):
        ex = AutonomousExecutor()

        calls = []
        def runner(step, ctx):
            calls.append(step.step_id)
            return {"real": True}

        ex.set_step_runner(runner)
        ex.config.dry_run = False
        plan = _make_plan([("mod_a", ACTION_READ), ("mod_b", ACTION_WRITE)])
        result = ex.execute(plan)
        assert len(calls) == 2
        assert result.steps_succeeded == 2


class TestCircuitBreakerIntegration:
    def test_circuit_breaker_opens_after_consecutive_failures(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.retry_backoff_seconds = 0
        ex = AutonomousExecutor(cfg)
        failures_called = [0]

        def failing_runner(step, ctx):
            failures_called[0] += 1
            raise RuntimeError("fail")

        ex.set_step_runner(failing_runner)
        plan = _make_plan([
            ("mod_a", ACTION_READ),
            ("mod_b", ACTION_READ),
            ("mod_c", ACTION_READ),
            ("mod_d", ACTION_READ),
        ])
        result = ex.execute(plan)
        assert result.status == AutonomousState.PAUSED_ERROR.value
        assert ex.circuit_breaker.is_open is True
        assert "Circuit breaker open" in " ".join(result.errors)

    def test_circuit_breaker_resets_on_success(self, ex=None):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.retry_backoff_seconds = 0
        ex = AutonomousExecutor(cfg)
        call_count = [0]

        def mixed_runner(step, ctx):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise RuntimeError("fail")
            return {"ok": True}

        ex.set_step_runner(mixed_runner)
        plan = _make_plan([
            ("mod_a", ACTION_READ),
            ("mod_b", ACTION_READ),
            ("mod_c", ACTION_READ),
            ("mod_d", ACTION_READ),
            ("mod_e", ACTION_READ),
        ])
        result = ex.execute(plan)
        # After 2 failures, step 3 succeeds resetting counter
        # step 4 and 5 should succeed
        assert result.status == AutonomousState.COMPLETED.value
        assert result.steps_succeeded >= 3


class TestTimeoutHandling:
    def test_mission_timeout_pauses(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.mission_timeout_seconds = 0  # timeout imediato
        ex = AutonomousExecutor(cfg)

        def slow_runner(step, ctx):
            return {"ok": True}

        ex.set_step_runner(slow_runner)
        plan = _make_plan([("mod_a", ACTION_READ)])
        result = ex.execute(plan)
        assert result.status == AutonomousState.PAUSED_TIMEOUT.value


class TestRetryBehavior:
    def test_retry_exhausted_marks_failed_with_execution_error(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.max_retries_per_step = 2
        cfg.retry_backoff_seconds = 0
        ex = AutonomousExecutor(cfg)

        def always_fail(step, ctx):
            raise ValueError("always fail")

        ex.set_step_runner(always_fail)
        plan = _make_plan([("mod_a", ACTION_READ)])
        result = ex.execute(plan)
        assert result.steps_failed >= 1
        assert any("failed after" in e for e in result.errors)

    def test_retry_succeeds_on_second_attempt(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.max_retries_per_step = 3
        cfg.retry_backoff_seconds = 0
        ex = AutonomousExecutor(cfg)
        attempts = [0]

        def flaky_runner(step, ctx):
            attempts[0] += 1
            if attempts[0] < 2:
                raise RuntimeError("flaky")
            return {"ok": True}

        ex.set_step_runner(flaky_runner)
        plan = _make_plan([("mod_a", ACTION_READ)])
        result = ex.execute(plan)
        assert result.steps_succeeded == 1
        assert result.steps_failed == 0


class TestResumeExecution:
    def test_resume_continues_from_paused_state(self):
        """Simula: executa ate checkpoint, depois 'resume' e continua."""
        cfg = AutonomousConfig.new()
        cfg.dry_run = True
        ex = AutonomousExecutor(cfg)

        # Cria plan com checkpoint no meio
        plan = _make_plan([
            ("akasha", ACTION_READ),
            ("mailgun", ACTION_SEND),   # checkpoint
            ("akasha", ACTION_READ),
        ])
        result = ex.execute(plan)
        # Em dry_run, checkpoints registram mas nao pausam
        assert result.status == AutonomousState.COMPLETED.value
        assert len(result.checkpoints_hit) == 1

    def test_non_dry_run_pauses_at_checkpoint(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.retry_backoff_seconds = 0
        ex = AutonomousExecutor(cfg)

        def real_runner(step, ctx):
            return {"real": True}

        ex.set_step_runner(real_runner)
        plan = _make_plan([
            ("akasha", ACTION_READ),
            ("mailgun", ACTION_SEND),  # checkpoint — deve pausar
        ])
        result = ex.execute(plan)
        assert result.status == AutonomousState.PAUSED_CHECKPOINT.value
        assert result.steps_executed == 1
        assert len(result.checkpoints_hit) == 1

    def test_resume_then_execute_remaining(self):
        """Pausa no checkpoint, faz resume, executa o resto."""
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.retry_backoff_seconds = 0
        ex = AutonomousExecutor(cfg)

        executed = []
        def runner(step, ctx):
            executed.append(step.step_id)
            return {"ok": True}

        ex.set_step_runner(runner)

        plan = _make_plan([
            ("akasha", ACTION_READ),
            ("mailgun", ACTION_SEND),   # checkpoint
            ("gringotts", ACTION_WRITE),
        ])
        result = ex.execute(plan)
        assert result.status == AutonomousState.PAUSED_CHECKPOINT.value

        # execute_remaining handles resume + execution from checkpoint onward
        result2 = ex.execute_remaining(result, plan, ctx={})
        assert result2.status == AutonomousState.COMPLETED.value


class TestStepTimeout:
    def test_step_timeout_emits_warning(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.max_retries_per_step = 1  # sem retry
        cfg.retry_backoff_seconds = 0
        cfg.step_timeout_seconds = 0  # timeout imediato
        ex = AutonomousExecutor(cfg)

        def runner(step, ctx):
            return {"ok": True}

        ex.set_step_runner(runner)
        plan = _make_plan([("mod_a", ACTION_READ)])
        result = ex.execute(plan)
        # Step timeout 0 → _execute_single_step sees elapsed >= 0 → timeout
        assert result.steps_failed >= 1
        assert any("timed out" in w.lower() for w in result.warnings)

    def test_mission_timeout_records_warning_message(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.mission_timeout_seconds = 0
        ex = AutonomousExecutor(cfg)

        def runner(step, ctx):
            return {"ok": True}

        ex.set_step_runner(runner)
        plan = _make_plan([("mod_a", ACTION_READ)])
        result = ex.execute(plan)
        assert "Mission timeout" in " ".join(result.warnings)

    def test_retry_exhausted_marks_failed(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.max_retries_per_step = 2
        cfg.retry_backoff_seconds = 0
        ex = AutonomousExecutor(cfg)

        def always_fail(step, ctx):
            raise ValueError("always fail")

        ex.set_step_runner(always_fail)
        plan = _make_plan([("mod_a", ACTION_READ)])
        result = ex.execute(plan)
        assert result.steps_failed >= 1
        assert any("failed after" in e for e in result.errors)

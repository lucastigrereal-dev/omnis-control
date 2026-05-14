"""E2E tests for P23 Autonomous Execution."""
import json
import tempfile
from pathlib import Path

import pytest

from src.autonomous_execution.cli import build_parser, main
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
    steps = [SupremeStep.new(m, op) for m, op in steps_spec]
    return SupremePlan.new(mission_id="e2e_mission", steps=steps)


class TestE2EDryRunFlow:
    def test_full_dry_run_mission_to_completion(self):
        cfg = AutonomousConfig.new(dry_run=True)
        ex = AutonomousExecutor(cfg)
        plan = _make_plan([
            ("akasha", ACTION_READ),
            ("gringotts", ACTION_WRITE),
            ("akasha", ACTION_READ),
            ("gringotts", ACTION_WRITE),
        ])
        result = ex.execute(plan)
        assert result.status == AutonomousState.COMPLETED.value
        assert result.steps_executed == 4
        assert result.steps_succeeded == 4
        assert result.steps_failed == 0

    def test_dry_run_with_all_checkpoint_types(self):
        cfg = AutonomousConfig.new(dry_run=True)
        ex = AutonomousExecutor(cfg)
        plan = _make_plan([
            ("akasha", ACTION_READ),
            ("mailgun", ACTION_SEND),       # checkpoint
            ("vercel", ACTION_DEPLOY),       # checkpoint
            ("supabase", ACTION_DELETE),     # checkpoint
            ("stripe", ACTION_FINANCIAL),   # checkpoint
        ])
        result = ex.execute(plan)
        assert result.status == AutonomousState.COMPLETED.value
        assert len(result.checkpoints_hit) == 4

    def test_dry_run_single_step_mission(self):
        cfg = AutonomousConfig.new(dry_run=True)
        ex = AutonomousExecutor(cfg)
        plan = _make_plan([("akasha", ACTION_READ)])
        result = ex.execute(plan)
        assert result.status == AutonomousState.COMPLETED.value
        assert result.steps_executed == 1
        assert result.success_rate == 1.0


class TestE2ERealExecutionFlow:
    def test_step_fails_circuit_breaker_opens(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.retry_backoff_seconds = 0
        ex = AutonomousExecutor(cfg)

        def failing_runner(step, ctx):
            raise RuntimeError("fail")

        ex.set_step_runner(failing_runner)
        plan = _make_plan([
            ("a", ACTION_READ),
            ("b", ACTION_READ),
            ("c", ACTION_READ),
            ("d", ACTION_READ),
        ])
        result = ex.execute(plan)
        assert result.status == AutonomousState.PAUSED_ERROR.value
        assert ex.circuit_breaker.is_open
        assert result.steps_failed == 3

    def test_checkpoint_pauses_non_dry_run(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.retry_backoff_seconds = 0
        ex = AutonomousExecutor(cfg)

        def runner(step, ctx):
            return {"ok": True}

        ex.set_step_runner(runner)
        plan = _make_plan([
            ("akasha", ACTION_READ),
            ("mailgun", ACTION_SEND),
            ("gringotts", ACTION_WRITE),
        ])
        result = ex.execute(plan)
        assert result.status == AutonomousState.PAUSED_CHECKPOINT.value
        assert result.steps_executed == 1
        assert len(result.checkpoints_hit) == 1


class TestE2EResumeFlow:
    def test_full_resume_after_checkpoint(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.retry_backoff_seconds = 0
        ex = AutonomousExecutor(cfg)

        executed_order = []
        def runner(step, ctx):
            executed_order.append(step.step_id)
            return {"ok": True}

        ex.set_step_runner(runner)
        plan = _make_plan([
            ("akasha", ACTION_READ),
            ("mailgun", ACTION_SEND),
            ("gringotts", ACTION_WRITE),
            ("akasha", ACTION_READ),
        ])
        result = ex.execute(plan)
        assert result.status == AutonomousState.PAUSED_CHECKPOINT.value
        first_run_count = len(executed_order)

        result2 = ex.execute_remaining(result, plan, ctx={})
        assert result2.status == AutonomousState.COMPLETED.value
        # total executed across both runs should be 4
        assert len(executed_order) == 4

    def test_cancel_clears_state(self):
        ex = AutonomousExecutor()
        result = AutonomousResult.new(plan_id="plan_abc")
        ex.circuit_breaker.record_failure("s1")
        ex.circuit_breaker.record_failure("s2")
        ex.cancel(result)
        assert result.status == AutonomousState.CANCELLED.value
        assert ex.circuit_breaker.failure_count == 0
        assert result.completed_at is not None


class TestE2ECLIIntegration:
    def test_cli_run_with_json_files(self):
        plan = _make_plan([("akasha", ACTION_READ), ("gringotts", ACTION_WRITE)])

        with tempfile.TemporaryDirectory() as tmp:
            plan_file = Path(tmp) / "plan.json"
            out_file = Path(tmp) / "result.json"
            plan_file.write_text(json.dumps(plan.to_dict()), encoding="utf-8")

            exit_code = main(["run", str(plan_file), "-o", str(out_file)])
            assert exit_code == 0

            result_data = json.loads(out_file.read_text(encoding="utf-8"))
            assert result_data["status"] == "completed"
            assert result_data["steps_succeeded"] == 2

    def test_cli_status_reads_result(self):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.COMPLETED)
        result.steps_executed = 3

        with tempfile.TemporaryDirectory() as tmp:
            result_file = Path(tmp) / "result.json"
            result_file.write_text(json.dumps(result.to_dict()), encoding="utf-8")

            exit_code = main(["status", str(result_file)])
            assert exit_code == 0

    def test_cli_cancel_updates_result(self):
        result = AutonomousResult.new(plan_id="plan_abc")
        result.transition(AutonomousState.RUNNING)

        with tempfile.TemporaryDirectory() as tmp:
            result_file = Path(tmp) / "result.json"
            result_file.write_text(json.dumps(result.to_dict()), encoding="utf-8")

            exit_code = main(["cancel", str(result_file)])
            assert exit_code == 0

    def test_cli_no_command_prints_help(self):
        exit_code = main([])
        assert exit_code == 1


class TestE2EErrorRecovery:
    def test_retry_then_fail_flow(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.max_retries_per_step = 3
        cfg.retry_backoff_seconds = 0
        ex = AutonomousExecutor(cfg)

        def always_fail(step, ctx):
            raise ValueError("fail")

        ex.set_step_runner(always_fail)
        plan = _make_plan([("mod_a", ACTION_READ)])
        result = ex.execute(plan)
        assert result.steps_failed == 1
        assert any("failed after" in e for e in result.errors)

    def test_partial_success_then_failure(self):
        cfg = AutonomousConfig.new()
        cfg.dry_run = False
        cfg.max_retries_per_step = 1  # sem retry
        cfg.retry_backoff_seconds = 0
        ex = AutonomousExecutor(cfg)

        fail_step_id = None
        def mixed_runner(step, ctx):
            nonlocal fail_step_id
            if fail_step_id is None:
                fail_step_id = step.step_id  # first step fails
                raise RuntimeError("fail on first")
            return {"ok": True}

        ex.set_step_runner(mixed_runner)
        plan = _make_plan([
            ("a", ACTION_READ),
            ("b", ACTION_WRITE),
            ("c", ACTION_READ),
            ("d", ACTION_WRITE),
            ("e", ACTION_READ),
        ])
        result = ex.execute(plan)
        assert result.steps_succeeded >= 4
        assert result.steps_failed >= 1

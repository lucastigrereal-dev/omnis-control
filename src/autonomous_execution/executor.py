"""P23 Autonomous Execution — Autonomous Executor."""
from __future__ import annotations

import time
from typing import Callable, Optional

from src.autonomous_execution.checkpoint import CheckpointManager
from src.autonomous_execution.circuit_breaker import CircuitBreaker
from src.autonomous_execution.errors import (
    CheckpointError,
    CircuitBreakerError,
    ExecutionError,
    TimeoutError,
)
from src.autonomous_execution.models import (
    AutonomousConfig,
    AutonomousResult,
    AutonomousState,
)
from src.autonomous_execution.recovery import RecoveryManager
from src.omnis_supreme.models import SupremePlan, SupremeStep


class AutonomousExecutor:
    """Executor autonomo de missoes Supreme."""

    def __init__(self, config: Optional[AutonomousConfig] = None) -> None:
        self.config = config or AutonomousConfig.new()
        self.checkpoint_mgr = CheckpointManager(self.config)
        self.circuit_breaker = CircuitBreaker(self.config.circuit_breaker_threshold)
        self.recovery = RecoveryManager(self.config)
        self._step_runner: Optional[Callable[[SupremeStep, dict], dict]] = None

    def set_step_runner(self, runner: Callable[[SupremeStep, dict], dict]) -> None:
        """Injeta funcao que executa um step real (adapter pattern)."""
        self._step_runner = runner

    def execute(self, plan: SupremePlan, context: Optional[dict] = None,
                approved_step_ids: Optional[set[str]] = None) -> AutonomousResult:
        """Executa plano autonomamente, parando apenas em checkpoints."""
        ctx = dict(context or {})
        approved = approved_step_ids or set()
        result = AutonomousResult.new(plan_id=plan.plan_id)
        result.transition(AutonomousState.RUNNING)
        start_time = time.monotonic()

        for i, step in enumerate(plan.steps):
            result.current_step_id = step.step_id

            # Timeout de missao
            elapsed = time.monotonic() - start_time
            if elapsed >= self.config.mission_timeout_seconds:
                result.transition(AutonomousState.PAUSED_TIMEOUT)
                result.elapsed_seconds = round(elapsed, 2)
                result.warnings.append(f"Mission timeout at step {step.step_id}")
                return result

            # Checkpoint gate
            if self.should_checkpoint(step) and step.step_id not in approved:
                self.checkpoint_mgr.record_checkpoint_hit(result, step.step_id)
                if not self.config.dry_run:
                    result.transition(AutonomousState.PAUSED_CHECKPOINT)
                    result.elapsed_seconds = round(time.monotonic() - start_time, 2)
                    return result

            # Executar step com retry
            try:
                step_result = self._execute_step_with_retry(step, ctx, start_time)
                ctx[step.step_id] = step_result
                result.steps_executed += 1
                result.steps_succeeded += 1
                self.circuit_breaker.record_success(step.step_id)
                result.trace_events.append({
                    "step_id": step.step_id,
                    "status": "success",
                    "result": step_result,
                })

            except TimeoutError as e:
                result.steps_executed += 1
                result.steps_failed += 1
                result.warnings.append(f"Step {step.step_id} timed out: {e}")
                self.circuit_breaker.record_failure(step.step_id)
                result.trace_events.append({
                    "step_id": step.step_id,
                    "status": "timeout",
                })
                if self.circuit_breaker.is_open:
                    result.transition(AutonomousState.PAUSED_ERROR)
                    result.errors.append(f"Circuit breaker open after step {step.step_id}")
                    result.elapsed_seconds = round(time.monotonic() - start_time, 2)
                    return result

            except Exception as e:
                result.steps_executed += 1
                result.steps_failed += 1
                result.errors.append(str(e))
                self.circuit_breaker.record_failure(step.step_id)
                result.trace_events.append({
                    "step_id": step.step_id,
                    "status": "failed",
                    "error": str(e),
                })
                if self.circuit_breaker.is_open:
                    result.transition(AutonomousState.PAUSED_ERROR)
                    result.errors.append(f"Circuit breaker open after step {step.step_id}")
                    result.elapsed_seconds = round(time.monotonic() - start_time, 2)
                    return result

        result.transition(AutonomousState.COMPLETED)
        result.elapsed_seconds = round(time.monotonic() - start_time, 2)
        result.resume_possible = False
        return result

    def _execute_step_with_retry(self, step: SupremeStep, context: dict, start_time: float) -> dict:
        """Executa um step com retry e timeout."""
        last_error = None
        for attempt in range(1, self.config.max_retries_per_step + 1):
            try:
                result = self._execute_single_step(step, context, start_time)
                return result
            except TimeoutError:
                raise
            except Exception as e:
                last_error = e
                if not self.recovery.should_retry(step.step_id, attempt, e):
                    raise ExecutionError(
                        f"Step {step.step_id} failed after {attempt} attempts: {e}"
                    ) from e
                backoff = self.recovery.backoff_seconds(attempt)
                if backoff > 0:
                    time.sleep(min(backoff, 30))
        raise ExecutionError(
            f"Step {step.step_id} failed after {self.config.max_retries_per_step} attempts: {last_error}"
        )

    def _execute_single_step(self, step: SupremeStep, context: dict, start_time: float) -> dict:
        """Executa um unico step com checagem de timeout."""
        elapsed = time.monotonic() - start_time
        if elapsed >= self.config.step_timeout_seconds:
            raise TimeoutError(f"Step {step.step_id} timeout ({self.config.step_timeout_seconds}s)")

        if self.config.dry_run or self._step_runner is None:
            return self._simulate_step(step, context)

        try:
            return self._step_runner(step, context)
        except Exception:
            raise

    def _simulate_step(self, step: SupremeStep, context: dict) -> dict:
        """Simula execucao de step (dry-run)."""
        return {
            "step_id": step.step_id,
            "module_ref": step.module_ref,
            "operation": step.operation,
            "status": "simulated",
            "dry_run": True,
            "output": f"[DRY-RUN] {step.module_ref}.{step.operation}() — simulado",
        }

    def should_checkpoint(self, step: SupremeStep) -> bool:
        """Verifica se step requer parada para aprovacao."""
        return self.checkpoint_mgr.is_checkpoint_action(step.operation)

    def pause_at_checkpoint(self, step: SupremeStep, result: AutonomousResult) -> AutonomousResult:
        """Pausa execucao em gate critico."""
        self.checkpoint_mgr.record_checkpoint_hit(result, step.step_id)
        result.transition(AutonomousState.PAUSED_CHECKPOINT)
        return result

    def resume(self, result: AutonomousResult) -> bool:
        """Verifica se pode retomar execucao de um resultado pausado."""
        if not self.recovery.can_resume(result):
            return False
        result.transition(AutonomousState.RESUMING)
        return True

    def cancel(self, result: AutonomousResult) -> None:
        """Cancela execucao em andamento."""
        result.transition(AutonomousState.CANCELLED)
        self.circuit_breaker.reset()

    def execute_remaining(self, result: AutonomousResult, plan: SupremePlan, ctx: dict) -> AutonomousResult:
        """Executa steps restantes apos resume de checkpoint."""
        if not self.recovery.can_resume(result):
            return result
        resume_idx = self.recovery.get_resume_point(result)
        result.transition(AutonomousState.RESUMING)

        remaining_steps = plan.steps[resume_idx:]
        if not remaining_steps:
            result.transition(AutonomousState.COMPLETED)
            return result

        first_step = remaining_steps[0]
        approved = {first_step.step_id} if self.should_checkpoint(first_step) else set()

        sub_plan = SupremePlan(
            plan_id=plan.plan_id,
            mission_id=plan.mission_id,
            steps=list(remaining_steps),
            dry_run=plan.dry_run,
        )
        return self.execute(sub_plan, context=ctx, approved_step_ids=approved)

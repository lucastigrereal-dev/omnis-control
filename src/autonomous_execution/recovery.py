"""P23 Autonomous Execution — Recovery Manager."""
from __future__ import annotations

from typing import Optional

from src.autonomous_execution.models import AutonomousConfig, AutonomousResult, AutonomousState
from src.autonomous_execution.errors import RecoveryError


class RecoveryManager:
    """Gerencia retry, resume e recuperacao de execucao autonoma."""

    def __init__(self, config: AutonomousConfig) -> None:
        self.config = config

    def should_retry(self, step_id: str, attempt: int, error: Optional[Exception] = None) -> bool:
        """Decide se um step deve ser retentado. True = retry, False = abort."""
        if attempt >= self.config.max_retries_per_step:
            return False
        return True

    def backoff_seconds(self, attempt: int) -> int:
        """Calcula tempo de backoff para retry."""
        return self.config.retry_backoff_seconds * attempt

    def can_resume(self, result: AutonomousResult) -> bool:
        """Verifica se execucao pode ser retomada."""
        if result.is_terminal:
            return False
        if result.status in {
            AutonomousState.PAUSED_CHECKPOINT.value,
            AutonomousState.PAUSED_ERROR.value,
            AutonomousState.PAUSED_TIMEOUT.value,
        }:
            return True
        return False

    def get_resume_point(self, result: AutonomousResult) -> int:
        """Retorna index do step onde retomar (0-based)."""
        if not self.can_resume(result):
            raise RecoveryError(f"Cannot resume from status '{result.status}'")
        return result.steps_executed

    def get_retry_summary(self, step_id: str, attempt: int, error: Optional[Exception] = None) -> dict:
        return {
            "step_id": step_id,
            "attempt": attempt,
            "max_retries": self.config.max_retries_per_step,
            "will_retry": self.should_retry(step_id, attempt, error),
            "backoff_seconds": self.backoff_seconds(attempt) if self.should_retry(step_id, attempt) else 0,
            "error": str(error) if error else None,
        }

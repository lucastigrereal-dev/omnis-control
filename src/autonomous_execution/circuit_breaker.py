"""P23 Autonomous Execution — Circuit Breaker."""
from __future__ import annotations


class CircuitBreaker:
    """Detecta padroes de falha e decide pausar execucao autonoma."""

    def __init__(self, threshold: int = 3) -> None:
        self.threshold = threshold
        self._failure_count = 0
        self._last_failed_step_id: str | None = None
        self._failure_history: list[str] = []

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def is_open(self) -> bool:
        """True se threshold de falhas consecutivas foi atingido."""
        return self._failure_count >= self.threshold

    def record_failure(self, step_id: str) -> None:
        """Registra falha de um step."""
        self._failure_count += 1
        self._last_failed_step_id = step_id
        self._failure_history.append(step_id)

    def record_success(self, step_id: str) -> None:
        """Registra sucesso e reseta contador de falhas consecutivas."""
        self._failure_count = 0
        self._last_failed_step_id = None

    def reset(self) -> None:
        """Reseta completamente o circuit breaker."""
        self._failure_count = 0
        self._last_failed_step_id = None
        self._failure_history = []

    def status(self) -> dict:
        return {
            "failure_count": self._failure_count,
            "threshold": self.threshold,
            "is_open": self.is_open,
            "last_failed_step_id": self._last_failed_step_id,
            "failure_history": list(self._failure_history),
        }

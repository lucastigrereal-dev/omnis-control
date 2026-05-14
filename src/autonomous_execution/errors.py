"""P23 Autonomous Execution errors."""


class AutonomousError(Exception):
    """Base error for P23 Autonomous Execution."""


class CheckpointError(AutonomousError):
    """Erro em checkpoint gate — acao requer aprovacao."""


class CircuitBreakerError(AutonomousError):
    """Circuit breaker aberto — muitas falhas consecutivas."""


class TimeoutError(AutonomousError):
    """Timeout de step ou missao."""


class RecoveryError(AutonomousError):
    """Falha na recuperacao de execucao."""


class ExecutionError(AutonomousError):
    """Falha na execucao de step."""

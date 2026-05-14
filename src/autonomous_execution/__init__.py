"""P23 Autonomous Execution — supervised autonomous mission runner."""
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
from src.autonomous_execution.executor import AutonomousExecutor
from src.autonomous_execution.checkpoint import CheckpointManager
from src.autonomous_execution.circuit_breaker import CircuitBreaker
from src.autonomous_execution.recovery import RecoveryManager
from src.autonomous_execution.errors import (
    AutonomousError,
    CheckpointError,
    CircuitBreakerError,
    ExecutionError,
    RecoveryError,
    TimeoutError,
)

__all__ = [
    # Models
    "AutonomousConfig",
    "AutonomousResult",
    "AutonomousState",
    # Actions
    "ACTION_READ",
    "ACTION_WRITE",
    "ACTION_SEND",
    "ACTION_DEPLOY",
    "ACTION_DELETE",
    "ACTION_FINANCIAL",
    "ACTION_CONFIGURE",
    # Collections
    "CHECKPOINT_ACTIONS",
    "PAUSED_STATES",
    "TERMINAL_AUTONOMOUS_STATES",
    # Core
    "AutonomousExecutor",
    "CheckpointManager",
    "CircuitBreaker",
    "RecoveryManager",
    # Errors
    "AutonomousError",
    "CheckpointError",
    "CircuitBreakerError",
    "ExecutionError",
    "RecoveryError",
    "TimeoutError",
]

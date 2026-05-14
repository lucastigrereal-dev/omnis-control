"""P23 Autonomous Execution — Checkpoint Manager."""
from __future__ import annotations

from typing import Optional

from src.autonomous_execution.models import CHECKPOINT_ACTIONS, AutonomousConfig, AutonomousResult


class CheckpointManager:
    """Gerencia gates de aprovacao durante execucao autonoma."""

    def __init__(self, config: AutonomousConfig) -> None:
        self.config = config

    def is_checkpoint_action(self, action: str) -> bool:
        """Verifica se uma action requer parada para aprovacao."""
        return self.config.checkpoint_actions.get(action, False)

    def request_approval(self, step_id: str, action: str, context: Optional[dict] = None) -> dict:
        """Gera um pedido de aprovacao para um step critico."""
        return {
            "step_id": step_id,
            "action": action,
            "reason": f"Acao '{action}' requer aprovacao do operador (checkpoint gate)",
            "context": context or {},
            "requires_human": True,
            "approved": False,
        }

    def get_pending_checkpoints(self, result: AutonomousResult) -> list[str]:
        """Retorna lista de step_ids que pararam em checkpoint."""
        return list(result.checkpoints_hit)

    def record_checkpoint_hit(self, result: AutonomousResult, step_id: str) -> None:
        """Registra que um step atingiu checkpoint."""
        if step_id not in result.checkpoints_hit:
            result.checkpoints_hit.append(step_id)

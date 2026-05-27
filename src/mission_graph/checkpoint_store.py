"""CheckpointStore — adapter entre MissionGraphState e JsonlRepository."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.missions.repository import JsonlRepository
from src.mission_graph.mission_state import MissionGraphState


class CheckpointStore:
    """Persiste e recupera checkpoints do grafo usando JsonlRepository.

    MissionGraphState é um TypedDict (não Pydantic), portanto não pode ser
    passado diretamente para JsonlRepository.save_checkpoint() que espera
    TaskState.  Por isso escrevemos o JSON diretamente no mesmo diretório e
    formato que o repositório usa, garantindo compatibilidade total com
    get_checkpoint() e get_latest_checkpoint().
    """

    def __init__(self, base_dir: Optional[str] = None) -> None:
        self._repo = JsonlRepository(base_dir=base_dir)
        # checkpoints_dir é o mesmo que o repo usa
        self._checkpoints_dir = self._repo.checkpoints_dir

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, state: MissionGraphState) -> str:
        """Persiste state atual. Retorna checkpoint_id."""
        checkpoint_id = str(uuid.uuid4())[:8]
        mission_id = state["mission_id"]

        ckpt_dir = self._checkpoints_dir / mission_id
        ckpt_dir.mkdir(parents=True, exist_ok=True)

        # Serializa MissionGraphState como payload — valores que não são
        # JSON-natively serializable (ex. dicts nested) são convertidos
        # pelo json.dumps padrão.
        payload: Dict[str, Any] = dict(state)

        data = {
            "checkpoint_id": checkpoint_id,
            "mission_id": mission_id,
            "state": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        ckpt_path = ckpt_dir / f"{checkpoint_id}.json"
        ckpt_path.write_text(
            json.dumps(data, ensure_ascii=True, separators=(",", ":")),
            encoding="utf-8",
        )
        return checkpoint_id

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def load(
        self,
        mission_id: str,
        checkpoint_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Carrega checkpoint.

        Se checkpoint_id=None, retorna o mais recente (por created_at).
        Retorna None se não existir.
        """
        if checkpoint_id:
            return self._repo.get_checkpoint(mission_id, checkpoint_id)
        return self._repo.get_latest_checkpoint(mission_id)

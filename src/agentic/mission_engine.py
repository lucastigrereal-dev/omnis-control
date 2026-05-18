"""MissionEngine — cria ID, pasta, contrato e gerencia ciclo de vida da missão."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


MISSION_STATUS_OPEN = "open"
MISSION_STATUS_CLOSED = "closed"

MISSION_SUBDIRS = ["05_outputs", "06_exports", "07_approval", "08_logs"]

BASE = Path(__file__).resolve().parent.parent.parent
MISSIONS_ROOT = BASE / "missions"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


@dataclass
class MissionContract:
    mission_id: str
    timestamp: str
    status: str
    setor: str
    objetivo: str
    criado_por: str
    closed_at: Optional[str] = None
    mission_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "timestamp": self.timestamp,
            "status": self.status,
            "setor": self.setor,
            "objetivo": self.objetivo,
            "criado_por": self.criado_por,
            "closed_at": self.closed_at,
            "mission_path": self.mission_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MissionContract":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class MissionEngine:
    """Gerencia o ciclo de vida de uma missão no filesystem local."""

    def __init__(self, missions_root: Optional[Path] = None) -> None:
        self.missions_root = Path(missions_root) if missions_root else MISSIONS_ROOT

    def open_mission(
        self,
        objetivo: str,
        setor: str = "general",
        criado_por: str = "OMNIS",
    ) -> MissionContract:
        """Abre uma nova missão: gera ID, cria pastas, escreve mission_contract.json."""
        mission_id = self._generate_id()
        mission_path = self.missions_root / mission_id
        self._create_structure(mission_path)

        contract = MissionContract(
            mission_id=mission_id,
            timestamp=_now_iso(),
            status=MISSION_STATUS_OPEN,
            setor=setor,
            objetivo=objetivo,
            criado_por=criado_por,
            mission_path=str(mission_path.resolve()),
        )

        self._write_contract(mission_path, contract)
        return contract

    def close_mission(self, mission_id: str) -> Optional[MissionContract]:
        """Fecha uma missão existente: atualiza status=closed e closed_at."""
        mission_path = self.missions_root / mission_id
        contract_path = mission_path / "mission_contract.json"

        if not contract_path.exists():
            return None

        contract = self._read_contract(mission_path)
        if contract is None:
            return None

        contract.status = MISSION_STATUS_CLOSED
        contract.closed_at = _now_iso()
        self._write_contract(mission_path, contract)
        return contract

    def get_mission(self, mission_id: str) -> Optional[MissionContract]:
        """Retorna o contrato de uma missão existente."""
        mission_path = self.missions_root / mission_id
        return self._read_contract(mission_path)

    def _generate_id(self) -> str:
        today = _today_str()
        self.missions_root.mkdir(parents=True, exist_ok=True)
        existing = sorted(self.missions_root.glob(f"MIS-{today}-*"))
        next_num = len(existing) + 1
        return f"MIS-{today}-{next_num:03d}"

    def _create_structure(self, mission_path: Path) -> None:
        mission_path.mkdir(parents=True, exist_ok=True)
        for subdir in MISSION_SUBDIRS:
            (mission_path / subdir).mkdir(exist_ok=True)

    def _write_contract(self, mission_path: Path, contract: MissionContract) -> None:
        contract_path = mission_path / "mission_contract.json"
        contract_path.write_text(
            json.dumps(contract.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _read_contract(self, mission_path: Path) -> Optional[MissionContract]:
        contract_path = mission_path / "mission_contract.json"
        if not contract_path.exists():
            return None
        try:
            data = json.loads(contract_path.read_text(encoding="utf-8"))
            return MissionContract.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

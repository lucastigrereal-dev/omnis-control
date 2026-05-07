"""Mission Repository — ABC + JsonlRepository file-based MVP."""
from __future__ import annotations

import hashlib
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.missions.models import MissionContract
from src.missions.events import EventEnvelope, EventType
from src.missions.state import TaskState, project_from_events
from src.missions.state_machine import MissionStatus


class ContractTamperedError(Exception):
    """Hash do contract não confere com .hash file."""


class SequenceGapError(Exception):
    """Gap na sequência de eventos — evento rejeitado."""


class MissionRepository(ABC):
    """Interface abstrata para storage de missions."""

    @abstractmethod
    def save_contract(self, contract: MissionContract) -> str:
        """Persiste contract + .hash. Retorna content_hash."""

    @abstractmethod
    def get_contract(self, mission_id: str) -> MissionContract:
        """Carrega contract e verifica hash."""

    @abstractmethod
    def append_event(self, event: EventEnvelope) -> EventEnvelope:
        """Append event com cálculo de cumulative + validação de sequence."""

    @abstractmethod
    def get_events(self, mission_id: str) -> List[EventEnvelope]:
        """Retorna eventos ordenados por sequence."""

    @abstractmethod
    def list_missions(self, status: Optional[str] = None) -> List[TaskState]:
        """Lista todas as missions (com projeção)."""

    @abstractmethod
    def project(self, mission_id: str) -> TaskState:
        """Projeta TaskState atual."""


class JsonlRepository(MissionRepository):
    """Storage file-based: JSON contracts + JSONL events + hash verification."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is None:
            base_dir = os.path.expanduser("~/omnis-control/data/missions")
        self.base_dir = Path(base_dir)
        self.contracts_dir = self.base_dir / "contracts"
        self.events_dir = self.base_dir / "events"
        self.index_path = self.base_dir / "index.jsonl"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self.contracts_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def save_contract(self, contract: MissionContract) -> str:
        mission_id = contract.content_hash()
        canonical = contract.canonical_json()

        contract_path = self.contracts_dir / f"{mission_id}.json"
        hash_path = self.contracts_dir / f"{mission_id}.hash"

        contract_path.write_text(canonical, encoding="utf-8")

        file_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        hash_data = {"algorithm": "sha256", "hash": file_hash}
        hash_path.write_text(
            json.dumps(hash_data, ensure_ascii=True, separators=(",", ":")),
            encoding="utf-8",
        )

        # Append to index
        entry = {
            "mission_id": mission_id,
            "title": contract.title,
            "sector": contract.sector.value,
            "status": "draft",
            "created_at": contract.created_at.isoformat() if hasattr(contract.created_at, "isoformat") else str(contract.created_at),
        }
        with open(self.index_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True, separators=(",", ":")) + "\n")

        return mission_id

    def get_contract(self, mission_id: str) -> MissionContract:
        contract_path = self.contracts_dir / f"{mission_id}.json"
        hash_path = self.contracts_dir / f"{mission_id}.hash"

        if not contract_path.exists():
            raise FileNotFoundError(f"Contract não encontrado: {mission_id}")

        raw = contract_path.read_text(encoding="utf-8")
        actual_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        if hash_path.exists():
            stored = json.loads(hash_path.read_text(encoding="utf-8"))
            if stored.get("hash") != actual_hash:
                raise ContractTamperedError(
                    f"Hash mismatch para {mission_id}: esperado {stored.get('hash')}, atual {actual_hash}"
                )

        data = json.loads(raw)
        return MissionContract(**data)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _events_path(self, mission_id: str) -> Path:
        return self.events_dir / f"{mission_id}.jsonl"

    def _read_last_event(self, mission_id: str) -> Optional[EventEnvelope]:
        path = self._events_path(mission_id)
        if not path.exists():
            return None
        last_line = ""
        with open(path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    last_line = stripped
        return EventEnvelope.from_jsonl(last_line) if last_line else None

    def append_event(self, event: EventEnvelope) -> EventEnvelope:
        path = self._events_path(event.mission_id)
        last = self._read_last_event(event.mission_id)

        # Sequence validation
        if last is None:
            expected_seq = 1
        else:
            expected_seq = last.sequence + 1

        if event.sequence == 0:
            sequence = expected_seq
        elif event.sequence != expected_seq:
            raise SequenceGapError(
                f"Gap de sequência: esperado {expected_seq}, recebido {event.sequence}"
            )
        else:
            sequence = event.sequence

        # Cumulative calculation
        prev_tokens = last.cumulative_tokens if last else 0
        prev_cost = last.cumulative_cost_usd if last else 0
        cumulative_tokens = prev_tokens + event.delta_tokens
        cumulative_cost_usd = prev_cost + event.delta_cost_usd

        # Rebuild with computed values
        finalized = EventEnvelope(
            mission_id=event.mission_id,
            event_type=event.event_type,
            sequence=sequence,
            actor=event.actor,
            actor_detail=event.actor_detail,
            payload=event.payload,
            delta_tokens=event.delta_tokens,
            delta_cost_usd=event.delta_cost_usd,
            cumulative_tokens=cumulative_tokens,
            cumulative_cost_usd=cumulative_cost_usd,
            timestamp=event.timestamp,
            idempotency_key=event.idempotency_key,
        )

        with open(path, "a", encoding="utf-8") as f:
            f.write(finalized.to_jsonl() + "\n")

        # Update index
        self._update_index_status(event.mission_id, finalized)

        return finalized

    def get_events(self, mission_id: str) -> List[EventEnvelope]:
        path = self._events_path(mission_id)
        if not path.exists():
            return []
        events: List[EventEnvelope] = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    events.append(EventEnvelope.from_jsonl(stripped))
        return events

    # ------------------------------------------------------------------
    # Projection
    # ------------------------------------------------------------------

    def project(self, mission_id: str) -> TaskState:
        contract = self.get_contract(mission_id)
        events = self.get_events(mission_id)
        return project_from_events(contract, events)

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def _update_index_status(self, mission_id: str, event: EventEnvelope) -> None:
        """Atualiza status no index baseado no evento mais recente."""
        status_map: dict[str, str] = {
            "mission_started": "running",
            "mission_completed": "completed",
            "mission_failed": "failed",
            "mission_cancelled": "cancelled",
            "approval_requested": "waiting_approval",
            "budget_exceeded": "waiting_approval",
            "mission_paused": "paused",
            "mission_resumed": "running",
            "approval_granted": "running",
        }
        new_status = status_map.get(event.event_type)
        if new_status is None:
            return

        if not self.index_path.exists():
            return

        lines = []
        updated = False
        with open(self.index_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entry = json.loads(stripped)
                except json.JSONDecodeError:
                    lines.append(stripped)
                    continue
                if entry.get("mission_id") == mission_id:
                    entry["status"] = new_status
                    updated = True
                lines.append(json.dumps(entry, ensure_ascii=True, separators=(",", ":")))

        if updated:
            self.index_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def list_missions(self, status: Optional[str] = None) -> List[TaskState]:
        """Lista missions via projeção completa (aceitável para MVP)."""
        results: List[TaskState] = []
        if not self.index_path.exists():
            return results

        with open(self.index_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entry = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                mission_id = entry.get("mission_id", "")
                if not mission_id:
                    continue
                try:
                    state = self.project(mission_id)
                    if status is None or state.status.value == status:
                        results.append(state)
                except (FileNotFoundError, ContractTamperedError):
                    continue

        return results

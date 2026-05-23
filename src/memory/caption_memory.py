"""CaptionMemory — persiste e consulta legendas aprovadas para reuso pelo agente.

Armazenamento: data/caption_memory.jsonl (JSONL, uma entrada por legenda aprovada).
Leitura: busca por account_handle + objective para popular similar_captions.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from src.utils.file_lock import jsonl_write_lock


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_ROOT = os.path.normpath(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))
CAPTION_MEMORY_PATH = os.path.join(_ROOT, "data", "caption_memory.jsonl")


@dataclass
class CaptionMemoryEntry:
    """Legenda aprovada persistida para reuso semantico simples."""

    entry_id: str
    account_handle: str
    objective: str
    format: str
    caption_text: str
    run_id: str
    draft_id: str
    approved_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, object]:
        """Serializa a entrada para JSONL."""
        return asdict(self)

    @classmethod
    def from_dict(cls: type["CaptionMemoryEntry"], data: dict[str, object]) -> "CaptionMemoryEntry":
        """Reconstrui uma entrada persistida."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class CaptionMemoryWriter:
    """Persiste legendas aprovadas em JSONL para reuso futuro."""

    def __init__(self, path: str = CAPTION_MEMORY_PATH) -> None:
        self.path = path
        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)

    def write(
        self,
        account_handle: str,
        objective: str,
        format: str,
        caption_text: str,
        run_id: str,
        draft_id: str,
    ) -> CaptionMemoryEntry:
        """Persiste uma legenda aprovada e retorna a entrada criada."""
        entry = CaptionMemoryEntry(
            entry_id=uuid.uuid4().hex[:12],
            account_handle=account_handle,
            objective=objective,
            format=format,
            caption_text=caption_text,
            run_id=run_id,
            draft_id=draft_id,
        )
        with jsonl_write_lock(self.path):
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        return entry


class CaptionMemoryReader:
    """Consulta legendas aprovadas por account + objective."""

    def __init__(self, path: str = CAPTION_MEMORY_PATH) -> None:
        self.path = path

    def find_similar(
        self,
        account_handle: str,
        objective: str,
        top_k: int = 3,
    ) -> list[str]:
        """Retorna até top_k textos de legendas aprovadas para essa conta e objetivo."""
        if not os.path.exists(self.path):
            return []
        matches: list[CaptionMemoryEntry] = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = CaptionMemoryEntry.from_dict(json.loads(line))
                except (json.JSONDecodeError, TypeError, KeyError):
                    continue
                if (
                    entry.account_handle == account_handle
                    and entry.objective == objective
                ):
                    matches.append(entry)
        # mais recentes primeiro
        matches.sort(key=lambda e: e.approved_at, reverse=True)
        return [e.caption_text for e in matches[:top_k]]

    def count(self, account_handle: str | None = None) -> int:
        """Conta entradas totais ou filtradas por conta."""
        if not os.path.exists(self.path):
            return 0
        total = 0
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = CaptionMemoryEntry.from_dict(json.loads(line))
                    if account_handle is None or entry.account_handle == account_handle:
                        total += 1
                except (json.JSONDecodeError, TypeError, KeyError):
                    continue
        return total

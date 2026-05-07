"""Registry Manager — CRUD thread-safe em JSONL."""
from __future__ import annotations
import json
import logging
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import RegistryEntry

logger = logging.getLogger("omnis.forge.registry")

DATA_DIR = Path(__file__).parent / "data"
REGISTRY_PATH = DATA_DIR / "skillregistry.jsonl"


class RegistryManager:
    """CRUD thread-safe para o skillregistry.jsonl."""

    def __init__(self, registry_path: Path = REGISTRY_PATH):
        self.path = registry_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _load_all(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        entries = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        logger.warning("Linha invalida no registry", extra={"error": str(e)})
        return entries

    def _write_all(self, entries: List[Dict[str, Any]]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    def add(self, entry: RegistryEntry) -> None:
        with self._lock:
            entries = self._load_all()
            existing = next((e for e in entries if e["name"] == entry.name), None)
            if existing:
                raise ValueError(f"Skill '{entry.name}' ja existe no registry. Use update().")
            entries.append(self._to_dict(entry))
            self._write_all(entries)
            logger.info("Skill adicionada ao registry", extra={"skill": entry.name})

    def update(self, name: str, updates: Dict[str, Any]) -> None:
        with self._lock:
            entries = self._load_all()
            for i, entry in enumerate(entries):
                if entry["name"] == name:
                    entries[i] = {**entry, **updates, "updated_at": datetime.utcnow().isoformat()}
                    self._write_all(entries)
                    logger.info("Skill atualizada", extra={"skill": name})
                    return
            raise KeyError(f"Skill '{name}' nao encontrada no registry.")

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        for entry in self._load_all():
            if entry["name"] == name:
                return entry
        return None

    def list_by_status(self, status: str) -> List[Dict[str, Any]]:
        return [e for e in self._load_all() if e.get("status") == status]

    def list_by_sector(self, sector: str) -> List[Dict[str, Any]]:
        return [e for e in self._load_all() if e.get("owner") == sector]

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        return [
            e for e in self._load_all()
            if q in e.get("name", "").lower()
            or q in e.get("description", "").lower()
            or any(q in tag.lower() for tag in e.get("tags", []))
        ]

    def _to_dict(self, entry: RegistryEntry) -> Dict[str, Any]:
        return {
            "id": entry.id or str(uuid.uuid4()),
            "name": entry.name,
            "version": entry.version,
            "description": entry.description,
            "status": entry.status,
            "risk_level": entry.risk_level,
            "owner": entry.owner,
            "tags": entry.tags,
            "path": str(entry.path) if entry.path else "",
            "manifest_path": str(entry.manifest_path) if entry.manifest_path else "",
            "created_at": entry.created_at.isoformat() if entry.created_at else datetime.utcnow().isoformat(),
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else datetime.utcnow().isoformat(),
            "usage_stats": entry.usage_stats,
        }

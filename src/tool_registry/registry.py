"""Tool Registry — storage JSONL + operacoes CRUD. P0.8."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.tool_registry.models import ToolRecord, ToolStatus
from src.tool_registry.errors import DuplicateToolError, ToolNotFoundError


class ToolRegistry:
    """Storage file-based para Tool Records."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is None:
            base_dir = os.path.expanduser("~/omnis-control/data/tool_registry")
        self.base_dir = Path(base_dir)
        self.tools_path = self.base_dir / "tools.jsonl"
        self.log_path = self.base_dir / "validation_log.jsonl"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ── CRUD ────────────────────────────────────────────────────────

    def add_tool(self, record: ToolRecord) -> ToolRecord:
        """Adiciona ferramenta. Levanta DuplicateToolError se tool_id ja existe."""
        if self._exists(record.tool_id):
            raise DuplicateToolError(
                f"Ferramenta '{record.tool_id}' ja registrada. Use update_tool() para modificar."
            )
        self._write_tool(record)
        return record

    def get_tool(self, tool_id: str) -> Optional[ToolRecord]:
        """Busca ferramenta por tool_id. Retorna None se nao encontrada."""
        for r in self._read_all():
            if r.tool_id == tool_id:
                return r
        return None

    def list_tools(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[ToolRecord]:
        """Lista ferramentas com filtros opcionais."""
        results = self._read_all()
        if status:
            results = [r for r in results if r.status == status]
        if category:
            results = [r for r in results if r.category == category]
        return results

    def update_tool(self, tool_id: str, **fields) -> Optional[ToolRecord]:
        """Atualiza campos de uma ferramenta existente."""
        records = self._read_all()
        updated = None
        for r in records:
            if r.tool_id == tool_id:
                data = r.model_dump()
                data.update(fields)
                data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                updated = ToolRecord(**data)
                break

        if updated is None:
            return None

        self._write_all(records, tool_id, updated)
        return updated

    def update_status(
        self,
        tool_id: str,
        status: str,
        validation_status: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[ToolRecord]:
        """Atualiza status com registro em validation_log."""
        fields = {"status": status}
        if validation_status is not None:
            fields["validation_status"] = validation_status
            fields["last_validated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if notes is not None:
            fields["notes"] = notes

        result = self.update_tool(tool_id, **fields)

        # Append to validation log
        if result is not None:
            log_entry = {
                "tool_id": tool_id,
                "previous_status": self._get_previous_status(tool_id, result.status),
                "new_status": status,
                "validation_status": validation_status,
                "notes": notes or "",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=True, separators=(",", ":")) + "\n")

        return result

    def mark_validated(
        self,
        tool_id: str,
        validation_status: str,
        notes: Optional[str] = None,
    ) -> Optional[ToolRecord]:
        """Marca ferramenta como validada (sem alterar status operacional)."""
        record = self.get_tool(tool_id)
        if record is None:
            return None
        return self.update_status(
            tool_id,
            status=record.status,
            validation_status=validation_status,
            notes=notes,
        )

    def tools_by_status(self) -> Dict[str, int]:
        """Contagem de ferramentas por status."""
        counts: Dict[str, int] = {}
        for r in self._read_all():
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts

    def tools_by_category(self) -> Dict[str, int]:
        """Contagem de ferramentas por categoria."""
        counts: Dict[str, int] = {}
        for r in self._read_all():
            counts[r.category] = counts.get(r.category, 0) + 1
        return counts

    def get_validation_log(self, tool_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Retorna entradas do validation log."""
        if not self.log_path.exists():
            return []
        entries: List[Dict[str, Any]] = []
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entry = json.loads(stripped)
                    if tool_id is None or entry.get("tool_id") == tool_id:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue
        return entries[-limit:]

    # ── Internals ───────────────────────────────────────────────────

    def _exists(self, tool_id: str) -> bool:
        return self.get_tool(tool_id) is not None

    def _read_all(self) -> List[ToolRecord]:
        if not self.tools_path.exists():
            return []
        records: List[ToolRecord] = []
        with open(self.tools_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                    records.append(ToolRecord(**data))
                except (json.JSONDecodeError, Exception):
                    continue
        return records

    def _write_tool(self, record: ToolRecord) -> None:
        line = json.dumps(record.model_dump(), ensure_ascii=True, separators=(",", ":"))
        with open(self.tools_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _write_all(self, records: List[ToolRecord], tool_id: str, updated: ToolRecord) -> None:
        """Reescreve arquivo substituindo tool_id por updated."""
        lines = []
        for r in records:
            if r.tool_id == tool_id:
                lines.append(json.dumps(updated.model_dump(), ensure_ascii=True, separators=(",", ":")))
            else:
                lines.append(json.dumps(r.model_dump(), ensure_ascii=True, separators=(",", ":")))
        self.tools_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _get_previous_status(self, tool_id: str, fallback: str) -> str:
        record = self.get_tool(tool_id)
        return record.status if record else fallback

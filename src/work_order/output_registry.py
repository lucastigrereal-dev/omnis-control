"""Output Registry — persistent index of all collected outputs."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.work_order.models import OutputEntry, OutputType


@dataclass
class OutputRegistry:
    """Index of all outputs collected across work orders."""
    entries: list[OutputRegistryEntry] = field(default_factory=list)
    _file_path: Path | None = None

    def add(self, entry: "OutputRegistryEntry"):
        self.entries.append(entry)
        self._save()

    def find_by_work_order(self, work_order_id: str) -> list["OutputRegistryEntry"]:
        return [e for e in self.entries if e.work_order_id == work_order_id]

    def find_by_type(self, output_type: OutputType) -> list["OutputRegistryEntry"]:
        return [e for e in self.entries if e.output_type == output_type]

    def find_by_status(self, status: str) -> list["OutputRegistryEntry"]:
        return [e for e in self.entries if e.status == status]

    def count_by_work_order(self, work_order_id: str) -> int:
        return len(self.find_by_work_order(work_order_id))

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}

    def _save(self):
        if self._file_path:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_path.write_text(
                json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    @classmethod
    def load(cls, path: Path) -> "OutputRegistry":
        reg = cls(entries=[], _file_path=path)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                reg.entries = [OutputRegistryEntry.from_dict(e) for e in data.get("entries", [])]
            except (json.JSONDecodeError, KeyError):
                reg.entries = []
        return reg


@dataclass
class OutputRegistryEntry:
    """A single entry in the output registry."""
    output_id: str
    work_order_id: str
    output_type: OutputType
    contract_id: str
    status: str  # submitted, validated, rejected
    disk_path: str  # relative to exports/work_orders/
    submitted_at: str
    validated_at: str | None = None
    content_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "output_id": self.output_id,
            "work_order_id": self.work_order_id,
            "output_type": self.output_type.value,
            "contract_id": self.contract_id,
            "status": self.status,
            "disk_path": self.disk_path,
            "submitted_at": self.submitted_at,
            "validated_at": self.validated_at,
            "content_hash": self.content_hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OutputRegistryEntry":
        return cls(
            output_id=d["output_id"],
            work_order_id=d["work_order_id"],
            output_type=OutputType(d["output_type"]),
            contract_id=d["contract_id"],
            status=d.get("status", "submitted"),
            disk_path=d.get("disk_path", ""),
            submitted_at=d.get("submitted_at", ""),
            validated_at=d.get("validated_at"),
            content_hash=d.get("content_hash", ""),
        )

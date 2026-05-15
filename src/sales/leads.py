"""W111 — Lead model + LeadRegistry."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path


@dataclass
class Lead:
    """Canonical lead model for Sales/CRM pipeline."""

    lead_id: str
    name: str
    company: str = ""
    contact_channel: str = ""  # email, whatsapp, telefonema, instagram, telegram, indicacao
    contact_value: str = ""  # masked placeholder — never store real phone/email
    source: str = ""  # instagram, indicacao, site, evento, prospeccao, outro
    segment: str = ""  # hotel, restaurante, agencia, operadora, outro
    interest: str = ""  # publi, collab, permuta, pacote, outro
    status: str = "novo"  # novo, qualificado, em_negociacao, convertido, perdido
    score: int = 0
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    dry_run: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "lead_id": self.lead_id,
            "name": self.name,
            "company": self.company,
            "contact_channel": self.contact_channel,
            "contact_value": self.contact_value,
            "source": self.source,
            "segment": self.segment,
            "interest": self.interest,
            "status": self.status,
            "score": self.score,
            "tags": self.tags,
            "notes": self.notes,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Lead":
        return cls(
            lead_id=d["lead_id"],
            name=d.get("name", ""),
            company=d.get("company", ""),
            contact_channel=d.get("contact_channel", ""),
            contact_value=d.get("contact_value", ""),
            source=d.get("source", ""),
            segment=d.get("segment", ""),
            interest=d.get("interest", ""),
            status=d.get("status", "novo"),
            score=d.get("score", 0),
            tags=d.get("tags", []),
            notes=d.get("notes", ""),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )

    def to_markdown(self) -> str:
        return "\n".join([
            f"# Lead: {self.name}",
            f"**ID:** {self.lead_id}",
            f"**Company:** {self.company or '—'}",
            f"**Channel:** {self.contact_channel or '—'}",
            f"**Source:** {self.source or '—'}",
            f"**Segment:** {self.segment or '—'}",
            f"**Interest:** {self.interest or '—'}",
            f"**Status:** {self.status}",
            f"**Score:** {self.score}",
            f"**Tags:** {', '.join(self.tags) if self.tags else '—'}",
            f"**Notes:** {self.notes or '—'}",
            f"**dry_run:** {self.dry_run}",
        ])

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


class LeadRegistry:
    """File-backed registry for leads."""

    def __init__(self, storage_dir: str | Path | None = None):
        self._leads: dict[str, Lead] = {}
        self._storage_dir = Path(storage_dir) if storage_dir else None

    @property
    def count(self) -> int:
        return len(self._leads)

    def create(self, name: str, **kwargs) -> Lead:
        import uuid
        lead = Lead(
            lead_id=str(uuid.uuid4())[:12],
            name=name,
            **kwargs,
        )
        self._leads[lead.lead_id] = lead
        if self._storage_dir:
            self._flush()
        return lead

    def get(self, lead_id: str) -> Lead | None:
        return self._leads.get(lead_id)

    def list_all(self) -> list[Lead]:
        return list(self._leads.values())

    def list_by_status(self, status: str) -> list[Lead]:
        return [l for l in self._leads.values() if l.status == status]

    def list_by_segment(self, segment: str) -> list[Lead]:
        return [l for l in self._leads.values() if l.segment == segment]

    def list_by_source(self, source: str) -> list[Lead]:
        return [l for l in self._leads.values() if l.source == source]

    def update(self, lead_id: str, **kwargs) -> Lead | None:
        lead = self._leads.get(lead_id)
        if not lead:
            return None
        for k, v in kwargs.items():
            if hasattr(lead, k):
                setattr(lead, k, v)
        lead.touch()
        if self._storage_dir:
            self._flush()
        return lead

    def delete(self, lead_id: str) -> bool:
        if lead_id in self._leads:
            del self._leads[lead_id]
            if self._storage_dir:
                self._flush()
            return True
        return False

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(l.to_dict(), ensure_ascii=False) for l in self._leads.values())

    def _flush(self) -> None:
        if not self._storage_dir:
            return
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        path = self._storage_dir / "leads.jsonl"
        path.write_text(self.to_jsonl() + "\n", encoding="utf-8")

    @classmethod
    def load(cls, storage_dir: str | Path) -> "LeadRegistry":
        registry = cls(storage_dir)
        path = Path(storage_dir) / "leads.jsonl"
        if path.exists():
            for line in path.read_text(encoding="utf-8").strip().split("\n"):
                if line.strip():
                    d = json.loads(line)
                    lead = Lead.from_dict(d)
                    registry._leads[lead.lead_id] = lead
        return registry

"""W113 — Deal model + DealRegistry."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path

from src.sales.leads import Lead
from src.sales.pipeline import PipelineStage


@dataclass
class Deal:
    """Canonical deal/negocio model linked to a lead."""

    deal_id: str
    lead_id: str
    title: str = ""
    value: float = 0.0
    currency: str = "BRL"
    stage: str = PipelineStage.NOVO.value
    probability: float = 0.1
    expected_close_date: str = ""
    owner: str = ""
    products: list[str] = field(default_factory=list)  # Starter, Growth, Premium
    notes: str = ""
    dry_run: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "deal_id": self.deal_id,
            "lead_id": self.lead_id,
            "title": self.title,
            "value": self.value,
            "currency": self.currency,
            "stage": self.stage,
            "probability": self.probability,
            "expected_close_date": self.expected_close_date,
            "owner": self.owner,
            "products": self.products,
            "notes": self.notes,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Deal":
        return cls(
            deal_id=d["deal_id"],
            lead_id=d.get("lead_id", ""),
            title=d.get("title", ""),
            value=d.get("value", 0.0),
            currency=d.get("currency", "BRL"),
            stage=d.get("stage", PipelineStage.NOVO.value),
            probability=d.get("probability", 0.1),
            expected_close_date=d.get("expected_close_date", ""),
            owner=d.get("owner", ""),
            products=d.get("products", []),
            notes=d.get("notes", ""),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )

    def to_markdown(self) -> str:
        return "\n".join([
            f"# Deal: {self.title}",
            f"**ID:** {self.deal_id}",
            f"**Lead:** {self.lead_id}",
            f"**Value:** {self.currency} {self.value:,.2f}",
            f"**Stage:** {self.stage}",
            f"**Probability:** {self.probability:.0%}",
            f"**Expected Close:** {self.expected_close_date or '—'}",
            f"**Owner:** {self.owner or '—'}",
            f"**Products:** {', '.join(self.products) if self.products else '—'}",
            f"**Notes:** {self.notes or '—'}",
            f"**dry_run:** {self.dry_run}",
        ])

    @property
    def weighted_value(self) -> float:
        return self.value * self.probability

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


class DealRegistry:
    """File-backed registry for deals."""

    def __init__(self, storage_dir: str | Path | None = None):
        self._deals: dict[str, Deal] = {}
        self._storage_dir = Path(storage_dir) if storage_dir else None

    @property
    def count(self) -> int:
        return len(self._deals)

    def create(self, lead_id: str, title: str = "", **kwargs) -> Deal:
        import uuid
        if "value" in kwargs and kwargs["value"] < 0:
            raise ValueError("Deal value cannot be negative")
        deal = Deal(
            deal_id=str(uuid.uuid4())[:12],
            lead_id=lead_id,
            title=title,
            **kwargs,
        )
        self._deals[deal.deal_id] = deal
        if self._storage_dir:
            self._flush()
        return deal

    def get(self, deal_id: str) -> Deal | None:
        return self._deals.get(deal_id)

    def list_all(self) -> list[Deal]:
        return list(self._deals.values())

    def list_by_lead(self, lead_id: str) -> list[Deal]:
        return [d for d in self._deals.values() if d.lead_id == lead_id]

    def list_by_stage(self, stage: str) -> list[Deal]:
        return [d for d in self._deals.values() if d.stage == stage]

    def update(self, deal_id: str, **kwargs) -> Deal | None:
        deal = self._deals.get(deal_id)
        if not deal:
            return None
        if "value" in kwargs and kwargs["value"] < 0:
            raise ValueError("Deal value cannot be negative")
        for k, v in kwargs.items():
            if hasattr(deal, k):
                setattr(deal, k, v)
        deal.touch()
        if self._storage_dir:
            self._flush()
        return deal

    def delete(self, deal_id: str) -> bool:
        if deal_id in self._deals:
            del self._deals[deal_id]
            if self._storage_dir:
                self._flush()
            return True
        return False

    def total_pipeline_value(self) -> float:
        return sum(d.value for d in self._deals.values())

    def total_weighted_value(self) -> float:
        return sum(d.weighted_value for d in self._deals.values())

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(d.to_dict(), ensure_ascii=False) for d in self._deals.values())

    def _flush(self) -> None:
        if not self._storage_dir:
            return
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        path = self._storage_dir / "deals.jsonl"
        path.write_text(self.to_jsonl() + "\n", encoding="utf-8")

    @classmethod
    def load(cls, storage_dir: str | Path) -> "DealRegistry":
        registry = cls(storage_dir)
        path = Path(storage_dir) / "deals.jsonl"
        if path.exists():
            for line in path.read_text(encoding="utf-8").strip().split("\n"):
                if line.strip():
                    d = json.loads(line)
                    deal = Deal.from_dict(d)
                    registry._deals[deal.deal_id] = deal
        return registry

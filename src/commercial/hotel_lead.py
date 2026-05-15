"""W121 — HotelLead model + HotelLeadRegistry. Extends src/sales/leads.py:Lead."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path

from src.sales.leads import Lead


HOTEL_NICHE_VALUES = frozenset({
    "hotel", "resort", "pousada", "boutique", "fazenda",
    "urbano", "hostel", "eco_resort", "glamping", "apart_hotel",
})

HOTEL_TIER_VALUES = frozenset({"Starter", "Growth", "Premium"})

PRIORITY_VALUES = frozenset({"hot", "warm", "cold", "disqualified"})


@dataclass
class HotelLead:
    """Hotel prospecting lead — composes Lead with hotel-specific fields.

    All contact data is masked/placeholder. Zero external enrichment.
    """

    hotel_lead_id: str
    base_lead: Lead  # composed Lead from src/sales/leads.py
    hotel_name: str = ""
    cnpj_placeholder: str = ""  # masked — never real CNPJ
    city: str = ""
    state: str = ""
    region: str = ""  # nordeste, sudeste, sul, etc.
    hotel_tier: str = "Growth"  # Starter, Growth, Premium
    niche: str = "hotel"
    room_count_placeholder: int = 0  # approximate, masked
    average_daily_rate_placeholder: float = 0.0  # approximate R$
    decision_maker_name: str = ""
    decision_maker_role: str = ""  # gerente, proprietario, marketing, etc.
    fit_score: int = 0  # 0-100
    priority_tier: str = "warm"  # hot, warm, cold, disqualified
    notes: str = ""
    dry_run: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if self.hotel_tier not in HOTEL_TIER_VALUES:
            raise ValueError(f"Invalid hotel_tier: {self.hotel_tier}. Valid: {sorted(HOTEL_TIER_VALUES)}")
        if self.niche not in HOTEL_NICHE_VALUES:
            raise ValueError(f"Invalid niche: {self.niche}. Valid: {sorted(HOTEL_NICHE_VALUES)}")
        if self.priority_tier not in PRIORITY_VALUES:
            raise ValueError(f"Invalid priority_tier: {self.priority_tier}. Valid: {sorted(PRIORITY_VALUES)}")

    @property
    def lead_id(self) -> str:
        """Proxy to composed Lead's id for cross-module queries."""
        return self.base_lead.lead_id

    @property
    def name(self) -> str:
        return self.base_lead.name

    @property
    def company(self) -> str:
        return self.base_lead.company

    @property
    def contact_channel(self) -> str:
        return self.base_lead.contact_channel

    @property
    def source(self) -> str:
        return self.base_lead.source

    @property
    def interest(self) -> str:
        return self.base_lead.interest

    @property
    def is_pursuable(self) -> bool:
        return self.priority_tier in {"hot", "warm"}

    @property
    def is_premium_candidate(self) -> bool:
        return self.fit_score >= 80 and self.hotel_tier == "Premium"

    def to_dict(self) -> dict:
        return {
            "hotel_lead_id": self.hotel_lead_id,
            "base_lead": self.base_lead.to_dict(),
            "hotel_name": self.hotel_name,
            "cnpj_placeholder": self.cnpj_placeholder,
            "city": self.city,
            "state": self.state,
            "region": self.region,
            "hotel_tier": self.hotel_tier,
            "niche": self.niche,
            "room_count_placeholder": self.room_count_placeholder,
            "average_daily_rate_placeholder": self.average_daily_rate_placeholder,
            "decision_maker_name": self.decision_maker_name,
            "decision_maker_role": self.decision_maker_role,
            "fit_score": self.fit_score,
            "priority_tier": self.priority_tier,
            "notes": self.notes,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HotelLead":
        base = Lead.from_dict(d["base_lead"])
        return cls(
            hotel_lead_id=d["hotel_lead_id"],
            base_lead=base,
            hotel_name=d.get("hotel_name", ""),
            cnpj_placeholder=d.get("cnpj_placeholder", ""),
            city=d.get("city", ""),
            state=d.get("state", ""),
            region=d.get("region", ""),
            hotel_tier=d.get("hotel_tier", "Growth"),
            niche=d.get("niche", "hotel"),
            room_count_placeholder=d.get("room_count_placeholder", 0),
            average_daily_rate_placeholder=d.get("average_daily_rate_placeholder", 0.0),
            decision_maker_name=d.get("decision_maker_name", ""),
            decision_maker_role=d.get("decision_maker_role", ""),
            fit_score=d.get("fit_score", 0),
            priority_tier=d.get("priority_tier", "warm"),
            notes=d.get("notes", ""),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )

    def to_markdown(self) -> str:
        return "\n".join([
            f"# Hotel Lead: {self.hotel_name or self.name}",
            f"**ID:** {self.hotel_lead_id}",
            f"**Base Lead:** {self.lead_id}",
            f"**CNPJ:** {self.cnpj_placeholder or 'mascarado'}",
            f"**City/State:** {self.city}/{self.state}",
            f"**Region:** {self.region or '—'}",
            f"**Niche:** {self.niche}",
            f"**Hotel Tier:** {self.hotel_tier}",
            f"**Rooms:** {self.room_count_placeholder or '—'}",
            f"**ADR:** R$ {self.average_daily_rate_placeholder:,.2f}" if self.average_daily_rate_placeholder > 0 else f"**ADR:** —",
            f"**Decision Maker:** {self.decision_maker_name or '—'} ({self.decision_maker_role or '—'})",
            f"**Fit Score:** {self.fit_score}/100",
            f"**Priority:** {self.priority_tier}",
            f"**Pursuable:** {self.is_pursuable}",
            f"**Premium Candidate:** {self.is_premium_candidate}",
            f"**Notes:** {self.notes or '—'}",
            f"**dry_run:** {self.dry_run}",
        ])

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


class HotelLeadRegistry:
    """File-backed registry for hotel prospecting leads."""

    def __init__(self, storage_dir: str | Path | None = None):
        self._hotel_leads: dict[str, HotelLead] = {}
        self._storage_dir = Path(storage_dir) if storage_dir else None

    @property
    def count(self) -> int:
        return len(self._hotel_leads)

    @property
    def pursuable_count(self) -> int:
        return sum(1 for hl in self._hotel_leads.values() if hl.is_pursuable)

    @property
    def premium_candidates(self) -> int:
        return sum(1 for hl in self._hotel_leads.values() if hl.is_premium_candidate)

    def create(self, base_lead: Lead, **kwargs) -> HotelLead:
        import uuid
        hl = HotelLead(
            hotel_lead_id=str(uuid.uuid4())[:12],
            base_lead=base_lead,
            **kwargs,
        )
        self._hotel_leads[hl.hotel_lead_id] = hl
        if self._storage_dir:
            self._flush()
        return hl

    def get(self, hotel_lead_id: str) -> HotelLead | None:
        return self._hotel_leads.get(hotel_lead_id)

    def get_by_base_lead(self, lead_id: str) -> HotelLead | None:
        for hl in self._hotel_leads.values():
            if hl.lead_id == lead_id:
                return hl
        return None

    def list_all(self) -> list[HotelLead]:
        return list(self._hotel_leads.values())

    def list_by_city(self, city: str) -> list[HotelLead]:
        return [hl for hl in self._hotel_leads.values() if hl.city.lower() == city.lower()]

    def list_by_state(self, state: str) -> list[HotelLead]:
        return [hl for hl in self._hotel_leads.values() if hl.state.lower() == state.lower()]

    def list_by_niche(self, niche: str) -> list[HotelLead]:
        return [hl for hl in self._hotel_leads.values() if hl.niche == niche]

    def list_by_tier(self, hotel_tier: str) -> list[HotelLead]:
        return [hl for hl in self._hotel_leads.values() if hl.hotel_tier == hotel_tier]

    def list_pursuable(self) -> list[HotelLead]:
        return [hl for hl in self._hotel_leads.values() if hl.is_pursuable]

    def list_by_priority(self, priority_tier: str) -> list[HotelLead]:
        return [hl for hl in self._hotel_leads.values() if hl.priority_tier == priority_tier]

    def update(self, hotel_lead_id: str, **kwargs) -> HotelLead | None:
        hl = self._hotel_leads.get(hotel_lead_id)
        if not hl:
            return None
        if "base_lead" in kwargs and isinstance(kwargs["base_lead"], Lead):
            hl.base_lead = kwargs.pop("base_lead")
        for k, v in kwargs.items():
            if hasattr(hl, k):
                setattr(hl, k, v)
        hl.touch()
        if self._storage_dir:
            self._flush()
        return hl

    def delete(self, hotel_lead_id: str) -> bool:
        if hotel_lead_id in self._hotel_leads:
            del self._hotel_leads[hotel_lead_id]
            if self._storage_dir:
                self._flush()
            return True
        return False

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(hl.to_dict(), ensure_ascii=False) for hl in self._hotel_leads.values())

    def _flush(self) -> None:
        if not self._storage_dir:
            return
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        path = self._storage_dir / "hotel_leads.jsonl"
        path.write_text(self.to_jsonl() + "\n", encoding="utf-8")

    @classmethod
    def load(cls, storage_dir: str | Path) -> "HotelLeadRegistry":
        registry = cls(storage_dir)
        path = Path(storage_dir) / "hotel_leads.jsonl"
        if path.exists():
            for line in path.read_text(encoding="utf-8").strip().split("\n"):
                if line.strip():
                    d = json.loads(line)
                    hl = HotelLead.from_dict(d)
                    registry._hotel_leads[hl.hotel_lead_id] = hl
        return registry

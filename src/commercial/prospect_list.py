"""W122 — SDR Prospect List for HotelLead management. File-backed, dry-run, local-first.

Extends legacy src/commercial_sdr/ scoring patterns adapted for HotelLead fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional

from src.commercial.hotel_lead import HotelLead


PRIORITY_WEIGHTS = {"hot": 3, "warm": 2, "cold": 1, "disqualified": 0}
TIER_BONUS = {"Premium": 15, "Growth": 5, "Starter": 0}
REGION_PRIORITY = {"nordeste": 10, "sudeste": 8, "sul": 6, "centro_oeste": 4, "norte": 2}


@dataclass
class ProspectEntry:
    """Entry in a prospect list — wraps HotelLead with list-specific metadata."""

    entry_id: str
    hotel_lead: HotelLead
    added_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    dry_run: bool = True

    @property
    def priority_score(self) -> int:
        """Deterministic priority score from HotelLead fields.

        Formula: fit_score + priority_weight*10 + tier_bonus + region_priority.
        Range ~0-155.
        """
        hl = self.hotel_lead
        score = hl.fit_score
        score += PRIORITY_WEIGHTS.get(hl.priority_tier, 0) * 10
        score += TIER_BONUS.get(hl.hotel_tier, 0)
        score += REGION_PRIORITY.get(hl.region.lower(), 0) if hl.region else 0
        return score

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "hotel_lead": self.hotel_lead.to_dict(),
            "added_at": self.added_at,
            "tags": self.tags,
            "notes": self.notes,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProspectEntry":
        hl = HotelLead.from_dict(d["hotel_lead"])
        return cls(
            entry_id=d["entry_id"],
            hotel_lead=hl,
            added_at=d.get("added_at", ""),
            tags=d.get("tags", []),
            notes=d.get("notes", ""),
            dry_run=d.get("dry_run", True),
        )

    def to_markdown(self) -> str:
        hl = self.hotel_lead
        return "\n".join([
            f"## Prospect: {hl.hotel_name or hl.name}",
            f"**Entry ID:** {self.entry_id}",
            f"**Hotel Lead ID:** {hl.hotel_lead_id}",
            f"**City/State:** {hl.city}/{hl.state}",
            f"**Region:** {hl.region or '—'}",
            f"**Tier:** {hl.hotel_tier} | **Niche:** {hl.niche}",
            f"**Priority:** {hl.priority_tier} | **Fit:** {hl.fit_score}/100",
            f"**Priority Score:** {self.priority_score}",
            f"**Tags:** {', '.join(self.tags) if self.tags else '—'}",
            f"**Notes:** {self.notes or '—'}",
            f"**dry_run:** {self.dry_run}",
        ])


class ProspectList:
    """File-backed registry for SDR hotel prospects.

    Wraps HotelLead entries with filtering, prioritization, and batch operations.
    Complements legacy src/commercial_sdr/service.py scoring.
    """

    def __init__(self, storage_dir: str | Path | None = None):
        self._entries: dict[str, ProspectEntry] = {}
        self._storage_dir = Path(storage_dir) if storage_dir else None

    @property
    def count(self) -> int:
        return len(self._entries)

    @property
    def pursuable_count(self) -> int:
        return sum(1 for e in self._entries.values() if e.hotel_lead.is_pursuable)

    @property
    def premium_candidates(self) -> int:
        return sum(1 for e in self._entries.values() if e.hotel_lead.is_premium_candidate)

    # ── CRUD ────────────────────────────────────────────────────────────────

    def add(self, hotel_lead: HotelLead, tags: list[str] | None = None,
            notes: str = "") -> ProspectEntry:
        import uuid
        entry = ProspectEntry(
            entry_id=str(uuid.uuid4())[:12],
            hotel_lead=hotel_lead,
            tags=tags or [],
            notes=notes,
        )
        self._entries[entry.entry_id] = entry
        if self._storage_dir:
            self._flush()
        return entry

    def get(self, entry_id: str) -> ProspectEntry | None:
        return self._entries.get(entry_id)

    def remove(self, entry_id: str) -> bool:
        if entry_id in self._entries:
            del self._entries[entry_id]
            if self._storage_dir:
                self._flush()
            return True
        return False

    def list_all(self) -> list[ProspectEntry]:
        return list(self._entries.values())

    # ── Filtering ───────────────────────────────────────────────────────────

    def filter_by_city(self, city: str) -> list[ProspectEntry]:
        c = city.lower()
        return [e for e in self._entries.values() if e.hotel_lead.city.lower() == c]

    def filter_by_state(self, state: str) -> list[ProspectEntry]:
        s = state.lower()
        return [e for e in self._entries.values() if e.hotel_lead.state.lower() == s]

    def filter_by_tier(self, hotel_tier: str) -> list[ProspectEntry]:
        return [e for e in self._entries.values() if e.hotel_lead.hotel_tier == hotel_tier]

    def filter_by_priority(self, priority_tier: str) -> list[ProspectEntry]:
        return [e for e in self._entries.values() if e.hotel_lead.priority_tier == priority_tier]

    def filter_by_niche(self, niche: str) -> list[ProspectEntry]:
        return [e for e in self._entries.values() if e.hotel_lead.niche == niche]

    def filter_by_region(self, region: str) -> list[ProspectEntry]:
        r = region.lower()
        return [e for e in self._entries.values() if e.hotel_lead.region.lower() == r]

    def filter_pursuable(self) -> list[ProspectEntry]:
        return [e for e in self._entries.values() if e.hotel_lead.is_pursuable]

    # ── Prioritization ──────────────────────────────────────────────────────

    def prioritized(self, descending: bool = True) -> list[ProspectEntry]:
        """Return entries sorted by priority_score (highest first by default)."""
        return sorted(self._entries.values(), key=lambda e: e.priority_score, reverse=descending)

    def top(self, n: int = 10) -> list[ProspectEntry]:
        return self.prioritized()[:n]

    def hot_list(self) -> list[ProspectEntry]:
        """Prospects with priority_tier='hot', sorted by fit_score descending."""
        hot = [e for e in self._entries.values() if e.hotel_lead.priority_tier == "hot"]
        return sorted(hot, key=lambda e: e.hotel_lead.fit_score, reverse=True)

    # ── Scoring ─────────────────────────────────────────────────────────────

    def compute_scores(self) -> list[dict]:
        """Compute and return priority scores for all entries, ranked.

        Adapts the legacy score_prospect() 4-factor model to HotelLead fields:
        - segment_fit → niche relevance (always hotel-aligned = high)
        - engagement_signal → contact_channel availability
        - budget_indicator → hotel_tier (Premium > Growth > Starter)
        - urgency → priority_tier (hot > warm > cold)
        """
        results = []
        for e in self._entries.values():
            hl = e.hotel_lead

            segment_fit = 0.90  # HotelLead niches are pre-validated hotel types
            engagement_signal = 0.50 + (0.15 if hl.base_lead.contact_channel else 0)
            budget_map = {"Premium": 0.85, "Growth": 0.55, "Starter": 0.30}
            budget_indicator = budget_map.get(hl.hotel_tier, 0.30)
            urgency_map = {"hot": 0.85, "warm": 0.50, "cold": 0.20, "disqualified": 0.0}
            urgency = urgency_map.get(hl.priority_tier, 0.20)

            composite = round(
                segment_fit * 0.35 + engagement_signal * 0.25 +
                budget_indicator * 0.25 + urgency * 0.15, 4
            )
            results.append({
                "entry_id": e.entry_id,
                "hotel_name": hl.hotel_name or hl.name,
                "priority_score": e.priority_score,
                "composite": composite,
                "segment_fit": segment_fit,
                "engagement_signal": round(engagement_signal, 2),
                "budget_indicator": budget_indicator,
                "urgency": urgency,
            })
        return sorted(results, key=lambda r: r["composite"], reverse=True)

    # ── Serialization ───────────────────────────────────────────────────────

    def to_jsonl(self) -> str:
        return "\n".join(
            json.dumps(e.to_dict(), ensure_ascii=False) for e in self._entries.values()
        )

    def export_summary(self) -> str:
        """Export prospect list as markdown summary."""
        lines = [
            "# SDR Prospect List Summary",
            f"**Total:** {self.count} | **Pursuable:** {self.pursuable_count} | "
            f"**Premium:** {self.premium_candidates}",
            "",
            "## Prioritized Prospects",
            "",
        ]
        for i, e in enumerate(self.prioritized(), 1):
            hl = e.hotel_lead
            lines.append(
                f"{i}. **{hl.hotel_name or hl.name}** — {hl.city}/{hl.state} | "
                f"Tier: {hl.hotel_tier} | Priority: {hl.priority_tier} | "
                f"Score: {e.priority_score} | Fit: {hl.fit_score}/100"
            )
        lines.append("")
        lines.append("## Scores Breakdown")
        lines.append("")
        for s in self.compute_scores():
            lines.append(
                f"- **{s['hotel_name']}** — composite={s['composite']}, "
                f"segment={s['segment_fit']}, engagement={s['engagement_signal']}, "
                f"budget={s['budget_indicator']}, urgency={s['urgency']}"
            )
        return "\n".join(lines)

    def _flush(self) -> None:
        if not self._storage_dir:
            return
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        path = self._storage_dir / "prospect_list.jsonl"
        path.write_text(self.to_jsonl() + "\n", encoding="utf-8")

    @classmethod
    def load(cls, storage_dir: str | Path) -> "ProspectList":
        plist = cls(storage_dir)
        path = Path(storage_dir) / "prospect_list.jsonl"
        if path.exists():
            for line in path.read_text(encoding="utf-8").strip().split("\n"):
                if line.strip():
                    d = json.loads(line)
                    entry = ProspectEntry.from_dict(d)
                    plist._entries[entry.entry_id] = entry
        return plist

"""W096 — 30-Day Content Calendar model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.content_factory.brief import ContentBrief


@dataclass
class CalendarSlot:
    day: int
    format: str = ""  # feed, carousel, reels, stories
    pillar: str = ""  # educacional, entretenimento, vendas, autoridade
    title: str = ""
    objective: str = "alcance"
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "format": self.format,
            "pillar": self.pillar,
            "title": self.title,
            "objective": self.objective,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CalendarSlot":
        return cls(
            day=d["day"],
            format=d.get("format", ""),
            pillar=d.get("pillar", ""),
            title=d.get("title", ""),
            objective=d.get("objective", "alcance"),
            notes=d.get("notes", ""),
        )


@dataclass
class ContentCalendar:
    calendar_id: str
    brand: str = ""
    theme: str = ""
    slots: list[CalendarSlot] = field(default_factory=list)
    start_date: str = ""  # ISO date
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    @property
    def slot_count(self) -> int:
        return len(self.slots)

    @property
    def format_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {}
        for s in self.slots:
            dist[s.format] = dist.get(s.format, 0) + 1
        return dist

    @property
    def pillar_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {}
        for s in self.slots:
            dist[s.pillar] = dist.get(s.pillar, 0) + 1
        return dist

    def to_dict(self) -> dict:
        return {
            "calendar_id": self.calendar_id,
            "brand": self.brand,
            "theme": self.theme,
            "slots": [s.to_dict() for s in self.slots],
            "start_date": self.start_date,
            "slot_count": self.slot_count,
            "format_distribution": self.format_distribution,
            "pillar_distribution": self.pillar_distribution,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContentCalendar":
        cal = cls(
            calendar_id=d["calendar_id"],
            brand=d.get("brand", ""),
            theme=d.get("theme", ""),
            start_date=d.get("start_date", ""),
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )
        for s in d.get("slots", []):
            cal.slots.append(CalendarSlot.from_dict(s))
        return cal

    def to_markdown(self) -> str:
        lines = [
            f"# Content Calendar: {self.theme}",
            f"**ID:** {self.calendar_id} | **Brand:** {self.brand} | **Days:** {self.slot_count}",
            f"**Start:** {self.start_date}",
            "",
            "| Day | Format | Pillar | Title | Objective |",
            "|---|---|---|---|---|",
        ]
        for s in self.slots:
            lines.append(f"| {s.day} | {s.format} | {s.pillar} | {s.title} | {s.objective} |")
        lines.extend(["", "## Format Distribution", ""])
        for fmt, count in sorted(self.format_distribution.items()):
            lines.append(f"- **{fmt}:** {count}")
        return "\n".join(lines)


class CalendarGenerator:
    """Deterministic 30-day content calendar from a brand theme. No LLM, no API."""

    DAYS = 30

    FORMAT_ROTATION = [
        "carousel", "feed", "stories", "feed",
        "reels", "feed", "carousel", "feed",
        "stories", "feed", "carousel", "reels",
        "feed", "feed", "carousel", "stories",
        "feed", "reels", "carousel", "feed",
        "stories", "feed", "carousel", "feed",
        "reels", "carousel", "feed", "stories",
        "feed", "feed",
    ]

    PILLAR_ROTATION = [
        "educacional", "entretenimento", "autoridade", "vendas",
        "educacional", "entretenimento", "vendas", "autoridade",
        "educacional", "vendas", "entretenimento", "autoridade",
        "educacional", "entretenimento", "autoridade", "vendas",
        "educacional", "autoridade", "entretenimento", "vendas",
        "educacional", "entretenimento", "autoridade", "vendas",
        "educacional", "vendas", "autoridade", "entretenimento",
        "educacional", "vendas",
    ]

    DAY_LABELS: dict[int, str] = {
        0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui",
        4: "Sex", 5: "Sab", 6: "Dom",
    }

    def generate(self, brief: ContentBrief) -> ContentCalendar:
        import uuid
        from datetime import datetime as dt, timedelta

        start = dt.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        slots: list[CalendarSlot] = []
        for day_idx in range(self.DAYS):
            fmt = self.FORMAT_ROTATION[day_idx % len(self.FORMAT_ROTATION)]
            pillar = self.PILLAR_ROTATION[day_idx % len(self.PILLAR_ROTATION)]

            date = start + timedelta(days=day_idx)
            dow = date.weekday()
            day_label = self.DAY_LABELS.get(dow, "")

            theme_words = brief.keywords[:2] if brief.keywords else [brief.title]
            theme_str = " ".join(theme_words)

            slot = CalendarSlot(
                day=day_idx + 1,
                format=fmt,
                pillar=pillar,
                title=f"{day_label} — {brief.brand}: {theme_str} ({pillar})",
                objective=self._objective_for_pillar(pillar),
                notes=f"Dia {day_idx + 1}/{self.DAYS} — {date.strftime('%Y-%m-%d')}",
            )
            slots.append(slot)

        return ContentCalendar(
            calendar_id=str(uuid.uuid4())[:8],
            brand=brief.brand,
            theme=f"{brief.title} — 30 dias",
            slots=slots,
            start_date=start.strftime("%Y-%m-%d"),
        )

    def _objective_for_pillar(self, pillar: str) -> str:
        mapping = {
            "educacional": "autoridade",
            "entretenimento": "alcance",
            "autoridade": "autoridade",
            "vendas": "conversao",
        }
        return mapping.get(pillar, "alcance")

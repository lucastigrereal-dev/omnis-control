"""W114 — Contact Timeline (append-only event log)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ContactEventType(str, Enum):
    EMAIL_MOCK = "email_mock"
    CALL_MOCK = "call_mock"
    MEETING_MOCK = "meeting_mock"
    WHATSAPP_MOCK = "whatsapp_mock"
    TELEGRAM_MOCK = "telegram_mock"
    NOTE = "note"
    PROPOSAL_SENT_MOCK = "proposal_sent_mock"
    FOLLOWUP_SCHEDULED = "followup_scheduled"


@dataclass
class ContactEvent:
    """A single contact event — append-only, immutable after creation."""

    event_id: str
    lead_id: str = ""
    deal_id: str = ""
    event_type: str = ContactEventType.NOTE.value
    summary: str = ""
    details: str = ""
    actor: str = "system"
    dry_run: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "lead_id": self.lead_id,
            "deal_id": self.deal_id,
            "event_type": self.event_type,
            "summary": self.summary,
            "details": self.details,
            "actor": self.actor,
            "dry_run": self.dry_run,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContactEvent":
        return cls(
            event_id=d["event_id"],
            lead_id=d.get("lead_id", ""),
            deal_id=d.get("deal_id", ""),
            event_type=d.get("event_type", ContactEventType.NOTE.value),
            summary=d.get("summary", ""),
            details=d.get("details", ""),
            actor=d.get("actor", "system"),
            dry_run=d.get("dry_run", True),
            timestamp=d.get("timestamp", ""),
        )


class ContactTimeline:
    """Append-only timeline of contact events. All events are mock/dry-run only."""

    def __init__(self):
        self._events: list[ContactEvent] = []

    @property
    def count(self) -> int:
        return len(self._events)

    @property
    def events(self) -> list[ContactEvent]:
        return list(self._events)

    def add_event(
        self,
        event_type: str,
        summary: str = "",
        lead_id: str = "",
        deal_id: str = "",
        details: str = "",
        actor: str = "system",
    ) -> ContactEvent:
        import uuid
        event = ContactEvent(
            event_id=str(uuid.uuid4())[:12],
            lead_id=lead_id,
            deal_id=deal_id,
            event_type=event_type,
            summary=summary,
            details=details,
            actor=actor,
        )
        self._events.append(event)
        return event

    def add_note(self, summary: str, lead_id: str = "", deal_id: str = "", actor: str = "system") -> ContactEvent:
        return self.add_event(ContactEventType.NOTE.value, summary=summary, lead_id=lead_id, deal_id=deal_id, actor=actor)

    def add_call_mock(self, summary: str, lead_id: str = "", deal_id: str = "", actor: str = "system") -> ContactEvent:
        return self.add_event(ContactEventType.CALL_MOCK.value, summary=summary, lead_id=lead_id, deal_id=deal_id, actor=actor)

    def add_whatsapp_mock(self, summary: str, lead_id: str = "", deal_id: str = "", actor: str = "system") -> ContactEvent:
        return self.add_event(ContactEventType.WHATSAPP_MOCK.value, summary=summary, lead_id=lead_id, deal_id=deal_id, actor=actor)

    def filter_by_lead(self, lead_id: str) -> list[ContactEvent]:
        return [e for e in self._events if e.lead_id == lead_id]

    def filter_by_deal(self, deal_id: str) -> list[ContactEvent]:
        return [e for e in self._events if e.deal_id == deal_id]

    def filter_by_type(self, event_type: str) -> list[ContactEvent]:
        return [e for e in self._events if e.event_type == event_type]

    def filter_by_date_range(self, start: str, end: str) -> list[ContactEvent]:
        return [e for e in self._events if start <= e.timestamp <= end]

    def list_all(self) -> list[ContactEvent]:
        return list(self._events)

    def to_dict_list(self) -> list[dict]:
        return [e.to_dict() for e in self._events]

    @classmethod
    def from_dict_list(cls, events: list[dict]) -> "ContactTimeline":
        timeline = cls()
        timeline._events = [ContactEvent.from_dict(d) for d in events]
        return timeline

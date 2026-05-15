"""W115 — Follow-up Scheduler for Sales/CRM."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum

DAYS_SEQUENCE = [1, 3, 7, 14]  # D+1, D+3, D+7, D+14


class FollowUpStatus(str, Enum):
    SCHEDULED = "scheduled"
    DUE = "due"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class FollowUpStep:
    """A single follow-up action in a sequence."""

    step_id: str
    sequence_id: str = ""
    step_number: int = 1
    due_date: str = ""
    action_type: str = "whatsapp_mock"  # whatsapp_mock, call_mock, email_mock, telegram_mock
    template: str = ""
    status: str = FollowUpStatus.SCHEDULED.value
    completed_at: str = ""
    notes: str = ""
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "sequence_id": self.sequence_id,
            "step_number": self.step_number,
            "due_date": self.due_date,
            "action_type": self.action_type,
            "template": self.template,
            "status": self.status,
            "completed_at": self.completed_at,
            "notes": self.notes,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FollowUpStep":
        return cls(
            step_id=d.get("step_id", ""),
            sequence_id=d.get("sequence_id", ""),
            step_number=d.get("step_number", 1),
            due_date=d.get("due_date", ""),
            action_type=d.get("action_type", "whatsapp_mock"),
            template=d.get("template", ""),
            status=d.get("status", FollowUpStatus.SCHEDULED.value),
            completed_at=d.get("completed_at", ""),
            notes=d.get("notes", ""),
            dry_run=d.get("dry_run", True),
        )

    @property
    def is_pending(self) -> bool:
        return self.status in {FollowUpStatus.SCHEDULED.value, FollowUpStatus.DUE.value}


@dataclass
class FollowUpSequence:
    """A complete follow-up sequence for a lead/deal."""

    sequence_id: str
    lead_id: str = ""
    deal_id: str = ""
    steps: list[FollowUpStep] = field(default_factory=list)
    dry_run: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def pending_count(self) -> int:
        return sum(1 for s in self.steps if s.is_pending)

    def to_dict(self) -> dict:
        return {
            "sequence_id": self.sequence_id,
            "lead_id": self.lead_id,
            "deal_id": self.deal_id,
            "steps": [s.to_dict() for s in self.steps],
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FollowUpSequence":
        seq = cls(
            sequence_id=d.get("sequence_id", ""),
            lead_id=d.get("lead_id", ""),
            deal_id=d.get("deal_id", ""),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", ""),
        )
        seq.steps = [FollowUpStep.from_dict(s) for s in d.get("steps", [])]
        return seq

    def to_markdown(self) -> str:
        lines = [
            f"# Follow-Up Sequence: {self.sequence_id}",
            f"**Lead:** {self.lead_id} | **Deal:** {self.deal_id}",
            f"**Steps:** {self.step_count} | **Pending:** {self.pending_count}",
            "",
            "| # | Due Date | Action | Status | Template |",
            "|---|---|---|---|---|",
        ]
        for s in self.steps:
            lines.append(
                f"| {s.step_number} | {s.due_date} | {s.action_type} | {s.status} | {s.template[:40]} |"
            )
        return "\n".join(lines)


class FollowUpScheduler:
    """Generates follow-up sequences — zero real sends."""

    TEMPLATES = {
        1: "D+1: Olá {name}! Foi ótimo conversar com você. Fico à disposição para qualquer dúvida.",
        2: "D+3: Olá {name}! Passando para saber se você já conseguiu avaliar nossa proposta?",
        3: "D+7: Olá {name}! Não esqueça que nossa oferta especial está disponível até o fim do mês.",
        4: "D+14: Olá {name}! Último contato — se precisar de algo, estamos aqui. Abs!",
    }

    def generate_sequence(
        self,
        lead_id: str = "",
        deal_id: str = "",
        start_date: str | None = None,
    ) -> FollowUpSequence:
        import uuid

        if start_date is None:
            base = datetime.now(timezone.utc)
        else:
            base = datetime.fromisoformat(start_date)

        sequence = FollowUpSequence(
            sequence_id=str(uuid.uuid4())[:12],
            lead_id=lead_id,
            deal_id=deal_id,
        )

        for i, offset_days in enumerate(DAYS_SEQUENCE, start=1):
            due = base + timedelta(days=offset_days)
            step = FollowUpStep(
                step_id=str(uuid.uuid4())[:12],
                sequence_id=sequence.sequence_id,
                step_number=i,
                due_date=due.strftime("%Y-%m-%d"),
                action_type="whatsapp_mock",
                template=self.TEMPLATES.get(i, f"D+{offset_days}: Follow-up step {i}"),
                status=FollowUpStatus.SCHEDULED.value,
            )
            sequence.steps.append(step)

        return sequence

    def mark_due(self, sequence: FollowUpSequence) -> list[FollowUpStep]:
        due: list[FollowUpStep] = []
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for step in sequence.steps:
            if step.due_date <= today and step.status == FollowUpStatus.SCHEDULED.value:
                step.status = FollowUpStatus.DUE.value
                due.append(step)
        return due

    def complete_step(self, step: FollowUpStep, notes: str = "") -> FollowUpStep:
        step.status = FollowUpStatus.COMPLETED.value
        step.completed_at = datetime.now(timezone.utc).isoformat()
        if notes:
            step.notes = notes
        return step

    def skip_step(self, step: FollowUpStep, reason: str = "") -> FollowUpStep:
        step.status = FollowUpStatus.SKIPPED.value
        if reason:
            step.notes = reason
        return step

    def cancel_sequence(self, sequence: FollowUpSequence) -> FollowUpSequence:
        for step in sequence.steps:
            if step.is_pending:
                step.status = FollowUpStatus.CANCELLED.value
        return sequence

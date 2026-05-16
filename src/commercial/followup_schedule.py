"""W128 — Follow-Up Schedule Optimizer.

Builds a calendar/schedule layer on top of OutreachSequencer (W123).
Does NOT recreate templates or steps — reads sequences and adds:
- Calendar of due dates per lead
- Overdue detection
- Priority-based reordering suggestions
- Next-best-action per lead
- Schedule reports

All dry-run, zero message sending, zero API.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from src.commercial.hotel_lead import HotelLead
from src.commercial.outreach_sequence import (
    OutreachSequencer, OutreachSequence, OutreachStep, StepStatus,
)
from src.commercial.pipeline_sync import PipelineSyncEntry, SyncStage


# ── Follow-Up Entry ─────────────────────────────────────────────────────────

@dataclass
class FollowUpEntry:
    """Single follow-up action entry — calendar slot for one lead."""

    entry_id: str
    hotel_lead_id: str
    hotel_name: str

    # Source data
    sequence_id: str = ""
    step_number: int = 0
    step_label: str = ""
    channel: str = ""
    call_to_action: str = ""

    # Timing
    due_date: str = ""  # ISO date
    days_until_due: int = 0
    is_overdue: bool = False
    overdue_days: int = 0

    # Priority
    fit_score: int = 0
    priority_tier: str = ""
    suggested_stage: str = ""
    priority_rank: int = 99  # lower = higher priority

    # Status
    step_status: str = ""
    dry_run: bool = True

    @property
    def is_actionable(self) -> bool:
        return self.step_status in ("ready", "pending") and not self.is_overdue

    @property
    def urgency(self) -> str:
        if self.is_overdue and self.overdue_days >= 5:
            return "critical"
        if self.is_overdue:
            return "overdue"
        if self.days_until_due <= 1:
            return "imminent"
        if self.days_until_due <= 3:
            return "soon"
        return "scheduled"

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "hotel_lead_id": self.hotel_lead_id,
            "hotel_name": self.hotel_name,
            "sequence_id": self.sequence_id,
            "step_number": self.step_number,
            "step_label": self.step_label,
            "channel": self.channel,
            "call_to_action": self.call_to_action,
            "due_date": self.due_date,
            "days_until_due": self.days_until_due,
            "is_overdue": self.is_overdue,
            "overdue_days": self.overdue_days,
            "fit_score": self.fit_score,
            "priority_tier": self.priority_tier,
            "suggested_stage": self.suggested_stage,
            "priority_rank": self.priority_rank,
            "step_status": self.step_status,
            "dry_run": self.dry_run,
        }


# ── Follow-Up Schedule ──────────────────────────────────────────────────────

class FollowUpSchedule:
    """Builds a follow-up calendar from OutreachSequencer data.

    Reads sequences (W123) and optionally PipelineSyncEntry (W127) to produce
    prioritized follow-up schedule with overdue detection.
    """

    def build(
        self,
        sequencer: OutreachSequencer,
        sync_entries: list[PipelineSyncEntry] | None = None,
        reference_date: str | None = None,
    ) -> list[FollowUpEntry]:
        """Build follow-up schedule from active sequences.

        Args:
            sequencer: W123 OutreachSequencer with generated sequences
            sync_entries: Optional W127 PipelineSyncEntry list for stage/priority enrichment
            reference_date: ISO date to calculate due/overdue (defaults to now)

        Returns:
            Sorted list of FollowUpEntry (highest priority first)
        """
        import uuid

        # Build sync lookup
        sync_by_id: dict[str, PipelineSyncEntry] = {}
        if sync_entries:
            for se in sync_entries:
                sync_by_id[se.hotel_lead_id] = se

        # Parse reference date
        if reference_date:
            ref = datetime.fromisoformat(reference_date.replace("Z", "+00:00"))
        else:
            ref = datetime.now(timezone.utc)

        entries: list[FollowUpEntry] = []

        for seq in sequencer.list_all():
            if seq.status not in ("active", "draft"):
                continue

            sync = sync_by_id.get(seq.hotel_lead_id)
            fit = sync.fit_score if sync else 0
            priority_tier = sync.priority_tier if sync else ""
            stage = sync.suggested_stage if sync else ""

            for step in seq.steps:
                if step.status not in (StepStatus.READY, StepStatus.PENDING):
                    continue

                # Calculate due date from sequence creation + delay
                if seq.created_at:
                    base = datetime.fromisoformat(seq.created_at.replace("Z", "+00:00"))
                else:
                    base = ref
                target = base + timedelta(days=step.delay_days)
                due_date = target.isoformat()

                diff = target - ref
                days_until = diff.days
                is_overdue = days_until < 0
                overdue_days = abs(days_until) if is_overdue else 0

                # Priority ranking: fit_score + overdue penalty + tier bonus
                rank = 100 - fit if fit > 0 else 99
                if is_overdue:
                    rank -= min(overdue_days * 2, 30)  # overdue penalty up to -30
                if priority_tier == "hot":
                    rank -= 15
                elif priority_tier == "warm":
                    rank -= 5

                cta = step.message.call_to_action if step.message else ""

                entries.append(FollowUpEntry(
                    entry_id=str(uuid.uuid4())[:12],
                    hotel_lead_id=seq.hotel_lead_id,
                    hotel_name=seq.hotel_name,
                    sequence_id=seq.sequence_id,
                    step_number=step.step_number,
                    step_label=step.label,
                    channel=step.channel.value if hasattr(step.channel, 'value') else str(step.channel),
                    call_to_action=cta,
                    due_date=due_date,
                    days_until_due=days_until,
                    is_overdue=is_overdue,
                    overdue_days=overdue_days,
                    fit_score=fit,
                    priority_tier=priority_tier,
                    suggested_stage=stage,
                    priority_rank=rank,
                    step_status=step.status.value if hasattr(step.status, 'value') else str(step.status),
                    dry_run=True,
                ))

        # Sort by priority_rank (lowest = highest priority)
        entries.sort(key=lambda e: e.priority_rank)
        return entries

    def build_from_prospect_list(
        self,
        sequencer: OutreachSequencer,
        prospect_list,
        sync_entries: list[PipelineSyncEntry] | None = None,
        reference_date: str | None = None,
    ) -> list[FollowUpEntry]:
        """Build schedule filtered to entries in ProspectList."""
        all_entries = self.build(sequencer, sync_entries, reference_date)
        valid_ids = {e.hotel_lead.hotel_lead_id for e in prospect_list.list_all()}
        return [fe for fe in all_entries if fe.hotel_lead_id in valid_ids]

    def detect_overdue(self, entries: list[FollowUpEntry]) -> list[FollowUpEntry]:
        """Return only overdue entries, sorted by urgency."""
        overdue = [e for e in entries if e.is_overdue]
        overdue.sort(key=lambda e: (-e.overdue_days, e.priority_rank))
        return overdue

    def suggest_priority(self, entries: list[FollowUpEntry]) -> list[FollowUpEntry]:
        """Return entries re-sorted by suggested priority (highest first)."""
        return sorted(entries, key=lambda e: e.priority_rank)

    def next_best_action(self, entries: list[FollowUpEntry]) -> FollowUpEntry | None:
        """Return the single highest-priority action to take next."""
        actionable = [e for e in entries if e.step_status in ("ready", "pending")]
        if not actionable:
            return None
        return min(actionable, key=lambda e: e.priority_rank)

    def summary_by_urgency(self, entries: list[FollowUpEntry]) -> dict:
        """Count entries by urgency level."""
        counts: dict[str, int] = {}
        for e in entries:
            counts[e.urgency] = counts.get(e.urgency, 0) + 1
        return counts

    def export_schedule_report(self, entries: list[FollowUpEntry]) -> str:
        """Generate markdown calendar report."""
        urgency_summary = self.summary_by_urgency(entries)
        overdue = self.detect_overdue(entries)
        next_best = self.next_best_action(entries)

        lines = [
            "# Follow-Up Schedule Report",
            f"**Total actions:** {len(entries)}",
            f"**Overdue:** {len(overdue)} | **Next best:** {next_best.hotel_name if next_best else '—'}",
            "",
            "## Urgency Breakdown",
            "",
        ]
        for level in ("critical", "overdue", "imminent", "soon", "scheduled"):
            count = urgency_summary.get(level, 0)
            if count > 0:
                lines.append(f"- **{level}:** {count}")

        if overdue:
            lines.extend([
                "",
                "## Overdue Actions",
                "",
            ])
            lines.append("| # | Hotel | Days Overdue | Step | Channel | Priority |")
            lines.append("|---|---|---|---|---|---|")
            for i, e in enumerate(overdue, 1):
                lines.append(
                    f"| {i} | {e.hotel_name} | {e.overdue_days}d | "
                    f"{e.step_label} | {e.channel} | {e.priority_tier or '—'} |"
                )

        lines.extend([
            "",
            "## Scheduled Actions (by priority)",
            "",
        ])
        lines.append("| # | Hotel | Due | Step | Channel | Urgency | Stage |")
        lines.append("|---|---|---|---|---|---|---|")
        for i, e in enumerate(entries, 1):
            due_short = e.due_date[:10] if e.due_date else "—"
            lines.append(
                f"| {i} | {e.hotel_name} | {due_short} | "
                f"{e.step_label} | {e.channel} | {e.urgency} | {e.suggested_stage or '—'} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "**Disclaimer:** Schedule generated by OMNIS Commercial SDR.",
            "All actions are suggestions only — no messages have been sent.",
            "**dry_run:** True",
        ])
        return "\n".join(lines)

    def export_calendar_dict(self, entries: list[FollowUpEntry]) -> dict:
        """Export entries grouped by due date for calendar integration."""
        calendar: dict[str, list[dict]] = {}
        for e in entries:
            date_key = e.due_date[:10] if e.due_date else "unknown"
            if date_key not in calendar:
                calendar[date_key] = []
            calendar[date_key].append({
                "hotel_name": e.hotel_name,
                "channel": e.channel,
                "step": e.step_label,
                "urgency": e.urgency,
                "priority_rank": e.priority_rank,
            })
        return calendar

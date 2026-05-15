"""Tests for W115 — Follow-up Scheduler."""
from __future__ import annotations

import pytest

from src.sales.followups import (
    FollowUpScheduler,
    FollowUpSequence,
    FollowUpStep,
    FollowUpStatus,
    DAYS_SEQUENCE,
)


class TestFollowUpStep:
    def test_create_step(self):
        step = FollowUpStep(step_id="s1", step_number=1, due_date="2026-05-16")
        assert step.step_id == "s1"
        assert step.step_number == 1
        assert step.status == "scheduled"
        assert step.dry_run is True

    def test_is_pending(self):
        step = FollowUpStep(step_id="s1", step_number=1, due_date="2026-05-16")
        assert step.is_pending is True

    def test_not_pending_after_complete(self):
        step = FollowUpStep(step_id="s1", step_number=1, due_date="2026-05-16")
        step.status = FollowUpStatus.COMPLETED.value
        assert step.is_pending is False

    def test_to_dict_roundtrip(self):
        step = FollowUpStep(
            step_id="s1",
            sequence_id="seq1",
            step_number=2,
            due_date="2026-05-18",
            action_type="whatsapp_mock",
            template="Olá {name}, follow-up D+3!",
        )
        d = step.to_dict()
        restored = FollowUpStep.from_dict(d)
        assert restored.step_id == "s1"
        assert restored.sequence_id == "seq1"
        assert restored.step_number == 2
        assert restored.template == "Olá {name}, follow-up D+3!"


class TestFollowUpSequence:
    def test_create_empty(self):
        seq = FollowUpSequence(sequence_id="seq1")
        assert seq.sequence_id == "seq1"
        assert seq.step_count == 0
        assert seq.dry_run is True

    def test_with_steps(self):
        seq = FollowUpSequence(sequence_id="seq2")
        seq.steps = [
            FollowUpStep(step_id="s1", step_number=1, due_date="2026-05-16"),
            FollowUpStep(step_id="s2", step_number=2, due_date="2026-05-18"),
        ]
        assert seq.step_count == 2
        assert seq.pending_count == 2

    def test_pending_count_mixed(self):
        seq = FollowUpSequence(sequence_id="seq3")
        seq.steps = [
            FollowUpStep(step_id="s1", step_number=1, due_date="2026-05-16"),
            FollowUpStep(step_id="s2", step_number=2, due_date="2026-05-18", status=FollowUpStatus.COMPLETED.value),
            FollowUpStep(step_id="s3", step_number=3, due_date="2026-05-22"),
        ]
        assert seq.pending_count == 2

    def test_to_dict_roundtrip(self):
        seq = FollowUpSequence(sequence_id="seq4", lead_id="l1", deal_id="d1")
        seq.steps = [FollowUpStep(step_id="s1", step_number=1)]
        d = seq.to_dict()
        restored = FollowUpSequence.from_dict(d)
        assert restored.sequence_id == "seq4"
        assert restored.step_count == 1

    def test_to_markdown(self):
        seq = FollowUpSequence(sequence_id="seq5", lead_id="l1")
        seq.steps = [FollowUpStep(step_id="s1", step_number=1, due_date="2026-05-16")]
        md = seq.to_markdown()
        assert "seq5" in md
        assert "2026-05-16" in md


class TestFollowUpScheduler:
    def setup_method(self):
        self.scheduler = FollowUpScheduler()

    def test_generates_4_steps(self):
        seq = self.scheduler.generate_sequence(lead_id="l1", deal_id="d1")
        assert seq.step_count == 4
        assert seq.lead_id == "l1"
        assert seq.deal_id == "d1"

    def test_steps_have_templates(self):
        seq = self.scheduler.generate_sequence(lead_id="l1")
        for i, step in enumerate(seq.steps, start=1):
            assert step.template != ""
            assert f"D+{DAYS_SEQUENCE[i-1]}" in step.template or "D+" in step.template

    def test_respects_cadence_dates(self):
        seq = self.scheduler.generate_sequence(
            lead_id="l1", start_date="2026-05-15"
        )
        assert seq.steps[0].due_date == "2026-05-16"  # D+1
        assert seq.steps[1].due_date == "2026-05-18"  # D+3
        assert seq.steps[2].due_date == "2026-05-22"  # D+7
        assert seq.steps[3].due_date == "2026-05-29"  # D+14

    def test_all_steps_scheduled_initially(self):
        seq = self.scheduler.generate_sequence(lead_id="l1")
        assert all(s.status == FollowUpStatus.SCHEDULED.value for s in seq.steps)

    def test_no_real_sends(self):
        seq = self.scheduler.generate_sequence(lead_id="l1")
        assert seq.dry_run is True
        assert all(s.dry_run for s in seq.steps)
        assert all(s.action_type == "whatsapp_mock" for s in seq.steps)

    def test_mark_due(self):
        today = "2026-05-15"
        seq = self.scheduler.generate_sequence(lead_id="l1", start_date="2026-05-01")
        due_steps = self.scheduler.mark_due(seq)
        assert len(due_steps) == 4  # all are in the past relative to today

    def test_complete_step(self):
        seq = self.scheduler.generate_sequence(lead_id="l1")
        step = seq.steps[0]
        self.scheduler.complete_step(step, notes="Cliente respondeu positivamente")
        assert step.status == FollowUpStatus.COMPLETED.value
        assert step.notes == "Cliente respondeu positivamente"

    def test_skip_step(self):
        seq = self.scheduler.generate_sequence(lead_id="l1")
        step = seq.steps[1]
        self.scheduler.skip_step(step, reason="Cliente pediu para pular")
        assert step.status == FollowUpStatus.SKIPPED.value

    def test_cancel_sequence(self):
        seq = self.scheduler.generate_sequence(lead_id="l1")
        self.scheduler.cancel_sequence(seq)
        assert all(s.status == FollowUpStatus.CANCELLED.value for s in seq.steps)

    def test_cancel_only_pending(self):
        seq = self.scheduler.generate_sequence(lead_id="l1")
        self.scheduler.complete_step(seq.steps[0])
        self.scheduler.cancel_sequence(seq)
        assert seq.steps[0].status == FollowUpStatus.COMPLETED.value  # stays completed
        assert all(s.status == FollowUpStatus.CANCELLED.value for s in seq.steps[1:])

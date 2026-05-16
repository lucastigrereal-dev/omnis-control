"""Tests for W123 — OutreachSequence + OutreachSequencer."""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path

from src.sales.leads import Lead
from src.commercial.hotel_lead import HotelLead
from src.commercial.prospect_list import ProspectList
from src.commercial.outreach_sequence import (
    OutreachChannel,
    StepStatus,
    CADENCE_DAYS,
    CADENCE_LABELS,
    OutreachMessage,
    OutreachStep,
    OutreachSequence,
    OutreachSequencer,
    _generate_message,
)


class TestOutreachMessage:
    def test_create_message(self):
        msg = OutreachMessage(
            message_id="m1", step_label="D+0 — Abertura",
            channel=OutreachChannel.EMAIL, body="Ola, tudo bem?",
            call_to_action="Responder",
        )
        assert msg.message_id == "m1"
        assert msg.body == "Ola, tudo bem?"
        assert msg.sent is False
        assert msg.dry_run is True
        assert msg.requires_approval is True

    def test_to_dict_roundtrip(self):
        msg = OutreachMessage(
            message_id="m1", step_label="D+2 — Reforco",
            channel=OutreachChannel.WHATSAPP,
            body="Mensagem de teste", call_to_action="Responder",
        )
        d = msg.to_dict()
        restored = OutreachMessage.from_dict(d)
        assert restored.message_id == "m1"
        assert restored.channel == OutreachChannel.WHATSAPP
        assert restored.body == "Mensagem de teste"
        assert restored.sent is False


class TestOutreachStep:
    def test_create_step(self):
        step = OutreachStep(
            step_id="s1", sequence_id="seq1", step_number=1,
            delay_days=0, label="D+0 — Abertura",
            channel=OutreachChannel.EMAIL,
        )
        assert step.step_number == 1
        assert step.status == StepStatus.PENDING
        assert step.dry_run is True

    def test_to_dict_roundtrip(self):
        msg = OutreachMessage(
            message_id="m1", step_label="D+0", channel=OutreachChannel.EMAIL,
            body="Teste",
        )
        step = OutreachStep(
            step_id="s1", sequence_id="seq1", step_number=2,
            delay_days=2, label="D+2 — Reforco",
            channel=OutreachChannel.INSTAGRAM_DM, message=msg,
            status=StepStatus.READY,
        )
        d = step.to_dict()
        restored = OutreachStep.from_dict(d)
        assert restored.step_id == "s1"
        assert restored.message is not None
        assert restored.message.body == "Teste"
        assert restored.status == StepStatus.READY


class TestMessageGeneration:
    def _make_hotel_lead(self) -> HotelLead:
        base = Lead(lead_id="l1", name="Hotel Sol RN", contact_channel="instagram")
        return HotelLead(
            hotel_lead_id="h1", base_lead=base, hotel_name="Hotel Sol RN Resort",
            city="Natal", state="RN", region="nordeste", hotel_tier="Premium",
            niche="resort", fit_score=85, priority_tier="hot",
        )

    def test_generate_d0_email(self):
        hl = self._make_hotel_lead()
        msg = _generate_message(hl, OutreachChannel.EMAIL, "D+0 — Abertura")
        assert "Hotel Sol RN Resort" in msg.body
        assert "Natal/RN" in msg.body
        assert msg.call_to_action != ""
        assert msg.sent is False
        assert msg.dry_run is True

    def test_generate_d0_instagram_dm(self):
        hl = self._make_hotel_lead()
        msg = _generate_message(hl, OutreachChannel.INSTAGRAM_DM, "D+0 — Abertura")
        assert "Hotel Sol RN Resort" in msg.body
        assert "@lucastigrereal" in msg.body

    def test_generate_d0_whatsapp(self):
        hl = self._make_hotel_lead()
        msg = _generate_message(hl, OutreachChannel.WHATSAPP, "D+0 — Abertura")
        assert "Hotel Sol RN Resort" in msg.body
        assert "2.3M+" in msg.body

    def test_generate_d0_call(self):
        hl = self._make_hotel_lead()
        msg = _generate_message(hl, OutreachChannel.CALL, "D+0 — Abertura")
        assert "Roteiro de ligacao" in msg.body
        assert "Hotel Sol RN Resort" in msg.body

    def test_generate_d0_manual(self):
        hl = self._make_hotel_lead()
        msg = _generate_message(hl, OutreachChannel.MANUAL, "D+0 — Abertura")
        assert "Contato manual" in msg.body
        assert "Hotel Sol RN Resort" in msg.body

    def test_generate_d2_email(self):
        hl = self._make_hotel_lead()
        msg = _generate_message(hl, OutreachChannel.EMAIL, "D+2 — Reforco")
        assert "Hotel Sol RN Resort" in msg.body
        assert "media kit" in msg.body.lower()

    def test_generate_d5_email(self):
        hl = self._make_hotel_lead()
        msg = _generate_message(hl, OutreachChannel.EMAIL, "D+5 — Ultimo contato")
        assert "ultima" in msg.body.lower()
        assert "Hotel Sol RN Resort" in msg.body

    def test_generate_d2_premium_highlight(self):
        hl = self._make_hotel_lead()  # Premium, fit_score=85 → is_premium_candidate
        msg = _generate_message(hl, OutreachChannel.EMAIL, "D+2 — Reforco")
        assert "Premium" in msg.body

    def test_all_channels_produce_body(self):
        hl = self._make_hotel_lead()
        for ch in OutreachChannel:
            msg = _generate_message(hl, ch, "D+0 — Abertura")
            assert len(msg.body) > 10
            assert msg.sent is False
            assert msg.requires_approval is True

    def test_no_real_send(self):
        hl = self._make_hotel_lead()
        for ch in OutreachChannel:
            for label in CADENCE_LABELS:
                msg = _generate_message(hl, ch, label)
                assert msg.sent is False, f"sent=True for {ch}/{label}"


class TestOutreachSequence:
    def _make_hotel_lead(self) -> HotelLead:
        base = Lead(lead_id="l1", name="Hotel Test", contact_channel="instagram")
        return HotelLead(
            hotel_lead_id="h1", base_lead=base, hotel_name="Hotel Test",
            city="Natal", state="RN", region="nordeste", hotel_tier="Growth",
            niche="hotel", fit_score=75, priority_tier="hot",
        )

    def test_create_empty_sequence(self):
        seq = OutreachSequence(sequence_id="s1", hotel_lead_id="h1")
        assert seq.total_steps == 0
        assert seq.status == "draft"
        assert seq.dry_run is True

    def test_next_action_no_steps(self):
        seq = OutreachSequence(sequence_id="s1", hotel_lead_id="h1")
        assert seq.next_action is None

    def test_complete_step(self):
        seq = OutreachSequence(sequence_id="s1", hotel_lead_id="h1")
        step = OutreachStep(
            step_id="st1", sequence_id="s1", step_number=1, delay_days=0,
            label="D+0", channel=OutreachChannel.EMAIL, status=StepStatus.READY,
        )
        seq.steps = [step]
        assert seq.complete_step(1) is True
        assert step.status == StepStatus.COMPLETED
        assert step.completed_at != ""

    def test_complete_already_completed(self):
        seq = OutreachSequence(sequence_id="s1", hotel_lead_id="h1")
        step = OutreachStep(
            step_id="st1", sequence_id="s1", step_number=1, delay_days=0,
            label="D+0", channel=OutreachChannel.EMAIL, status=StepStatus.COMPLETED,
        )
        seq.steps = [step]
        assert seq.complete_step(1) is False

    def test_skip_step(self):
        seq = OutreachSequence(sequence_id="s1", hotel_lead_id="h1")
        step = OutreachStep(
            step_id="st1", sequence_id="s1", step_number=1, delay_days=0,
            label="D+0", channel=OutreachChannel.EMAIL, status=StepStatus.READY,
        )
        seq.steps = [step]
        assert seq.skip_step(1) is True
        assert step.status == StepStatus.SKIPPED

    def test_cancel_sequence(self):
        seq = OutreachSequence(sequence_id="s1", hotel_lead_id="h1")
        steps = [
            OutreachStep(step_id="st1", sequence_id="s1", step_number=1, delay_days=0,
                         label="D+0", channel=OutreachChannel.EMAIL, status=StepStatus.READY),
            OutreachStep(step_id="st2", sequence_id="s1", step_number=2, delay_days=2,
                         label="D+2", channel=OutreachChannel.EMAIL, status=StepStatus.PENDING),
            OutreachStep(step_id="st3", sequence_id="s1", step_number=3, delay_days=5,
                         label="D+5", channel=OutreachChannel.EMAIL, status=StepStatus.PENDING),
        ]
        seq.steps = steps
        seq.status = "active"
        seq.cancel()
        assert seq.status == "cancelled"
        assert all(s.status in (StepStatus.SKIPPED, StepStatus.COMPLETED) for s in seq.steps)

    def test_to_dict_roundtrip(self):
        hl = self._make_hotel_lead()
        msg = OutreachMessage(
            message_id="m1", step_label="D+0", channel=OutreachChannel.EMAIL,
            body="Teste",
        )
        step = OutreachStep(
            step_id="st1", sequence_id="s1", step_number=1, delay_days=0,
            label="D+0", channel=OutreachChannel.EMAIL, message=msg,
        )
        seq = OutreachSequence(
            sequence_id="s1", hotel_lead_id=hl.hotel_lead_id,
            hotel_name="Hotel Test", channel=OutreachChannel.EMAIL,
            steps=[step], status="active",
        )
        d = seq.to_dict()
        restored = OutreachSequence.from_dict(d)
        assert restored.sequence_id == "s1"
        assert restored.total_steps == 1
        assert restored.steps[0].message.body == "Teste"

    def test_to_markdown(self):
        seq = OutreachSequence(
            sequence_id="s1", hotel_lead_id="h1", hotel_name="Hotel Test",
            channel=OutreachChannel.EMAIL, status="active",
        )
        msg = OutreachMessage(
            message_id="m1", step_label="D+0", channel=OutreachChannel.EMAIL,
            body="Ola, teste de mensagem.",
        )
        step = OutreachStep(
            step_id="st1", sequence_id="s1", step_number=1, delay_days=0,
            label="D+0 — Abertura", channel=OutreachChannel.EMAIL,
            message=msg, status=StepStatus.READY,
        )
        seq.steps = [step]
        md = seq.to_markdown()
        assert "Hotel Test" in md
        assert "teste de mensagem" in md
        assert "D+0" in md


class TestOutreachSequencer:
    def _make_hotel_lead(self, hotel_lead_id: str = "h1", lead_id: str = "l1",
                         hotel_name: str = "Hotel Test", priority_tier: str = "hot",
                         fit_score: int = 80, hotel_tier: str = "Premium") -> HotelLead:
        base = Lead(lead_id=lead_id, name=hotel_name, contact_channel="instagram")
        return HotelLead(
            hotel_lead_id=hotel_lead_id, base_lead=base, hotel_name=hotel_name,
            city="Natal", state="RN", region="nordeste", hotel_tier=hotel_tier,
            niche="resort", fit_score=fit_score, priority_tier=priority_tier,
        )

    def test_generate_sequence_creates_3_steps(self):
        seqr = OutreachSequencer()
        hl = self._make_hotel_lead()
        seq = seqr.generate_sequence(hl)
        assert seq.total_steps == 3
        assert seq.status == "active"
        assert seq.dry_run is True

    def test_generate_sequence_different_channels(self):
        hl = self._make_hotel_lead()
        for ch in OutreachChannel:
            seqr = OutreachSequencer(default_channel=ch)
            seq = seqr.generate_sequence(hl)
            assert seq.channel == ch
            assert seq.total_steps == 3

    def test_cadence_days_match_spec(self):
        hl = self._make_hotel_lead()
        seqr = OutreachSequencer()
        seq = seqr.generate_sequence(hl)
        for i, step in enumerate(seq.steps):
            assert step.delay_days == CADENCE_DAYS[i]
            assert step.label == CADENCE_LABELS[i]

    def test_first_step_is_ready(self):
        hl = self._make_hotel_lead()
        seqr = OutreachSequencer()
        seq = seqr.generate_sequence(hl)
        assert seq.steps[0].status == StepStatus.READY
        assert seq.steps[1].status == StepStatus.PENDING
        assert seq.steps[2].status == StepStatus.PENDING

    def test_next_action_returns_first_ready(self):
        hl = self._make_hotel_lead()
        seqr = OutreachSequencer()
        seq = seqr.generate_sequence(hl)
        na = seq.next_action
        assert na is not None
        assert na.step_number == 1
        assert na.label.startswith("D+0")

    def test_complete_and_advance(self):
        hl = self._make_hotel_lead()
        seqr = OutreachSequencer()
        seq = seqr.generate_sequence(hl)
        # Complete step 1
        seq.complete_step(1)
        # Manually activate step 2
        seq.steps[1].status = StepStatus.READY
        na = seq.next_action
        assert na is not None
        assert na.step_number == 2

    def test_complete_all_steps(self):
        hl = self._make_hotel_lead()
        seqr = OutreachSequencer()
        seq = seqr.generate_sequence(hl)
        seq.complete_step(1)
        seq.steps[1].status = StepStatus.READY
        seq.complete_step(2)
        seq.steps[2].status = StepStatus.READY
        seq.complete_step(3)
        assert seq.pending_steps == 0
        assert seq.status == "completed"

    def test_generate_for_prospect_list(self):
        seqr = OutreachSequencer()
        pl = ProspectList()
        hl1 = self._make_hotel_lead(hotel_lead_id="h1", lead_id="l1",
                                     priority_tier="hot")
        hl2 = self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2",
                                     priority_tier="warm")
        hl3 = self._make_hotel_lead(hotel_lead_id="h3", lead_id="l3",
                                     priority_tier="cold")
        pl.add(hl1)
        pl.add(hl2)
        pl.add(hl3)

        sequences = seqr.generate_for_prospect_list(pl)
        assert len(sequences) == 2  # only hot + warm
        assert seqr.count == 2

    def test_generate_for_hot_list(self):
        seqr = OutreachSequencer()
        pl = ProspectList()
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", lead_id="l1", priority_tier="hot"))
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", priority_tier="warm"))
        sequences = seqr.generate_for_hot_list(pl)
        assert len(sequences) == 1

    def test_list_due_actions(self):
        seqr = OutreachSequencer()
        hl = self._make_hotel_lead()
        seqr.generate_sequence(hl)
        due = seqr.list_due_actions()
        assert len(due) == 1
        assert due[0].step_number == 1

    def test_advance_all_ready(self):
        seqr = OutreachSequencer()
        hl1 = self._make_hotel_lead(hotel_lead_id="h1", lead_id="l1")
        hl2 = self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2")
        seqr.generate_sequence(hl1)
        seqr.generate_sequence(hl2)
        advanced = seqr.advance_all_ready()
        assert advanced == 2  # Both step 1's advanced
        # Now step 2 should be ready for both
        due = seqr.list_due_actions()
        assert len(due) == 2
        assert all(s.step_number == 2 for s in due)

    def test_get_sequence(self):
        seqr = OutreachSequencer()
        hl = self._make_hotel_lead()
        seq = seqr.generate_sequence(hl)
        fetched = seqr.get(seq.sequence_id)
        assert fetched is not None
        assert fetched.sequence_id == seq.sequence_id

    def test_get_nonexistent(self):
        seqr = OutreachSequencer()
        assert seqr.get("nonexistent") is None

    def test_list_by_hotel_lead(self):
        seqr = OutreachSequencer()
        hl = self._make_hotel_lead()
        seqr.generate_sequence(hl)
        results = seqr.list_by_hotel_lead(hl.hotel_lead_id)
        assert len(results) == 1

    def test_list_active(self):
        seqr = OutreachSequencer()
        hl = self._make_hotel_lead()
        seqr.generate_sequence(hl)
        seq = seqr.generate_sequence(
            self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2")
        )
        seq.cancel()
        assert seqr.active_count == 1
        assert len(seqr.list_active()) == 1

    def test_all_messages_are_dry_run(self):
        seqr = OutreachSequencer()
        hl = self._make_hotel_lead()
        seq = seqr.generate_sequence(hl)
        for step in seq.steps:
            assert step.dry_run is True
            assert step.message is not None
            assert step.message.sent is False
            assert step.message.dry_run is True
            assert step.message.requires_approval is True

    def test_file_backed_save_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            seqr1 = OutreachSequencer(storage_dir=tmp)
            hl = self._make_hotel_lead()
            seqr1.generate_sequence(hl)

            seqr2 = OutreachSequencer.load(tmp)
            assert seqr2.count == 1

    def test_to_jsonl(self):
        seqr = OutreachSequencer()
        hl = self._make_hotel_lead()
        seqr.generate_sequence(hl)
        jsonl = seqr.to_jsonl()
        assert "Hotel Test" in jsonl

    def test_no_external_calls(self):
        seqr = OutreachSequencer()
        hl = self._make_hotel_lead()
        seq = seqr.generate_sequence(hl)
        assert seq.dry_run is True
        assert hl.dry_run is True
        assert hl.base_lead.dry_run is True

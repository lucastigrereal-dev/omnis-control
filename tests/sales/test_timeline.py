"""Tests for W114 — Contact Timeline."""
from __future__ import annotations

import pytest

from src.sales.timeline import ContactTimeline, ContactEvent, ContactEventType


class TestContactEvent:
    def test_create_event(self):
        e = ContactEvent(event_id="e1", lead_id="l1", deal_id="d1", event_type="note")
        assert e.event_id == "e1"
        assert e.lead_id == "l1"
        assert e.deal_id == "d1"
        assert e.dry_run is True

    def test_create_full_event(self):
        e = ContactEvent(
            event_id="e2",
            lead_id="l2",
            deal_id="d2",
            event_type=ContactEventType.CALL_MOCK.value,
            summary="Ligacao inicial — qualificacao",
            details="Hotel interessado no pacote Growth. Retornar em 3 dias.",
            actor="lucas",
        )
        assert e.summary == "Ligacao inicial — qualificacao"
        assert e.actor == "lucas"

    def test_to_dict_roundtrip(self):
        e = ContactEvent(
            event_id="e3",
            lead_id="l3",
            event_type=ContactEventType.WHATSAPP_MOCK.value,
            summary="Mensagem WhatsApp mock",
        )
        d = e.to_dict()
        restored = ContactEvent.from_dict(d)
        assert restored.event_id == "e3"
        assert restored.summary == "Mensagem WhatsApp mock"

    def test_timestamp_auto_set(self):
        e = ContactEvent(event_id="e4")
        assert e.timestamp != ""

    def test_dry_run_default(self):
        e = ContactEvent(event_id="e5")
        assert e.dry_run is True


class TestContactTimeline:
    def test_add_event(self):
        timeline = ContactTimeline()
        e = timeline.add_event("note", summary="Primeira nota")
        assert timeline.count == 1
        assert e.summary == "Primeira nota"

    def test_add_note(self):
        timeline = ContactTimeline()
        e = timeline.add_note("Nota de acompanhamento", lead_id="l1")
        assert e.event_type == "note"
        assert e.lead_id == "l1"

    def test_add_call_mock(self):
        timeline = ContactTimeline()
        e = timeline.add_call_mock("Ligacao de follow-up", lead_id="l1", deal_id="d1")
        assert e.event_type == "call_mock"

    def test_add_whatsapp_mock(self):
        timeline = ContactTimeline()
        e = timeline.add_whatsapp_mock("WhatsApp enviado", lead_id="l1")
        assert e.event_type == "whatsapp_mock"
        assert e.dry_run is True  # never real

    def test_append_only_order(self):
        timeline = ContactTimeline()
        e1 = timeline.add_event("note", summary="Primeiro")
        e2 = timeline.add_event("call_mock", summary="Segundo")
        e3 = timeline.add_event("note", summary="Terceiro")
        events = timeline.list_all()
        assert events[0].event_id == e1.event_id
        assert events[1].event_id == e2.event_id
        assert events[2].event_id == e3.event_id

    def test_filter_by_lead(self):
        timeline = ContactTimeline()
        timeline.add_event("note", lead_id="l1", summary="Lead 1 event")
        timeline.add_event("call_mock", lead_id="l2", summary="Lead 2 event")
        timeline.add_event("note", lead_id="l1", summary="Lead 1 another")
        assert len(timeline.filter_by_lead("l1")) == 2
        assert len(timeline.filter_by_lead("l2")) == 1

    def test_filter_by_deal(self):
        timeline = ContactTimeline()
        timeline.add_event("note", deal_id="d1", summary="Deal 1")
        timeline.add_event("call_mock", deal_id="d2", summary="Deal 2")
        assert len(timeline.filter_by_deal("d1")) == 1

    def test_filter_by_type(self):
        timeline = ContactTimeline()
        timeline.add_event("note", summary="N1")
        timeline.add_event("call_mock", summary="C1")
        timeline.add_event("note", summary="N2")
        assert len(timeline.filter_by_type("note")) == 2
        assert len(timeline.filter_by_type("call_mock")) == 1

    def test_filter_by_date_range(self):
        timeline = ContactTimeline()
        timeline.add_event("note", summary="Event A")
        import time
        time.sleep(0.01)
        mid = timeline.add_event("note", summary="Event B").timestamp
        time.sleep(0.01)
        timeline.add_event("note", summary="Event C")
        filtered = timeline.filter_by_date_range(start=mid, end=mid)
        assert len(filtered) == 1

    def test_to_dict_list_roundtrip(self):
        timeline = ContactTimeline()
        timeline.add_note("Nota 1", lead_id="l1")
        timeline.add_call_mock("Call 1", lead_id="l2")
        dlist = timeline.to_dict_list()
        restored = ContactTimeline.from_dict_list(dlist)
        assert restored.count == 2

    def test_no_real_sends(self):
        timeline = ContactTimeline()
        e = timeline.add_event(ContactEventType.WHATSAPP_MOCK.value, summary="Test")
        assert e.dry_run is True
        # All event types are *MOCK — zero real sends

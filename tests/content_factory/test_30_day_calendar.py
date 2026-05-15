"""Tests for W096 — 30-Day Content Calendar model."""
from __future__ import annotations

import pytest

from src.content_factory.brief import ContentBrief
from src.content_factory.calendar import CalendarSlot, ContentCalendar, CalendarGenerator


class TestCalendarSlot:
    def test_create_slot(self):
        slot = CalendarSlot(day=1)
        assert slot.day == 1
        assert slot.format == ""
        assert slot.pillar == ""

    def test_create_full_slot(self):
        slot = CalendarSlot(
            day=5,
            format="carousel",
            pillar="vendas",
            title="Carrossel de Vendas",
            objective="conversao",
            notes="Publicar as 10h",
        )
        assert slot.day == 5
        assert slot.format == "carousel"
        assert slot.pillar == "vendas"
        assert slot.title == "Carrossel de Vendas"
        assert slot.objective == "conversao"
        assert slot.notes == "Publicar as 10h"

    def test_to_dict_roundtrip(self):
        slot = CalendarSlot(day=10, format="reels", pillar="entretenimento")
        d = slot.to_dict()
        restored = CalendarSlot.from_dict(d)
        assert restored.day == slot.day
        assert restored.format == slot.format
        assert restored.pillar == slot.pillar


class TestContentCalendar:
    def test_create_calendar(self):
        cal = ContentCalendar(calendar_id="cal1")
        assert cal.calendar_id == "cal1"
        assert cal.slot_count == 0

    def test_format_distribution(self):
        cal = ContentCalendar(calendar_id="cal2")
        cal.slots.append(CalendarSlot(day=1, format="feed"))
        cal.slots.append(CalendarSlot(day=2, format="carousel"))
        cal.slots.append(CalendarSlot(day=3, format="feed"))
        dist = cal.format_distribution
        assert dist == {"feed": 2, "carousel": 1}

    def test_pillar_distribution(self):
        cal = ContentCalendar(calendar_id="cal3")
        cal.slots.append(CalendarSlot(day=1, pillar="educacional"))
        cal.slots.append(CalendarSlot(day=2, pillar="vendas"))
        cal.slots.append(CalendarSlot(day=3, pillar="educacional"))
        dist = cal.pillar_distribution
        assert dist == {"educacional": 2, "vendas": 1}

    def test_to_dict_roundtrip(self):
        cal = ContentCalendar(
            calendar_id="cal4",
            brand="Tigre Real",
            theme="Ferias de Verao",
            start_date="2026-06-01",
        )
        cal.slots.append(CalendarSlot(day=1, format="feed", pillar="educacional"))
        d = cal.to_dict()
        restored = ContentCalendar.from_dict(d)
        assert restored.calendar_id == cal.calendar_id
        assert restored.brand == cal.brand
        assert restored.slot_count == 1

    def test_to_markdown(self):
        cal = ContentCalendar(
            calendar_id="cal5",
            brand="Familia Tigre",
            theme="Julho 2026",
        )
        cal.slots.append(CalendarSlot(day=1, format="carousel", pillar="vendas", title="Oferta"))
        md = cal.to_markdown()
        assert "Julho 2026" in md
        assert "Familia Tigre" in md
        assert "carousel" in md
        assert "vendas" in md


class TestCalendarGenerator:
    def setup_method(self):
        self.generator = CalendarGenerator()

    def _make_brief(self) -> ContentBrief:
        return ContentBrief(
            brief_id="b_test",
            title="Turismo de Luxo",
            brand="Tigre Real",
            keywords=["turismo", "luxo", "resort"],
        )

    def test_generate_returns_calendar(self):
        brief = self._make_brief()
        cal = self.generator.generate(brief)
        assert isinstance(cal, ContentCalendar)
        assert cal.calendar_id != ""

    def test_generate_has_30_days(self):
        brief = self._make_brief()
        cal = self.generator.generate(brief)
        assert cal.slot_count == 30

    def test_generate_all_days_have_format(self):
        brief = self._make_brief()
        cal = self.generator.generate(brief)
        for slot in cal.slots:
            assert slot.format != ""

    def test_generate_all_days_have_pillar(self):
        brief = self._make_brief()
        cal = self.generator.generate(brief)
        for slot in cal.slots:
            assert slot.pillar != ""

    def test_generate_days_are_sequential(self):
        brief = self._make_brief()
        cal = self.generator.generate(brief)
        for i, slot in enumerate(cal.slots, 1):
            assert slot.day == i

    def test_generate_format_diversity(self):
        brief = self._make_brief()
        cal = self.generator.generate(brief)
        dist = cal.format_distribution
        assert len(dist) >= 3  # at least feed, carousel, reels/stories

    def test_generate_pillar_rotation(self):
        brief = self._make_brief()
        cal = self.generator.generate(brief)
        dist = cal.pillar_distribution
        pillars = set(dist.keys())
        assert "educacional" in pillars or "vendas" in pillars

    def test_generate_brand_set(self):
        brief = self._make_brief()
        cal = self.generator.generate(brief)
        assert cal.brand == brief.brand

    def test_objective_for_pillar_educacional(self):
        obj = self.generator._objective_for_pillar("educacional")
        assert obj == "autoridade"

    def test_objective_for_pillar_entretenimento(self):
        obj = self.generator._objective_for_pillar("entretenimento")
        assert obj == "alcance"

    def test_objective_for_pillar_vendas(self):
        obj = self.generator._objective_for_pillar("vendas")
        assert obj == "conversao"

    def test_objective_for_pillar_autoridade(self):
        obj = self.generator._objective_for_pillar("autoridade")
        assert obj == "autoridade"

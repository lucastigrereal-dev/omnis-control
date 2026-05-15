"""Tests for W107 — Cover Brief."""
from __future__ import annotations

import pytest

from src.video_studio.cover import CoverBrief, CoverBriefBuilder


class TestCoverBrief:
    def test_create_brief(self):
        cb = CoverBrief(brief_id="cb1")
        assert cb.brief_id == "cb1"
        assert cb.title == ""
        assert cb.dry_run is True

    def test_create_full_brief(self):
        cb = CoverBrief(
            brief_id="cb2",
            source_id="vs1",
            title="Natal Paradisiaca",
            subtitle="Descubra o paraiso no Nordeste",
            visual_direction="Foto aerea de Ponta Negra com ceu azul e coqueiros",
            subject="Turismo em Natal",
            color_mood="vibrant",
            safe_text_area="center-bottom",
            platform="instagram",
        )
        assert cb.title == "Natal Paradisiaca"
        assert cb.subtitle == "Descubra o paraiso no Nordeste"
        assert cb.visual_direction != ""
        assert cb.subject == "Turismo em Natal"
        assert cb.color_mood == "vibrant"
        assert cb.safe_text_area == "center-bottom"
        assert cb.platform == "instagram"

    def test_to_dict_roundtrip(self):
        cb = CoverBrief(
            brief_id="cb3",
            title="Test Cover",
            visual_direction="Visual direction here",
            color_mood="warm",
        )
        d = cb.to_dict()
        restored = CoverBrief.from_dict(d)
        assert restored.brief_id == cb.brief_id
        assert restored.title == cb.title
        assert restored.visual_direction == cb.visual_direction
        assert restored.color_mood == cb.color_mood

    def test_to_markdown(self):
        cb = CoverBrief(
            brief_id="cb4",
            title="Capa Teste",
            visual_direction="Direcao visual",
            color_mood="cool",
        )
        md = cb.to_markdown()
        assert "Capa Teste" in md
        assert "cool" in md
        assert "Direcao visual" in md

    def test_dry_run_default_true(self):
        cb = CoverBrief(brief_id="cb5")
        assert cb.dry_run is True

    def test_no_real_image(self):
        cb = CoverBrief(brief_id="cb6", visual_direction="Mock direction only")
        # visual_direction is text only — no image processing
        assert isinstance(cb.visual_direction, str)


class TestCoverBriefBuilder:
    def setup_method(self):
        self.builder = CoverBriefBuilder()

    def test_build_basic_cover(self):
        cb = self.builder.build(
            source_id="vs1",
            title="Turismo em Natal",
            tags=["turismo", "praia"],
            city="Natal",
        )
        assert cb.title == "Turismo em Natal"
        assert cb.subject == "Turismo em Natal"
        assert "Natal" in cb.subtitle
        assert cb.visual_direction != ""

    def test_build_from_hook(self):
        cb = self.builder.build_from_hook(
            source_id="vs1",
            hook_text="Voce ja imaginou acordar com essa vista em Natal?",
            city="Natal",
        )
        assert cb.title != ""
        assert "Natal" in cb.subtitle

    def test_build_detects_mood_from_tags(self):
        cb = self.builder.build(
            source_id="vs1",
            title="Gastronomia",
            tags=["gastronomia", "restaurante"],
        )
        assert cb.color_mood == "warm"

    def test_build_default_mood(self):
        cb = self.builder.build(
            source_id="vs1",
            title="Viagem",
            tags=["desconhecido"],
        )
        assert cb.color_mood == "vibrant"

    def test_build_with_empty_tags(self):
        cb = self.builder.build(source_id="vs1", title="Viagem")
        assert cb.color_mood == "vibrant"

    def test_detect_mood_turismo(self):
        mood = self.builder._detect_mood(["turismo"])
        assert mood == "vibrant"

    def test_detect_mood_gastronomia(self):
        mood = self.builder._detect_mood(["gastronomia"])
        assert mood == "warm"

    def test_detect_mood_hotel(self):
        mood = self.builder._detect_mood(["hotel"])
        assert mood == "warm"

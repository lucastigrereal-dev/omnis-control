"""Tests for W094 — Reel Script Package model."""
from __future__ import annotations

import pytest

from src.content_factory.brief import ContentBrief
from src.content_factory.reels import Scene, ReelScriptPackage, ReelScriptBuilder


class TestScene:
    def test_create_scene(self):
        s = Scene(index=1)
        assert s.index == 1
        assert s.duration_seconds == 3.0

    def test_create_full_scene(self):
        s = Scene(
            index=2,
            description="Cena dramatica",
            narration="Narrador fala...",
            on_screen_text="Texto na tela",
            b_roll_suggestion="Drone shot",
            duration_seconds=5.0,
        )
        assert s.description == "Cena dramatica"
        assert s.narration == "Narrador fala..."
        assert s.on_screen_text == "Texto na tela"
        assert s.b_roll_suggestion == "Drone shot"
        assert s.duration_seconds == 5.0

    def test_to_dict_roundtrip(self):
        s = Scene(index=3, description="Test", duration_seconds=7.0)
        d = s.to_dict()
        restored = Scene.from_dict(d)
        assert restored.index == s.index
        assert restored.description == s.description
        assert restored.duration_seconds == s.duration_seconds

    def test_from_dict_defaults(self):
        d = {"index": 4}
        s = Scene.from_dict(d)
        assert s.index == 4
        assert s.duration_seconds == 3.0
        assert s.description == ""


class TestReelScriptPackage:
    def test_create_package(self):
        pkg = ReelScriptPackage(package_id="r1", brief_id="b1")
        assert pkg.package_id == "r1"
        assert pkg.scene_count == 0
        assert pkg.total_duration == 0.0
        assert pkg.target_duration_seconds == 30.0

    def test_total_duration_sums_scenes(self):
        pkg = ReelScriptPackage(package_id="r2", brief_id="b2")
        pkg.scenes.append(Scene(index=1, duration_seconds=5.0))
        pkg.scenes.append(Scene(index=2, duration_seconds=7.0))
        pkg.scenes.append(Scene(index=3, duration_seconds=3.0))
        assert pkg.total_duration == 15.0
        assert pkg.scene_count == 3

    def test_to_dict_roundtrip(self):
        pkg = ReelScriptPackage(
            package_id="r3",
            brief_id="b3",
            title="Meu Reel",
            hook="Hook impactante!",
            cta="Arrasta pra cima!",
            target_duration_seconds=15.0,
        )
        pkg.scenes.append(Scene(index=1, narration="Fala 1", duration_seconds=5.0))
        d = pkg.to_dict()
        restored = ReelScriptPackage.from_dict(d)
        assert restored.package_id == pkg.package_id
        assert restored.hook == pkg.hook
        assert restored.scene_count == 1
        assert restored.total_duration == 5.0

    def test_to_markdown(self):
        pkg = ReelScriptPackage(
            package_id="r4",
            brief_id="b4",
            title="Reel Test",
            hook="Hook MD!",
            cta="CTA MD!",
        )
        pkg.scenes.append(Scene(index=1, narration="Narracao teste", duration_seconds=3.0))
        md = pkg.to_markdown()
        assert "Reel Test" in md
        assert "Hook MD!" in md
        assert "Narracao teste" in md
        assert "CTA MD!" in md

    def test_dry_run_default_true(self):
        pkg = ReelScriptPackage(package_id="r5", brief_id="b5")
        assert pkg.dry_run is True


class TestReelScriptBuilder:
    def setup_method(self):
        self.builder = ReelScriptBuilder()

    def _make_brief(self) -> ContentBrief:
        return ContentBrief(
            brief_id="b_test",
            title="Resort em Natal",
            brand="Natal Ai Vou Eu",
            cta="Arrasta pra cima!",
            keywords=["turismo", "praia"],
        )

    def test_build_returns_package(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert isinstance(pkg, ReelScriptPackage)
        assert pkg.package_id != ""

    def test_build_has_min_scenes(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert pkg.scene_count >= ReelScriptBuilder.MIN_SCENES

    def test_build_has_hook(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert pkg.hook != ""

    def test_build_all_scenes_have_duration(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        for s in pkg.scenes:
            assert s.duration_seconds > 0

    def test_build_scenes_are_sequential(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        for i, s in enumerate(pkg.scenes, 1):
            assert s.index == i

    def test_build_last_scene_is_cta(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert "CTA" in pkg.scenes[-1].description or pkg.cta != ""

    def test_build_target_duration_set(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert pkg.target_duration_seconds > 0

    def test_build_brief_id_matches(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert pkg.brief_id == brief.brief_id

    def test_build_with_autoridade_hook(self):
        brief = self._make_brief()
        brief.objective = "autoridade"
        pkg = self.builder.build(brief)
        assert pkg.hook != ""

    def test_build_with_conversao_hook(self):
        brief = self._make_brief()
        brief.objective = "conversao"
        pkg = self.builder.build(brief)
        assert pkg.hook != ""

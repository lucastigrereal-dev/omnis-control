"""Tests for W093 — Carousel Package model."""
from __future__ import annotations

import pytest

from src.content_factory.brief import ContentBrief
from src.content_factory.carousel import CarouselSlide, CarouselPackage, CarouselBuilder


class TestCarouselSlide:
    def test_create_slide(self):
        slide = CarouselSlide(index=1, title="Hook")
        assert slide.index == 1
        assert slide.title == "Hook"
        assert slide.content == ""
        assert slide.image_description == ""

    def test_create_full_slide(self):
        slide = CarouselSlide(
            index=2,
            title="O Problema",
            content="Muita gente nao sabe...",
            image_description="Pessoa confusa",
            overlay_text="O desafio",
        )
        assert slide.index == 2
        assert slide.content == "Muita gente nao sabe..."
        assert slide.image_description == "Pessoa confusa"
        assert slide.overlay_text == "O desafio"

    def test_to_dict_roundtrip(self):
        slide = CarouselSlide(
            index=3,
            title="Solucao",
            content="A solucao e...",
            image_description="Produto",
            overlay_text="A solucao",
        )
        d = slide.to_dict()
        restored = CarouselSlide.from_dict(d)
        assert restored.index == slide.index
        assert restored.title == slide.title
        assert restored.content == slide.content

    def test_from_dict_missing_optional(self):
        d = {"index": 4}
        slide = CarouselSlide.from_dict(d)
        assert slide.index == 4
        assert slide.title == ""


class TestCarouselPackage:
    def _make_slide(self, idx: int) -> CarouselSlide:
        return CarouselSlide(index=idx, title=f"Slide {idx}")

    def test_create_package(self):
        pkg = CarouselPackage(package_id="p1", brief_id="b1")
        assert pkg.package_id == "p1"
        assert pkg.brief_id == "b1"
        assert pkg.slide_count == 0

    def test_add_slides(self):
        pkg = CarouselPackage(package_id="p2", brief_id="b2")
        pkg.slides.append(self._make_slide(1))
        pkg.slides.append(self._make_slide(2))
        assert pkg.slide_count == 2

    def test_to_dict_roundtrip(self):
        pkg = CarouselPackage(
            package_id="p3",
            brief_id="b3",
            title="Carrossel de Teste",
            cta_final="Fale conosco!",
        )
        pkg.slides.append(self._make_slide(1))
        pkg.slides.append(self._make_slide(2))
        d = pkg.to_dict()
        restored = CarouselPackage.from_dict(d)
        assert restored.package_id == pkg.package_id
        assert restored.title == pkg.title
        assert restored.slide_count == 2
        assert restored.cta_final == "Fale conosco!"

    def test_to_markdown(self):
        pkg = CarouselPackage(package_id="p4", brief_id="b4", title="Meu Carrossel")
        slide = CarouselSlide(index=1, title="Hook", content="Conteudo do hook", image_description="Imagem 1")
        pkg.slides.append(slide)
        md = pkg.to_markdown()
        assert "Meu Carrossel" in md
        assert "Hook" in md
        assert "Conteudo do hook" in md

    def test_dry_run_default_true(self):
        pkg = CarouselPackage(package_id="p5", brief_id="b5")
        assert pkg.dry_run is True


class TestCarouselBuilder:
    def setup_method(self):
        self.builder = CarouselBuilder()

    def _make_brief(self) -> ContentBrief:
        return ContentBrief(
            brief_id="b_test",
            title="Resort All-Inclusive",
            brand="Familia Tigre",
            cta="Reserve agora!",
            keywords=["resort", "familia"],
        )

    def test_build_returns_package(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert isinstance(pkg, CarouselPackage)
        assert pkg.package_id != ""

    def test_build_generates_min_slides(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert pkg.slide_count >= CarouselBuilder.MIN_SLIDES

    def test_build_slide_1_is_hook(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert pkg.slides[0].title == "Hook"
        assert brief.title in pkg.slides[0].content

    def test_build_last_slide_is_cta(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert pkg.slides[-1].title == "CTA"

    def test_build_uses_brief_cta(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert pkg.cta_final == brief.cta

    def test_build_slide_structure_includes_all_parts(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        for slide in pkg.slides:
            assert slide.index >= 1
            assert slide.title != ""
            assert slide.content != ""

    def test_build_brief_id_correct(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert pkg.brief_id == brief.brief_id

    def test_build_slides_are_sequential(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        for i, slide in enumerate(pkg.slides, 1):
            assert slide.index == i

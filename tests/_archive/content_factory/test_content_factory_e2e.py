"""Tests for W100 — Content Factory E2E (Content Package Builder)."""
from __future__ import annotations

import pytest

from src.content_factory.brief import ContentBrief
from src.content_factory.seogram import SEOgramCaption
from src.content_factory.carousel import CarouselPackage
from src.content_factory.reels import ReelScriptPackage
from src.content_factory.stories import StoriesPackage
from src.content_factory.package import ContentPackage, ContentPackageBuilder


class TestContentPackage:
    def test_create_package(self):
        pkg = ContentPackage(package_id="cp1")
        assert pkg.package_id == "cp1"
        assert pkg.brief is None
        assert pkg.generated_formats == []

    def test_generated_formats_detects_all(self):
        brief = ContentBrief(brief_id="b1", title="Test")
        caption = SEOgramCaption(caption_id="c1", brief_id="b1")
        carousel = CarouselPackage(package_id="p1", brief_id="b1")
        reels = ReelScriptPackage(package_id="r1", brief_id="b1")
        stories = StoriesPackage(package_id="s1", brief_id="b1")

        pkg = ContentPackage(
            package_id="cp2",
            brief=brief,
            caption=caption,
            carousel=carousel,
            reels=reels,
            stories=stories,
        )
        formats = pkg.generated_formats
        assert "caption" in formats
        assert "carousel" in formats
        assert "reels" in formats
        assert "stories" in formats

    def test_generated_formats_empty_when_none(self):
        pkg = ContentPackage(package_id="cp3")
        assert pkg.generated_formats == []

    def test_to_dict_roundtrip(self):
        brief = ContentBrief(brief_id="b1", title="E2E Test")
        caption = SEOgramCaption(caption_id="c1", brief_id="b1", hook="Hook!")
        pkg = ContentPackage(package_id="cp4", brief=brief, caption=caption)
        d = pkg.to_dict()
        restored = ContentPackage.from_dict(d)
        assert restored.package_id == pkg.package_id
        assert restored.brief.title == "E2E Test"
        assert restored.caption.hook == "Hook!"

    def test_to_dict_roundtrip_minimal(self):
        pkg = ContentPackage(package_id="cp5")
        d = pkg.to_dict()
        restored = ContentPackage.from_dict(d)
        assert restored.package_id == "cp5"

    def test_to_markdown(self):
        brief = ContentBrief(brief_id="b1", title="MD Test", brand="Tigre")
        pkg = ContentPackage(package_id="cp6", brief=brief)
        md = pkg.to_markdown()
        assert "cp6" in md
        assert "MD Test" in md
        assert "Tigre" in md

    def test_dry_run_default_true(self):
        pkg = ContentPackage(package_id="cp7")
        assert pkg.dry_run is True


class TestContentPackageBuilder:
    def setup_method(self):
        self.builder = ContentPackageBuilder()

    def _make_brief(self, **kwargs) -> ContentBrief:
        defaults = {
            "brief_id": "b_test",
            "title": "Resort em Natal",
            "brand": "Tigre Real",
            "keywords": ["turismo", "praia", "resort"],
            "cta": "Reserve agora!",
        }
        defaults.update(kwargs)
        return ContentBrief(**defaults)

    def test_build_from_brief_all_formats(self):
        brief = self._make_brief()
        pkg = self.builder.build_from_brief(brief)
        assert pkg.brief is not None
        assert pkg.caption is not None
        assert isinstance(pkg.caption, SEOgramCaption)
        assert pkg.carousel is not None
        assert isinstance(pkg.carousel, CarouselPackage)
        assert pkg.reels is not None
        assert isinstance(pkg.reels, ReelScriptPackage)
        assert pkg.stories is not None
        assert isinstance(pkg.stories, StoriesPackage)

    def test_build_from_brief_caption_only(self):
        brief = self._make_brief()
        pkg = self.builder.build_from_brief(brief, formats=["caption"])
        assert pkg.caption is not None
        assert pkg.carousel is None
        assert pkg.reels is None
        assert pkg.stories is None

    def test_build_from_brief_carousel_only(self):
        brief = self._make_brief()
        pkg = self.builder.build_from_brief(brief, formats=["carousel"])
        assert pkg.caption is None
        assert pkg.carousel is not None
        assert pkg.carousel.slide_count >= 5

    def test_build_from_brief_reels_only(self):
        brief = self._make_brief()
        pkg = self.builder.build_from_brief(brief, formats=["reels"])
        assert pkg.reels is not None
        assert pkg.reels.scene_count >= 4

    def test_build_from_brief_stories_only(self):
        brief = self._make_brief()
        pkg = self.builder.build_from_brief(brief, formats=["stories"])
        assert pkg.stories is not None
        assert pkg.stories.frame_count >= 4

    def test_build_with_approval(self):
        brief = self._make_brief()
        pkg = self.builder.build_with_approval(brief)
        assert pkg.caption is not None
        assert pkg.approval is not None
        assert pkg.approval.is_approved is True

    def test_build_batch(self):
        briefs = [self._make_brief(brief_id="b1"), self._make_brief(brief_id="b2")]
        pkgs = self.builder.build_batch(briefs, formats=["caption", "carousel"])
        assert len(pkgs) == 2
        for pkg in pkgs:
            assert pkg.caption is not None
            assert pkg.carousel is not None
            assert pkg.brief is not None

    def test_build_batch_empty(self):
        pkgs = self.builder.build_batch([])
        assert len(pkgs) == 0

    def test_e2e_factory_pipeline(self):
        """Full pipeline: create brief → generate all formats → approve.
        This is the canonical E2E test for Content Factory."""
        brief = ContentBrief(
            brief_id="b_e2e",
            title="Ferias em Natal com a Familia",
            brand="Familia Tigre Real",
            audience="Pais com filhos pequenos",
            objective="conversao",
            format="carousel",
            pillar="vendas",
            tone="inspirational",
            keywords=["familia", "ferias", "natal", "praia"],
            cta="Reserve sua experiencia agora!",
        )

        pkg = self.builder.build_with_approval(brief)

        assert pkg.brief is not None
        assert pkg.caption is not None
        assert pkg.carousel is not None
        assert pkg.reels is not None
        assert pkg.stories is not None
        assert pkg.approval is not None
        assert pkg.approval.is_approved is True
        assert pkg.dry_run is True

        assert len(pkg.caption.hashtags) > 0
        assert pkg.carousel.slide_count >= 5
        assert pkg.reels.scene_count >= 4
        assert pkg.stories.frame_count >= 4

        formats = pkg.generated_formats
        assert "caption" in formats
        assert "carousel" in formats
        assert "reels" in formats
        assert "stories" in formats

        d = pkg.to_dict()
        restored = ContentPackage.from_dict(d)
        assert restored.package_id == pkg.package_id
        assert restored.approval.is_approved is True

        md = pkg.to_markdown()
        assert "Ferias em Natal com a Familia" in md

    def test_e2e_multiple_objectives(self):
        """Test all 4 objectives produce valid packages."""
        for obj in ["alcance", "autoridade", "conversao", "relacionamento"]:
            brief = self._make_brief(objective=obj)
            pkg = self.builder.build_from_brief(brief, formats=["caption"])
            assert pkg.caption is not None
            assert pkg.caption.hook != ""

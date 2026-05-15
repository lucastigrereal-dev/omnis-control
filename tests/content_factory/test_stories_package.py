"""Tests for W095 — Stories Package model."""
from __future__ import annotations

import pytest

from src.content_factory.brief import ContentBrief
from src.content_factory.stories import StoryFrame, StoriesPackage, StoriesBuilder


class TestStoryFrame:
    def test_create_frame(self):
        f = StoryFrame(index=1)
        assert f.index == 1
        assert f.title == ""
        assert f.sticker_type == ""

    def test_create_full_frame(self):
        f = StoryFrame(
            index=2,
            title="Teaser",
            image_description="Imagem misteriosa",
            overlay_text="Descubra...",
            sticker_type="poll",
            link_url="https://example.com",
        )
        assert f.title == "Teaser"
        assert f.image_description == "Imagem misteriosa"
        assert f.overlay_text == "Descubra..."
        assert f.sticker_type == "poll"
        assert f.link_url == "https://example.com"

    def test_to_dict_roundtrip(self):
        f = StoryFrame(index=3, title="CTA", sticker_type="link")
        d = f.to_dict()
        restored = StoryFrame.from_dict(d)
        assert restored.index == f.index
        assert restored.title == f.title
        assert restored.sticker_type == f.sticker_type

    def test_from_dict_missing_optional(self):
        d = {"index": 4}
        f = StoryFrame.from_dict(d)
        assert f.index == 4
        assert f.title == ""


class TestStoriesPackage:
    def test_create_package(self):
        pkg = StoriesPackage(package_id="s1", brief_id="b1")
        assert pkg.package_id == "s1"
        assert pkg.frame_count == 0

    def test_frame_count(self):
        pkg = StoriesPackage(package_id="s2", brief_id="b2")
        pkg.frames.append(StoryFrame(index=1))
        pkg.frames.append(StoryFrame(index=2))
        pkg.frames.append(StoryFrame(index=3))
        assert pkg.frame_count == 3

    def test_to_dict_roundtrip(self):
        pkg = StoriesPackage(
            package_id="s3",
            brief_id="b3",
            title="Stories Test",
            swipe_up_link="https://link.com",
        )
        pkg.frames.append(StoryFrame(index=1, title="F1"))
        pkg.frames.append(StoryFrame(index=2, title="F2"))
        d = pkg.to_dict()
        restored = StoriesPackage.from_dict(d)
        assert restored.package_id == pkg.package_id
        assert restored.frame_count == 2
        assert restored.swipe_up_link == "https://link.com"

    def test_to_markdown(self):
        pkg = StoriesPackage(package_id="s4", brief_id="b4", title="Stories MD")
        pkg.frames.append(StoryFrame(
            index=1, title="Teaser", image_description="Img 1", overlay_text="Overlay 1", sticker_type="poll"
        ))
        md = pkg.to_markdown()
        assert "Stories MD" in md
        assert "Teaser" in md
        assert "poll" in md

    def test_dry_run_default_true(self):
        pkg = StoriesPackage(package_id="s5", brief_id="b5")
        assert pkg.dry_run is True


class TestStoriesBuilder:
    def setup_method(self):
        self.builder = StoriesBuilder()

    def _make_brief(self) -> ContentBrief:
        return ContentBrief(
            brief_id="b_test",
            title="Gastronomia Natalense",
            brand="O Que Comer Natal RN",
            cta="Quer saber mais?",
            keywords=["gastronomia", "restaurante"],
        )

    def test_build_returns_package(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert isinstance(pkg, StoriesPackage)
        assert pkg.package_id != ""

    def test_build_has_min_frames(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert pkg.frame_count >= StoriesBuilder.MIN_FRAMES

    def test_build_first_frame_is_teaser(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert "Teaser" in pkg.frames[0].title

    def test_build_has_cta_frame(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert "CTA" in pkg.frames[-1].title

    def test_build_frames_are_sequential(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        for i, f in enumerate(pkg.frames, 1):
            assert f.index == i

    def test_build_brief_id_matches(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert pkg.brief_id == brief.brief_id

    def test_build_teaser_has_poll_sticker(self):
        brief = self._make_brief()
        pkg = self.builder.build(brief)
        assert pkg.frames[0].sticker_type == "poll"

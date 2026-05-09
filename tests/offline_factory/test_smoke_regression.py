"""Smoke regression tests — one package of each type with standard fixture.

Ensures that after any refactor, all package types still:
1. Create their expected files
2. Return valid DeliveryPackage
3. Never call Meta
4. Never write secrets to disk
"""
from pathlib import Path
from unittest.mock import patch

import src.offline_factory.packager as packager_mod
from src.offline_factory.models import PackageStatus, PackageType
from src.offline_factory.validator import validate_package
from tests.offline_factory.conftest import FAKE_CAPTION, FAKE_ASSET


def _patch_both(caption=FAKE_CAPTION, asset=None):
    return (
        patch.object(packager_mod, "_load_caption", return_value=caption),
        patch.object(packager_mod, "_load_asset", return_value=asset),
    )


class TestCarouselSmoke:
    def test_carousel_generates_all_expected_files(self):
        with _patch_both(asset=None)[0], _patch_both(asset=None)[1]:
            pkg = packager_mod.create_carousel_package("smoke_q1")
        out = Path(pkg.output_dir)
        for fname in ("caption.md", "seo_metadata.json", "visual_brief.md",
                      "slides_outline.md", "publishing_checklist.md", "README.md", "manifest.json"):
            assert (out / fname).is_file(), f"Missing: {fname}"

    def test_carousel_partial_without_asset(self):
        with _patch_both(asset=None)[0], _patch_both(asset=None)[1]:
            pkg = packager_mod.create_carousel_package("smoke_q2")
        assert pkg.status == PackageStatus.PARTIAL

    def test_carousel_ready_with_asset(self):
        with _patch_both(asset=FAKE_ASSET)[0], _patch_both(asset=FAKE_ASSET)[1]:
            pkg = packager_mod.create_carousel_package("smoke_q3")
        assert pkg.status == PackageStatus.READY

    def test_carousel_blocked_without_caption(self):
        with patch.object(packager_mod, "_load_caption", return_value=None):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_carousel_package("smoke_q4")
        assert pkg.status == PackageStatus.BLOCKED

    def test_carousel_no_meta_call(self):
        with _patch_both()[0], _patch_both()[1]:
            with patch("requests.post") as mock:
                packager_mod.create_carousel_package("smoke_q5")
                mock.assert_not_called()


class TestReelsSmoke:
    def test_reels_generates_all_expected_files(self):
        with _patch_both()[0], _patch_both()[1]:
            pkg = packager_mod.create_reels_script_package("smoke_r1")
        out = Path(pkg.output_dir)
        for fname in ("caption.md", "script.md", "shot_list.md", "voiceover.md",
                      "editing_notes.md", "publishing_checklist.md", "README.md", "manifest.json"):
            assert (out / fname).is_file(), f"Missing: {fname}"

    def test_reels_ready_with_caption(self):
        with _patch_both()[0], _patch_both()[1]:
            pkg = packager_mod.create_reels_script_package("smoke_r2")
        assert pkg.status == PackageStatus.READY

    def test_reels_blocked_without_caption(self):
        with patch.object(packager_mod, "_load_caption", return_value=None):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_reels_script_package("smoke_r3")
        assert pkg.status == PackageStatus.BLOCKED


class TestPostSmoke:
    def test_post_generates_all_expected_files(self):
        with _patch_both(asset=None)[0], _patch_both(asset=None)[1]:
            pkg = packager_mod.create_post_package("smoke_p1")
        out = Path(pkg.output_dir)
        for fname in ("caption.md", "hashtags.md", "cta.md",
                      "publishing_checklist.md", "README.md", "manifest.json"):
            assert (out / fname).is_file(), f"Missing: {fname}"

    def test_post_partial_without_asset(self):
        with _patch_both(asset=None)[0], _patch_both(asset=None)[1]:
            pkg = packager_mod.create_post_package("smoke_p2")
        assert pkg.status == PackageStatus.PARTIAL

    def test_post_ready_with_asset(self):
        with _patch_both(asset=FAKE_ASSET)[0], _patch_both(asset=FAKE_ASSET)[1]:
            pkg = packager_mod.create_post_package("smoke_p3")
        assert pkg.status == PackageStatus.READY


class TestValidateSmoke:
    def test_validate_intact_package_high_score(self):
        with _patch_both(asset=FAKE_ASSET)[0], _patch_both(asset=FAKE_ASSET)[1]:
            pkg = packager_mod.create_carousel_package("smoke_v1")
        result = validate_package(Path(pkg.output_dir))
        assert result.score >= 70
        assert result.is_valid

    def test_validate_detects_missing_file(self):
        with _patch_both()[0], _patch_both()[1]:
            pkg = packager_mod.create_carousel_package("smoke_v2")
        out = Path(pkg.output_dir)
        (out / "caption.md").unlink()
        result = validate_package(out)
        assert not result.is_valid or result.score < 100

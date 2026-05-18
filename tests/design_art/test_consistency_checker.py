"""Tests for consistency checker."""

from src.design_art.models import (
    DesignBrief, AssetSpec, BrandVisualProfile,
    ARCHETYPE_BOLD,
)
from src.design_art.consistency_checker import ConsistencyChecker, ConsistencyCheck


class TestConsistencyCheck:
    def test_passed(self):
        c = ConsistencyCheck(dimension="test", expected="a", actual="a", passed=True)
        assert c.passed
        assert c.severity == "info"

    def test_failed(self):
        c = ConsistencyCheck(dimension="format", expected="png", actual="mp4", passed=False, severity="error")
        assert not c.passed
        assert c.severity == "error"

    def test_to_dict(self):
        c = ConsistencyCheck(dimension="dpi", expected="72", actual="150", passed=True, detail="OK")
        d = c.to_dict()
        assert d["dimension"] == "dpi"
        assert d["detail"] == "OK"


class TestConsistencyCheckerBrief:
    @staticmethod
    def _make_profile():
        return BrandVisualProfile.new(
            name="Test Profile",
            description="Test",
            brand_id="test",
            primary_color="#111111",
            secondary_color="#222222",
            accent_color="#333333",
            visual_archetype=ARCHETYPE_BOLD,
        )

    @staticmethod
    def _make_brief():
        return DesignBrief.new(
            title="Test Brief",
            profile_id="test",
            target_format="carousel",
            dimensions="1080x1080",
            copy_text="Este e um texto de copy com mais de dez palavras para teste de consistencia visual.",
        )

    def test_consistent_brief_passes(self):
        profile = self._make_profile()
        brief = self._make_brief()
        checker = ConsistencyChecker()
        report = checker.check_design_brief(brief, profile)
        assert report.is_consistent
        assert report.failed == 0
        assert report.overall_score >= 8.0

    def test_invalid_format_raises(self):
        import pytest
        with pytest.raises(ValueError, match="Invalid target_format"):
            DesignBrief.new(title="Bad Format", profile_id="test", target_format="invalid_format")

    def test_invalid_dimensions_fails(self):
        profile = self._make_profile()
        brief = DesignBrief.new(title="Bad Dims", profile_id="test", dimensions="100x100")
        checker = ConsistencyChecker()
        report = checker.check_design_brief(brief, profile)
        assert not report.is_consistent

    def test_short_copy_warns(self):
        profile = self._make_profile()
        brief = DesignBrief.new(title="Short", profile_id="test", copy_text="curto")
        checker = ConsistencyChecker()
        report = checker.check_design_brief(brief, profile)
        # Should pass (no errors) but have warnings
        assert report.warnings >= 1


class TestConsistencyCheckerAsset:
    @staticmethod
    def _make_profile():
        return BrandVisualProfile.new(
            name="Test", description="T", brand_id="t",
            primary_color="#000", secondary_color="#111", accent_color="#222",
            visual_archetype=ARCHETYPE_BOLD,
        )

    @staticmethod
    def _make_asset():
        return AssetSpec.new(
            brief_id="b1", asset_type="image", asset_name="slide_01",
            description="First slide", width=1080, height=1080,
        )

    def test_valid_asset_passes(self):
        profile = self._make_profile()
        asset = self._make_asset()
        checker = ConsistencyChecker()
        report = checker.check_asset(asset, profile)
        assert report.is_consistent

    def test_low_resolution_fails(self):
        profile = self._make_profile()
        asset = AssetSpec.new(
            brief_id="b1", asset_type="image", asset_name="low_res",
            description="Low res", width=100, height=100,
        )
        checker = ConsistencyChecker()
        report = checker.check_asset(asset, profile)
        assert not report.is_consistent

    def test_bad_format_warns(self):
        profile = self._make_profile()
        asset = AssetSpec.new(
            brief_id="b1", asset_type="image", asset_name="test",
            description="Test", file_format="mp4",
        )
        checker = ConsistencyChecker()
        report = checker.check_asset(asset, profile)
        # mp4 format triggers error for asset (not png/jpg/webp)
        assert not report.is_consistent

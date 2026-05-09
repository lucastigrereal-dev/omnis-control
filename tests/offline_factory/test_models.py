"""Tests for offline_factory models."""
import pytest
from src.offline_factory.models import DeliveryPackage, PackageType, PackageStatus


def _make_pkg(**kwargs) -> DeliveryPackage:
    defaults = dict(
        package_id="test_pkg_001",
        package_type=PackageType.CAROUSEL,
    )
    defaults.update(kwargs)
    return DeliveryPackage(**defaults)


class TestPackageType:
    def test_carousel_value(self):
        assert PackageType.CAROUSEL.value == "carousel_package"

    def test_single_post_value(self):
        assert PackageType.SINGLE_POST.value == "single_post_package"

    def test_reels_script_value(self):
        assert PackageType.REELS_SCRIPT.value == "reels_script_package"

    def test_campaign_value(self):
        assert PackageType.CAMPAIGN.value == "campaign_package"

    def test_briefing_value(self):
        assert PackageType.BRIEFING.value == "briefing_package"

    def test_all_five_types_exist(self):
        assert len(PackageType) == 5


class TestPackageStatus:
    def test_all_statuses(self):
        assert PackageStatus.DRAFT.value == "draft"
        assert PackageStatus.PARTIAL.value == "partial"
        assert PackageStatus.READY.value == "ready"
        assert PackageStatus.BLOCKED.value == "blocked"
        assert PackageStatus.EXPORTED.value == "exported"

    def test_five_statuses(self):
        assert len(PackageStatus) == 5


class TestDeliveryPackage:
    def test_minimal_creation(self):
        pkg = _make_pkg()
        assert pkg.package_id == "test_pkg_001"
        assert pkg.package_type == PackageType.CAROUSEL
        assert pkg.status == PackageStatus.DRAFT

    def test_defaults(self):
        pkg = _make_pkg()
        assert pkg.files == []
        assert pkg.warnings == []
        assert pkg.blockers == []
        assert pkg.next_actions == []
        assert pkg.hashtags == []
        assert pkg.seo_keywords == []
        assert pkg.cta == ""

    def test_blocked_when_no_caption(self):
        pkg = _make_pkg(
            status=PackageStatus.BLOCKED,
            blockers=["Caption ausente"],
        )
        assert pkg.status == PackageStatus.BLOCKED
        assert not pkg.is_ready()

    def test_partial_with_caption_no_asset(self):
        pkg = _make_pkg(
            status=PackageStatus.PARTIAL,
            warnings=["Nenhum asset atribuido"],
        )
        assert pkg.status == PackageStatus.PARTIAL
        assert not pkg.is_ready()

    def test_ready_with_caption_and_asset(self):
        pkg = _make_pkg(
            status=PackageStatus.READY,
            blockers=[],
        )
        assert pkg.is_ready()

    def test_not_ready_when_blockers(self):
        pkg = _make_pkg(
            status=PackageStatus.READY,
            blockers=["still blocked"],
        )
        assert not pkg.is_ready()

    def test_safe_summary_contains_key_fields(self):
        pkg = _make_pkg(
            title="Test Carousel",
            account_handle="lucastigrereal",
            status=PackageStatus.PARTIAL,
            files=["caption.md", "manifest.json"],
            warnings=["sem asset"],
        )
        summary = pkg.safe_summary()
        assert "test_pkg_001" in summary
        assert "carousel_package" in summary
        assert "Test Carousel" in summary
        assert "lucastigrereal" in summary
        assert "partial" in summary
        assert "2" in summary  # files count
        assert "sem asset" in summary

    def test_safe_summary_with_blockers(self):
        pkg = _make_pkg(
            status=PackageStatus.BLOCKED,
            blockers=["Caption ausente"],
            next_actions=["Aprovar legenda"],
        )
        summary = pkg.safe_summary()
        assert "Caption ausente" in summary
        assert "Aprovar legenda" in summary

    def test_created_at_is_set(self):
        pkg = _make_pkg()
        assert pkg.created_at
        assert "T" in pkg.created_at

    def test_no_meta_credentials_in_model(self):
        fields = DeliveryPackage.model_fields.keys()
        forbidden = {"access_token", "token", "secret", "password", "meta_id"}
        assert forbidden.isdisjoint(fields)

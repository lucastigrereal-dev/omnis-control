"""Tests for create_post_package — P1.8."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from src.offline_factory.models import PackageStatus, PackageType
import src.offline_factory.packager as packager_mod
from tests.offline_factory.conftest import FAKE_CAPTION, FAKE_ASSET


class TestCreatePostPackage:
    def test_blocked_when_no_caption(self):
        with patch.object(packager_mod, "_load_caption", return_value=None):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_post_package("no_caption_id")
        assert pkg.status == PackageStatus.BLOCKED
        assert any("Caption" in b for b in pkg.blockers)

    def test_partial_with_caption_no_asset(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_post_package("0b79aa1c")
        assert pkg.status == PackageStatus.PARTIAL
        assert any("asset" in w.lower() for w in pkg.warnings)

    def test_ready_with_caption_and_asset(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=FAKE_ASSET):
                pkg = packager_mod.create_post_package("0b79aa1c")
        assert pkg.status == PackageStatus.READY

    def test_package_type_is_single_post(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_post_package("0b79aa1c")
        assert pkg.package_type == PackageType.SINGLE_POST

    def test_files_created_on_disk(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_post_package("0b79aa1c")
        output = Path(pkg.output_dir)
        assert output.is_dir()
        assert (output / "caption.md").is_file()
        assert (output / "hashtags.md").is_file()
        assert (output / "cta.md").is_file()
        assert (output / "publishing_checklist.md").is_file()
        assert (output / "README.md").is_file()
        assert (output / "manifest.json").is_file()

    def test_account_handle_from_caption(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_post_package("0b79aa1c")
        assert pkg.account_handle == "afamiliatigrereal"

    def test_account_handle_override(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_post_package("0b79aa1c", account_handle="lucastigrereal")
        assert pkg.account_handle == "lucastigrereal"

    def test_source_queue_id_set(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_post_package("0b79aa1c")
        assert pkg.source_queue_id == "0b79aa1c"

    def test_caption_id_from_draft(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_post_package("0b79aa1c")
        assert pkg.source_caption_id == "1d482d82"

    def test_manifest_json_valid(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_post_package("0b79aa1c")
        manifest_path = Path(pkg.output_dir) / "manifest.json"
        data = json.loads(manifest_path.read_text())
        assert data["package_type"] == "single_post_package"

    def test_no_meta_secrets_in_files(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_post_package("0b79aa1c")
        output = Path(pkg.output_dir)
        for f in output.iterdir():
            if f.suffix in (".md", ".json", ".txt"):
                content = f.read_text()
                for secret in ["access_token", "META_APP_SECRET", "client_secret"]:
                    assert secret not in content

    def test_never_calls_meta(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                with patch("requests.post") as mock_post:
                    packager_mod.create_post_package("0b79aa1c")
                    mock_post.assert_not_called()


class TestCarouselReachesReady:
    """Carousel can reach READY when _load_asset returns something."""

    def test_carousel_ready_with_asset(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=FAKE_ASSET):
                pkg = packager_mod.create_carousel_package("0b79aa1c")
        assert pkg.status == PackageStatus.READY

    def test_carousel_partial_without_asset(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=None):
                pkg = packager_mod.create_carousel_package("0b79aa1c")
        assert pkg.status == PackageStatus.PARTIAL

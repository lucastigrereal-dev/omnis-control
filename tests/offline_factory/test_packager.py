"""Tests for offline_factory packager."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from src.offline_factory.models import PackageStatus, PackageType
import src.offline_factory.packager as packager_mod


FAKE_CAPTION = {
    "draft_id": "1d482d82",
    "queue_id": "0b79aa1c",
    "caption_text": "Natal te espera! Venha descobrir os melhores lugares. #natal #viagem",
    "hashtags": ["#natal", "#viagem", "#turismo"],
    "cta": "Salva para nao esquecer",
    "objective": "alcance",
    "account_handle": "afamiliatigrereal",
    "status": "approved",
}


@pytest.fixture(autouse=True)
def temp_export_root(tmp_path, monkeypatch):
    monkeypatch.setattr(packager_mod, "EXPORT_ROOT", tmp_path / "offline_factory")


class TestCreateCarouselPackage:
    def test_blocked_when_no_caption(self):
        with patch.object(packager_mod, "_load_caption", return_value=None):
            pkg = packager_mod.create_carousel_package("no_caption_id")
        assert pkg.status == PackageStatus.BLOCKED
        assert any("Caption" in b for b in pkg.blockers)

    def test_partial_with_caption_no_asset(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
        assert pkg.status == PackageStatus.PARTIAL
        assert any("asset" in w.lower() for w in pkg.warnings)

    def test_package_type_is_carousel(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
        assert pkg.package_type == PackageType.CAROUSEL

    def test_source_queue_id_set(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
        assert pkg.source_queue_id == "0b79aa1c"

    def test_caption_id_set_from_draft(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
        assert pkg.source_caption_id == "1d482d82"

    def test_account_handle_from_caption(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
        assert pkg.account_handle == "afamiliatigrereal"

    def test_account_handle_override(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_carousel_package("0b79aa1c", account_handle="lucastigrereal")
        assert pkg.account_handle == "lucastigrereal"

    def test_output_dir_is_set(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
        assert pkg.output_dir

    def test_files_created_on_disk(self, tmp_path):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
        output = Path(pkg.output_dir)
        assert output.is_dir()
        assert (output / "caption.md").is_file()
        assert (output / "slides_outline.md").is_file()
        assert (output / "visual_brief.md").is_file()
        assert (output / "publishing_checklist.md").is_file()
        assert (output / "manifest.json").is_file()

    def test_manifest_json_valid(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
        manifest_path = Path(pkg.output_dir) / "manifest.json"
        data = json.loads(manifest_path.read_text())
        assert data["package_type"] == "carousel_package"
        assert data["status"] == "partial"

    def test_never_calls_meta(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch("requests.post") as mock_post:
                packager_mod.create_carousel_package("0b79aa1c")
                mock_post.assert_not_called()

    def test_no_meta_secrets_in_files(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
        output = Path(pkg.output_dir)
        for f in output.iterdir():
            if f.suffix in (".md", ".json", ".txt"):
                content = f.read_text()
                for secret in ["access_token", "META_APP_SECRET", "client_secret"]:
                    assert secret not in content, f"Secret '{secret}' found in {f.name}"

    def test_num_slides_default_five(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
        slides_path = Path(pkg.output_dir) / "slides_outline.md"
        content = slides_path.read_text()
        assert "Slide 1" in content
        assert "Slide 5" in content

    def test_num_slides_custom(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_carousel_package("0b79aa1c", num_slides=7)
        slides_path = Path(pkg.output_dir) / "slides_outline.md"
        content = slides_path.read_text()
        assert "Slide 7" in content


class TestCreateReelsScriptPackage:
    def test_blocked_when_no_caption(self):
        with patch.object(packager_mod, "_load_caption", return_value=None):
            pkg = packager_mod.create_reels_script_package("no_caption_id")
        assert pkg.status == PackageStatus.BLOCKED

    def test_ready_with_full_caption(self):
        # Reels script only needs caption + account — no visual asset required
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_reels_script_package("0b79aa1c")
        assert pkg.status == PackageStatus.READY

    def test_package_type_is_reels(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_reels_script_package("0b79aa1c")
        assert pkg.package_type == PackageType.REELS_SCRIPT

    def test_files_created_on_disk(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_reels_script_package("0b79aa1c")
        output = Path(pkg.output_dir)
        assert output.is_dir()
        assert (output / "script.md").is_file()
        assert (output / "shot_list.md").is_file()
        assert (output / "voiceover.md").is_file()
        assert (output / "editing_notes.md").is_file()
        assert (output / "manifest.json").is_file()

    def test_source_queue_id_set(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg = packager_mod.create_reels_script_package("0b79aa1c")
        assert pkg.source_queue_id == "0b79aa1c"

    def test_never_calls_meta(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch("requests.post") as mock_post:
                packager_mod.create_reels_script_package("0b79aa1c")
                mock_post.assert_not_called()


class TestListPackages:
    def test_empty_when_no_exports(self):
        result = packager_mod.list_packages()
        assert result == []

    def test_lists_created_packages(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            pkg1 = packager_mod.create_carousel_package("qqq111")
            pkg2 = packager_mod.create_reels_script_package("qqq222")

        result = packager_mod.list_packages()
        assert len(result) == 2
        ids = [p["package_id"] for p in result]
        assert pkg1.package_id in ids
        assert pkg2.package_id in ids

    def test_list_returns_dicts(self):
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            packager_mod.create_carousel_package("qqq333")
        result = packager_mod.list_packages()
        assert isinstance(result[0], dict)
        assert "package_id" in result[0]
        assert "status" in result[0]

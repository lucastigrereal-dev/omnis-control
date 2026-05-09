"""Tests for offline package validator — P1.8."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

import src.offline_factory.packager as packager_mod
from src.offline_factory.validator import validate_package, validate_by_id, ValidationResult
from tests.offline_factory.conftest import FAKE_CAPTION, FAKE_ASSET


@pytest.fixture()
def ready_package_dir(tmp_path, monkeypatch):
    """Create a fully ready carousel package and return its directory."""
    monkeypatch.setattr(packager_mod, "EXPORT_ROOT", tmp_path / "offline_factory")
    with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
        with patch.object(packager_mod, "_load_asset", return_value=FAKE_ASSET):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
    return Path(pkg.output_dir)


@pytest.fixture()
def partial_package_dir(tmp_path, monkeypatch):
    """Create a partial carousel package (no asset) and return its directory."""
    monkeypatch.setattr(packager_mod, "EXPORT_ROOT", tmp_path / "offline_factory")
    with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
        with patch.object(packager_mod, "_load_asset", return_value=None):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
    return Path(pkg.output_dir)


class TestValidatePackage:
    def test_returns_validation_result(self, ready_package_dir):
        result = validate_package(ready_package_dir)
        assert isinstance(result, ValidationResult)

    def test_score_0_to_100(self, ready_package_dir):
        result = validate_package(ready_package_dir)
        assert 0 <= result.score <= 100

    def test_intact_package_high_score(self, ready_package_dir):
        result = validate_package(ready_package_dir)
        assert result.score >= 70

    def test_intact_package_has_no_failed_checks(self, ready_package_dir):
        result = validate_package(ready_package_dir)
        assert result.is_valid

    def test_partial_package_still_valid(self, partial_package_dir):
        result = validate_package(partial_package_dir)
        assert isinstance(result, ValidationResult)
        assert result.score >= 60  # Partial is still structurally valid

    def test_detects_missing_file(self, ready_package_dir):
        (ready_package_dir / "caption.md").unlink()
        result = validate_package(ready_package_dir)
        assert not result.is_valid or result.score < 100
        assert any("caption" in c for c in result.checks_failed + result.warnings)

    def test_detects_missing_manifest_listed_file(self, ready_package_dir):
        manifest_path = ready_package_dir / "manifest.json"
        data = json.loads(manifest_path.read_text())
        files = data.get("files", [])
        if files:
            first_name = files[0].get("name") if isinstance(files[0], dict) else str(files[0])
            if first_name != "manifest.json":
                (ready_package_dir / first_name).unlink(missing_ok=True)
                result = validate_package(ready_package_dir)
                assert "all_listed_files_exist" in result.checks_failed

    def test_no_meta_secrets_check_passes(self, ready_package_dir):
        result = validate_package(ready_package_dir)
        assert "no_meta_secrets" in result.checks_passed

    def test_detects_injected_secret(self, ready_package_dir):
        caption_file = ready_package_dir / "caption.md"
        original = caption_file.read_text(encoding="utf-8")
        caption_file.write_text(original + "\naccess_token=FAKE123", encoding="utf-8")
        result = validate_package(ready_package_dir)
        assert "no_meta_secrets" in result.checks_failed

    def test_package_id_is_directory_name(self, ready_package_dir):
        result = validate_package(ready_package_dir)
        assert result.package_id == ready_package_dir.name

    def test_manifest_required_fields_checked(self, ready_package_dir):
        result = validate_package(ready_package_dir)
        assert "manifest_has_package_id" in result.checks_passed
        assert "manifest_has_status" in result.checks_passed


class TestValidateById:
    def test_finds_by_prefix(self, tmp_path, monkeypatch):
        monkeypatch.setattr(packager_mod, "EXPORT_ROOT", tmp_path / "offline_factory")
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch.object(packager_mod, "_load_asset", return_value=FAKE_ASSET):
                pkg = packager_mod.create_carousel_package("0b79aa1c")
        export_root = tmp_path / "offline_factory"
        result = validate_by_id("carousel_", export_root)
        assert result is not None
        assert result.package_id == pkg.package_id

    def test_returns_none_for_unknown_id(self, tmp_path):
        export_root = tmp_path / "does_not_exist"
        result = validate_by_id("nonexistent_pkg", export_root)
        assert result is None

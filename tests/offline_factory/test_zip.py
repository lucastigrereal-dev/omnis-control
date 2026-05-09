"""Tests for offline package zipper — P1.8."""
import zipfile
import json
import pytest
from pathlib import Path
from unittest.mock import patch

import src.offline_factory.packager as packager_mod
from src.offline_factory.zipper import zip_package, ZipResult
from tests.offline_factory.conftest import FAKE_CAPTION, FAKE_ASSET


@pytest.fixture()
def package_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(packager_mod, "EXPORT_ROOT", tmp_path / "offline_factory")
    with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
        with patch.object(packager_mod, "_load_asset", return_value=None):
            pkg = packager_mod.create_carousel_package("0b79aa1c")
    return Path(pkg.output_dir), tmp_path / "offline_factory"


class TestZipPackage:
    def test_creates_zip_file(self, package_dir, tmp_path):
        pkg_dir, export_root = package_dir
        result = zip_package(pkg_dir.name, export_root, zip_root=tmp_path / "zips")
        assert Path(result.zip_path).is_file()

    def test_returns_zip_result(self, package_dir, tmp_path):
        pkg_dir, export_root = package_dir
        result = zip_package(pkg_dir.name, export_root, zip_root=tmp_path / "zips")
        assert isinstance(result, ZipResult)

    def test_zip_contains_package_files(self, package_dir, tmp_path):
        pkg_dir, export_root = package_dir
        result = zip_package(pkg_dir.name, export_root, zip_root=tmp_path / "zips")
        with zipfile.ZipFile(result.zip_path) as zf:
            names = zf.namelist()
        assert "manifest.json" in names
        assert "caption.md" in names
        assert "README.md" in names

    def test_files_zipped_count(self, package_dir, tmp_path):
        pkg_dir, export_root = package_dir
        expected = len(list(pkg_dir.iterdir()))
        result = zip_package(pkg_dir.name, export_root, zip_root=tmp_path / "zips")
        assert result.files_zipped == expected

    def test_zip_size_positive(self, package_dir, tmp_path):
        pkg_dir, export_root = package_dir
        result = zip_package(pkg_dir.name, export_root, zip_root=tmp_path / "zips")
        assert result.size_bytes > 0

    def test_zip_prefix_match(self, package_dir, tmp_path):
        pkg_dir, export_root = package_dir
        prefix = pkg_dir.name[:10]
        result = zip_package(prefix, export_root, zip_root=tmp_path / "zips")
        assert result.package_id == pkg_dir.name

    def test_raises_for_missing_package(self, tmp_path):
        export_root = tmp_path / "offline_factory"
        export_root.mkdir()
        with pytest.raises(FileNotFoundError):
            zip_package("nonexistent_package_id", export_root, zip_root=tmp_path / "zips")

    def test_no_meta_secrets_in_zip_content(self, package_dir, tmp_path):
        pkg_dir, export_root = package_dir
        result = zip_package(pkg_dir.name, export_root, zip_root=tmp_path / "zips")
        with zipfile.ZipFile(result.zip_path) as zf:
            for name in zf.namelist():
                if name.endswith((".md", ".json", ".txt")):
                    content = zf.read(name).decode("utf-8", errors="ignore")
                    for secret in ["access_token", "META_APP_SECRET", "client_secret"]:
                        assert secret not in content

    def test_to_dict(self, package_dir, tmp_path):
        pkg_dir, export_root = package_dir
        result = zip_package(pkg_dir.name, export_root, zip_root=tmp_path / "zips")
        d = result.to_dict()
        assert "package_id" in d
        assert "zip_path" in d
        assert "files_zipped" in d
        assert "size_bytes" in d

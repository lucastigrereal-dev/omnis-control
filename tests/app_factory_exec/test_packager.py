"""Tests for App Packager."""

import tempfile
from pathlib import Path

import pytest

from src.app_factory_exec.models import AppSpec, AppType, GeneratedFile
from src.app_factory_exec.generator import AppGenerator
from src.app_factory_exec.packager import AppPackager


@pytest.fixture
def packager():
    with tempfile.TemporaryDirectory() as tmp:
        yield AppPackager(output_root=Path(tmp))


@pytest.fixture
def sample_files():
    spec = AppSpec(
        app_name="test_pkg",
        app_type=AppType.API_BACKEND,
        description="Test packaging",
        entities=["User"],
    )
    gen = AppGenerator()
    return spec, gen.generate(spec)


class TestAppPackager:
    def test_dry_run_produces_manifest(self, packager, sample_files):
        spec, files = sample_files
        result = packager.write_and_package(spec, files, dry_run=True)
        assert result["dry_run"] is True
        assert "manifest_path" in result
        assert Path(result["manifest_path"]).is_file()

    def test_dry_run_no_zip(self, packager, sample_files):
        spec, files = sample_files
        result = packager.write_and_package(spec, files, dry_run=True)
        assert "zip_path" not in result

    def test_real_write_creates_files(self, packager, sample_files):
        spec, files = sample_files
        result = packager.write_and_package(spec, files, dry_run=False)
        assert result["dry_run"] is False
        assert "zip_path" in result
        assert Path(result["zip_path"]).is_file()
        assert Path(result["zip_path"]).stat().st_size > 0

    def test_real_write_creates_zip_with_files(self, packager, sample_files):
        import zipfile
        spec, files = sample_files
        result = packager.write_and_package(spec, files, dry_run=False)
        with zipfile.ZipFile(result["zip_path"], "r") as zf:
            names = zf.namelist()
            assert any("README.md" in n for n in names)
            assert any("main.py" in n for n in names)

    def test_package_file_count(self, packager, sample_files):
        spec, files = sample_files
        result = packager.write_and_package(spec, files, dry_run=False)
        assert result["file_count"] > 0

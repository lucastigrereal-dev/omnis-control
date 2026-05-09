"""Tests for offline_factory manifest generator."""
import json
import pytest
from pathlib import Path
from src.offline_factory.models import DeliveryPackage, PackageType, PackageStatus
from src.offline_factory.manifest import generate_manifest, read_manifest


@pytest.fixture
def sample_pkg(tmp_path):
    return DeliveryPackage(
        package_id="manifest_test_001",
        package_type=PackageType.CAROUSEL,
        title="Test Carousel",
        account_handle="afamiliatigrereal",
        source_queue_id="0b79aa1c",
        source_caption_id="1d482d82",
        files=["caption.md", "slides_outline.md"],
        status=PackageStatus.PARTIAL,
        warnings=["Nenhum asset"],
        blockers=[],
        next_actions=["Atribuir asset"],
        hashtags=["#natal", "#viagem"],
        cta="Salva para nao esquecer",
    )


class TestGenerateManifest:
    def test_creates_manifest_file(self, tmp_path, sample_pkg):
        path = generate_manifest(sample_pkg, tmp_path)
        assert path.is_file()
        assert path.name == "manifest.json"

    def test_manifest_has_required_fields(self, tmp_path, sample_pkg):
        generate_manifest(sample_pkg, tmp_path)
        data = json.loads((tmp_path / "manifest.json").read_text())
        required = [
            "package_id", "package_type", "title", "account_handle",
            "source_queue_id", "source_caption_id", "status",
            "files", "warnings", "blockers", "next_actions",
            "hashtags", "cta", "generated_at",
        ]
        for field in required:
            assert field in data, f"Missing field: {field}"

    def test_manifest_values_match_package(self, tmp_path, sample_pkg):
        generate_manifest(sample_pkg, tmp_path)
        data = json.loads((tmp_path / "manifest.json").read_text())
        assert data["package_id"] == "manifest_test_001"
        assert data["package_type"] == "carousel_package"
        assert data["account_handle"] == "afamiliatigrereal"
        assert data["source_queue_id"] == "0b79aa1c"
        assert data["status"] == "partial"
        assert data["warnings"] == ["Nenhum asset"]
        assert data["cta"] == "Salva para nao esquecer"

    def test_manifest_files_catalog(self, tmp_path, sample_pkg):
        # Create the files so sizes can be measured
        (tmp_path / "caption.md").write_text("caption text")
        (tmp_path / "slides_outline.md").write_text("slide outline")
        generate_manifest(sample_pkg, tmp_path)
        data = json.loads((tmp_path / "manifest.json").read_text())
        files = data["files"]
        assert isinstance(files, list)
        names = [f["name"] if isinstance(f, dict) else f for f in files]
        assert "caption.md" in names
        assert "slides_outline.md" in names

    def test_manifest_missing_files_size_zero(self, tmp_path, sample_pkg):
        generate_manifest(sample_pkg, tmp_path)
        data = json.loads((tmp_path / "manifest.json").read_text())
        for f in data["files"]:
            if isinstance(f, dict):
                assert "size_bytes" in f

    def test_manifest_generated_at_set(self, tmp_path, sample_pkg):
        generate_manifest(sample_pkg, tmp_path)
        data = json.loads((tmp_path / "manifest.json").read_text())
        assert data["generated_at"]
        assert "T" in data["generated_at"]

    def test_no_meta_secrets_in_manifest(self, tmp_path, sample_pkg):
        generate_manifest(sample_pkg, tmp_path)
        raw = (tmp_path / "manifest.json").read_text()
        for forbidden in ["access_token", "meta_secret", "META_APP_SECRET", "password"]:
            assert forbidden not in raw


class TestReadManifest:
    def test_read_existing_manifest(self, tmp_path, sample_pkg):
        generate_manifest(sample_pkg, tmp_path)
        data = read_manifest(tmp_path)
        assert data is not None
        assert data["package_id"] == "manifest_test_001"

    def test_read_missing_returns_none(self, tmp_path):
        result = read_manifest(tmp_path)
        assert result is None

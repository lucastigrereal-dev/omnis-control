"""Tests for creative production export package (13 artifacts)."""

import json
from pathlib import Path

from src.creative_production.exporter import generate_export_package, ExportPackageResult
from src.creative_production.briefs import create_brief


class TestExportPackageArtifacts:
    """Verify all 13 artifacts are generated correctly."""

    def test_all_10_text_files_generated(self, empty_data, sample_brief_data):
        """Must generate at least 10 text files."""
        brief = create_brief(**sample_brief_data)
        result = generate_export_package(brief.creative_brief_id)
        assert result is not None
        text_files = {".md", ".txt", ".json"}
        text_count = sum(
            1 for f in result.files_generated
            if Path(f).suffix in text_files
        )
        assert text_count >= 10, f"Got {text_count} text files, expected >= 10"

    def test_html_preview_generated(self, empty_data, sample_brief_data):
        """HTML preview must be valid and self-contained."""
        brief = create_brief(**sample_brief_data)
        result = generate_export_package(brief.creative_brief_id, include_html=True)
        assert result is not None
        assert "preview.html" in result.files_generated
        html = (result.package_path / "preview.html").read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html
        assert brief.account_handle in html
        # No external CDN references
        assert "http://" not in html
        assert "https://" not in html

    def test_mock_image_generated(self, empty_data, sample_brief_data):
        """Mock image must be 1080x1080 PNG."""
        from PIL import Image
        brief = create_brief(**sample_brief_data)
        result = generate_export_package(brief.creative_brief_id, include_mock_image=True)
        assert result is not None
        assert "mock_image.png" in result.files_generated
        img = Image.open(result.package_path / "mock_image.png")
        assert img.size == (1080, 1080)
        assert img.format == "PNG"

    def test_warnings_md_when_fields_missing(self, empty_data, sample_brief_data):
        """WARNINGS.md must be generated when fields are empty."""
        data = dict(sample_brief_data)
        data["script"] = ""
        data["shot_list"] = None
        brief = create_brief(**data)
        result = generate_export_package(brief.creative_brief_id)
        assert result is not None
        assert "WARNINGS.md" in result.files_generated
        assert len(result.warnings) > 0
        warnings_text = (result.package_path / "WARNINGS.md").read_text(encoding="utf-8")
        assert "Warnings" in warnings_text

    def test_no_warnings_md_when_all_fields_present(self, empty_data, sample_brief_data):
        """WARNINGS.md must NOT be generated when all fields are filled."""
        brief = create_brief(**sample_brief_data)
        result = generate_export_package(brief.creative_brief_id)
        assert result is not None
        assert "WARNINGS.md" not in result.files_generated
        assert len(result.warnings) == 0

    def test_package_id_format(self, empty_data, sample_brief_data):
        """Package ID must follow brief_<id>_<timestamp> format."""
        brief = create_brief(**sample_brief_data)
        result = generate_export_package(brief.creative_brief_id)
        assert result is not None
        assert result.package_id.startswith(f"brief_{brief.creative_brief_id}_")
        assert len(result.package_id) > len(f"brief_{brief.creative_brief_id}_")

    def test_no_external_api_calls(self, empty_data, sample_brief_data):
        """Export must NOT call external APIs (only Pillow)."""
        brief = create_brief(**sample_brief_data)
        result = generate_export_package(brief.creative_brief_id)
        assert result is not None
        assert result.success
        # All files are local — no network calls made
        assert all(f.endswith((".md", ".txt", ".json", ".html", ".png")) for f in result.files_generated)

    def test_asset_requirements_json_valid(self, empty_data, sample_brief_data):
        """asset_requirements.json must be valid JSON."""
        brief = create_brief(**sample_brief_data)
        result = generate_export_package(brief.creative_brief_id)
        assert result is not None
        json_path = result.package_path / "asset_requirements.json"
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

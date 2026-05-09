"""Tests for html_renderer."""
import json
from pathlib import Path
from src.render_engine.html_renderer import render_html


def _make_pkg(tmp_path, manifest_extra=None, files=None):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    manifest = {
        "package_id": "test_pkg_001",
        "package_type": "carousel_package",
        "status": "ready",
        "account_handle": "afamiliatigrereal",
        "created_at": "2026-05-09T00:00:00Z",
    }
    if manifest_extra:
        manifest.update(manifest_extra)
    (pkg / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    if files:
        for name, content in files.items():
            (pkg / name).write_text(content, encoding="utf-8")
    return pkg


class TestRenderHtml:
    def test_returns_html_string(self, tmp_path):
        pkg = _make_pkg(tmp_path)
        html = render_html(pkg)
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_contains_package_id(self, tmp_path):
        pkg = _make_pkg(tmp_path)
        html = render_html(pkg)
        assert "test_pkg_001" in html

    def test_contains_account_handle(self, tmp_path):
        pkg = _make_pkg(tmp_path)
        html = render_html(pkg)
        assert "afamiliatigrereal" in html

    def test_contains_status_badge(self, tmp_path):
        pkg = _make_pkg(tmp_path)
        html = render_html(pkg)
        assert "READY" in html

    def test_caption_section_present(self, tmp_path):
        pkg = _make_pkg(tmp_path, files={"caption.md": "Minha legenda aqui"})
        html = render_html(pkg)
        assert "Caption" in html
        assert "Minha legenda aqui" in html

    def test_slides_section_present(self, tmp_path):
        pkg = _make_pkg(tmp_path, files={"slides_outline.md": "Slide 1: Abertura"})
        html = render_html(pkg)
        assert "Slides Outline" in html

    def test_no_secret_patterns(self, tmp_path):
        pkg = _make_pkg(tmp_path)
        html = render_html(pkg)
        for secret in ["access_token", "META_APP_SECRET", "client_secret"]:
            assert secret not in html

    def test_empty_package_returns_valid_html(self, tmp_path):
        pkg = tmp_path / "empty_pkg"
        pkg.mkdir()
        html = render_html(pkg)
        assert "<!DOCTYPE html>" in html

    def test_xss_escaped_in_caption(self, tmp_path):
        pkg = _make_pkg(tmp_path, files={"caption.md": "<script>alert(1)</script>"})
        html = render_html(pkg)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_no_external_cdn(self, tmp_path):
        pkg = _make_pkg(tmp_path)
        html = render_html(pkg)
        assert "cdn." not in html
        assert "https://" not in html

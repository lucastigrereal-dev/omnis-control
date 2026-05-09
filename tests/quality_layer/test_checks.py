"""Tests for quality_layer checks."""
import json
import pytest
from pathlib import Path

from src.quality_layer.checks import run_checks, compute_score, CHECKS, MAX_SCORE


def _pkg(tmp_path, manifest=None, files=None) -> Path:
    pkg = tmp_path / "pkg"
    pkg.mkdir(exist_ok=True)
    base_manifest = {
        "package_id": "pkg_test",
        "package_type": "carousel_package",
        "status": "ready",
        "account_handle": "afamiliatigrereal",
        "asset_id": "mock_001",
    }
    if manifest:
        base_manifest.update(manifest)
    (pkg / "manifest.json").write_text(json.dumps(base_manifest), encoding="utf-8")
    base_files = {
        "caption.md": "Legenda aqui.",
        "publishing_checklist.md": "- [ ] Revisar",
    }
    if files:
        base_files.update(files)
    for name, content in base_files.items():
        (pkg / name).write_text(content, encoding="utf-8")
    return pkg


class TestRunChecks:
    def test_all_pass_when_full_package_with_render(self, tmp_path):
        pkg = _pkg(tmp_path)
        render = tmp_path / "render"
        render.mkdir()
        (render / "preview.html").write_text("<!DOCTYPE html>", encoding="utf-8")
        passed, failed, _ = run_checks(pkg, render_dir=render)
        assert len(failed) == 0

    def test_manifest_missing_fails_critical(self, tmp_path):
        pkg = tmp_path / "pkg2"
        pkg.mkdir()
        passed, failed, _ = run_checks(pkg)
        assert any("Manifest" in f for f in failed)

    def test_caption_missing_fails(self, tmp_path):
        pkg = _pkg(tmp_path)
        (pkg / "caption.md").unlink(missing_ok=True)
        passed, failed, _ = run_checks(pkg)
        assert any("caption" in f.lower() for f in failed)

    def test_secret_pattern_detected(self, tmp_path):
        pkg = _pkg(tmp_path, files={"caption.md": "access_token aqui nao pode"})
        passed, failed, warnings = run_checks(pkg)
        assert any("secret" in f.lower() or "Secret" in f for f in failed)
        assert any("access_token" in w for w in warnings)

    def test_no_render_adds_warning(self, tmp_path):
        pkg = _pkg(tmp_path)
        passed, failed, warnings = run_checks(pkg, render_dir=None)
        assert any("preview" in w.lower() or "HTML" in w for w in warnings)

    def test_render_html_passes_when_present(self, tmp_path):
        pkg = _pkg(tmp_path)
        render = tmp_path / "render"
        render.mkdir()
        (render / "preview.html").write_text("x", encoding="utf-8")
        passed, failed, _ = run_checks(pkg, render_dir=render)
        passed_names = [p for p in passed if "preview" in p.lower() or "renderizado" in p.lower()]
        assert len(passed_names) > 0

    def test_empty_caption_fails(self, tmp_path):
        pkg = _pkg(tmp_path, files={"caption.md": "   "})
        passed, failed, _ = run_checks(pkg)
        assert any("vazio" in f.lower() or "empty" in f.lower() or "caption" in f.lower() for f in failed)


class TestComputeScore:
    def test_zero_passed_is_zero(self):
        assert compute_score([]) == 0

    def test_all_passed_is_100(self):
        all_descs = [desc for _, desc in CHECKS.values()]
        score = compute_score(all_descs)
        assert score == 100

    def test_score_between_0_and_100(self):
        some = list(CHECKS.values())[:3]
        score = compute_score([desc for _, desc in some])
        assert 0 <= score <= 100

    def test_max_score_constant_is_positive(self):
        assert MAX_SCORE > 0

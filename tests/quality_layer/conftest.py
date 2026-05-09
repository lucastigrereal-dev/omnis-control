"""Shared fixtures for quality_layer tests."""
import json
import pytest
from pathlib import Path

import src.quality_layer.service as svc_mod


def _make_full_package(base: Path, status="ready", has_asset=True) -> Path:
    pkg = base / "carousel_full_test"
    pkg.mkdir(parents=True, exist_ok=True)
    manifest = {
        "package_id": "carousel_full_test",
        "package_type": "carousel_package",
        "status": status,
        "account_handle": "afamiliatigrereal",
        "created_at": "2026-05-09T00:00:00Z",
        "asset_id": "mock_001" if has_asset else None,
    }
    (pkg / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (pkg / "caption.md").write_text("Natal te espera! Venha descobrir.", encoding="utf-8")
    (pkg / "publishing_checklist.md").write_text("- [ ] Revisar\n- [ ] Postar", encoding="utf-8")
    return pkg


def _make_render_dir(base: Path, pkg_name: str) -> Path:
    render = base / pkg_name
    render.mkdir(parents=True, exist_ok=True)
    (render / "preview.html").write_text("<!DOCTYPE html><html></html>", encoding="utf-8")
    return render


@pytest.fixture
def full_package(tmp_path) -> Path:
    return _make_full_package(tmp_path / "exports" / "offline_factory")


@pytest.fixture
def patched_roots(tmp_path, monkeypatch, full_package):
    export_root = tmp_path / "exports" / "offline_factory"
    render_root = tmp_path / "exports" / "rendered"
    scores_log = tmp_path / "data" / "quality_scores.jsonl"
    _make_render_dir(render_root, "carousel_full_test")
    monkeypatch.setattr(svc_mod, "EXPORT_ROOT", export_root)
    monkeypatch.setattr(svc_mod, "RENDER_ROOT", render_root)
    monkeypatch.setattr(svc_mod, "SCORES_LOG", scores_log)
    return export_root, render_root

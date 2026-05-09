"""Shared fixtures for render_engine tests."""
import json
import pytest
from pathlib import Path

import src.render_engine.service as svc_mod


FAKE_MANIFEST = {
    "package_id": "carousel_0b79aa1c_test",
    "package_type": "carousel_package",
    "status": "ready",
    "account_handle": "afamiliatigrereal",
    "created_at": "2026-05-09T00:00:00Z",
    "files": ["caption.md", "slides_outline.md", "publishing_checklist.md", "manifest.json"],
}

FAKE_CAPTION_MD = "# Caption\n\nNatal te espera! Venha descobrir os melhores lugares."
FAKE_SLIDES_MD = "# Slides\n\nSlide 1: Abertura\nSlide 2: Destaque\nSlide 5: CTA"
FAKE_CHECKLIST_MD = "# Checklist\n\n- [ ] Revisar legenda\n- [ ] Postar"


@pytest.fixture
def fake_package_dir(tmp_path) -> Path:
    """Create a realistic fake package directory."""
    pkg_dir = tmp_path / "exports" / "offline_factory" / "carousel_0b79aa1c_test"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "manifest.json").write_text(json.dumps(FAKE_MANIFEST), encoding="utf-8")
    (pkg_dir / "caption.md").write_text(FAKE_CAPTION_MD, encoding="utf-8")
    (pkg_dir / "slides_outline.md").write_text(FAKE_SLIDES_MD, encoding="utf-8")
    (pkg_dir / "publishing_checklist.md").write_text(FAKE_CHECKLIST_MD, encoding="utf-8")
    return pkg_dir


@pytest.fixture
def patched_roots(tmp_path, monkeypatch, fake_package_dir):
    """Redirect EXPORT_ROOT and RENDER_ROOT to tmp_path."""
    export_root = tmp_path / "exports" / "offline_factory"
    render_root = tmp_path / "exports" / "rendered"
    monkeypatch.setattr(svc_mod, "EXPORT_ROOT", export_root)
    monkeypatch.setattr(svc_mod, "RENDER_ROOT", render_root)
    return export_root, render_root

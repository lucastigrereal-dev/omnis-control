"""Shared fixtures for client_delivery tests."""
import json
import pytest
from pathlib import Path

import src.client_delivery.service as svc_mod


def _make_fake_package(base: Path) -> Path:
    pkg_dir = base / "carousel_0b79aa1c_fake"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "package_id": "carousel_0b79aa1c_fake",
        "package_type": "carousel_package",
        "status": "ready",
        "account_handle": "afamiliatigrereal",
        "created_at": "2026-05-09T00:00:00Z",
    }
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (pkg_dir / "caption.md").write_text("Legenda aqui.", encoding="utf-8")
    return pkg_dir


def _make_fake_campaign(base: Path) -> Path:
    camp_dir = base / "campaign_abc12345"
    camp_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "campaign_id": "campaign_abc12345",
        "name": "test_camp",
        "post_count": 3,
        "status": "ready",
    }
    (camp_dir / "campaign_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return camp_dir


@pytest.fixture
def patched_roots(tmp_path, monkeypatch):
    offline_root = tmp_path / "exports" / "offline_factory"
    campaigns_root = tmp_path / "exports" / "campaigns"
    delivery_root = tmp_path / "exports" / "client_delivery"
    zips_root = tmp_path / "exports" / "client_delivery_zips"

    offline_root.mkdir(parents=True)
    campaigns_root.mkdir(parents=True)

    _make_fake_package(offline_root)
    _make_fake_campaign(campaigns_root)

    monkeypatch.setattr(svc_mod, "OFFLINE_FACTORY_ROOT", offline_root)
    monkeypatch.setattr(svc_mod, "CAMPAIGNS_ROOT", campaigns_root)
    monkeypatch.setattr(svc_mod, "DELIVERY_ROOT", delivery_root)
    monkeypatch.setattr(svc_mod, "DELIVERY_ZIPS_ROOT", zips_root)

    return offline_root, campaigns_root, delivery_root, zips_root

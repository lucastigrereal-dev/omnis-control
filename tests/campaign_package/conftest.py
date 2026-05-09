"""Shared fixtures for campaign_package tests."""
import pytest
from pathlib import Path

import src.campaign_package.service as svc_mod


@pytest.fixture
def patched_campaign_root(tmp_path, monkeypatch):
    root = tmp_path / "exports" / "campaigns"
    zips_root = tmp_path / "exports" / "campaign_zips"
    monkeypatch.setattr(svc_mod, "CAMPAIGNS_ROOT", root)
    monkeypatch.setattr(svc_mod, "CAMPAIGN_ZIPS_ROOT", zips_root)
    return root, zips_root

"""Shared fixtures for manual_publishing tests."""
import pytest
from pathlib import Path

import src.manual_publishing.service as svc_mod
import src.manual_publishing.store as store_mod


@pytest.fixture
def log_path(tmp_path) -> Path:
    return tmp_path / "manual_publishing_log.jsonl"


@pytest.fixture(autouse=True)
def patch_log_path(log_path, monkeypatch):
    monkeypatch.setattr(svc_mod, "DEFAULT_LOG_PATH", log_path)
    monkeypatch.setattr(store_mod, "DEFAULT_LOG_PATH", log_path)

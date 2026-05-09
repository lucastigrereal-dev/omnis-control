"""Shared fixtures for offline_factory tests."""
import pytest
from pathlib import Path

import src.offline_factory.packager as packager_mod


FAKE_CAPTION = {
    "draft_id": "1d482d82",
    "queue_id": "0b79aa1c",
    "caption_text": "Natal te espera! Venha descobrir os melhores lugares. #natal #viagem",
    "hashtags": ["#natal", "#viagem", "#turismo"],
    "cta": "Salva para nao esquecer",
    "objective": "alcance",
    "account_handle": "afamiliatigrereal",
    "status": "approved",
}

FAKE_ASSET = {
    "asset_id": "asset_mock_001",
    "file_name": "natal_reel_01.mp4",
    "extension": ".mp4",
    "format": "reel",
    "status": "inbox",
    "source_type": "local",
    "source_path": "/mock/natal_reel_01.mp4",
    "size_bytes": 10240,
    "fingerprint": "/mock/natal_reel_01.mp4|10240|2026-05-09T00:00:00Z",
}


@pytest.fixture(autouse=True)
def temp_export_root(tmp_path, monkeypatch):
    """Redirect all package exports to tmp_path and isolate from real system data."""
    monkeypatch.setattr(packager_mod, "EXPORT_ROOT", tmp_path / "offline_factory")
    # Isolate _load_queue_item so real content_queue.jsonl doesn't bleed into tests
    monkeypatch.setattr(packager_mod, "_load_queue_item", lambda *a, **kw: None)
    return tmp_path / "offline_factory"

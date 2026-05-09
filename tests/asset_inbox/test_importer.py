"""Tests for asset importer — B8B Safe Import Registry (22 tests)."""
import pytest
from pathlib import Path
from src.asset_inbox import importer as imp_mod
from src.asset_inbox.importer import import_asset
from src.asset_inbox.models import (
    IMPORT_STATUS_IMPORTED,
    IMPORT_STATUS_DUPLICATE,
    IMPORT_STATUS_MISSING_SOURCE,
    IMPORT_STATUS_UNSUPPORTED,
    IMPORT_STATUS_TOO_LARGE,
)


def make_file(parent: Path, name: str, content: bytes = b"fake image data") -> Path:
    p = parent / name
    p.write_bytes(content)
    return p


@pytest.fixture
def storage(tmp_path):
    return tmp_path / "storage" / "asset_inbox"


@pytest.fixture
def registry_path(tmp_path):
    return tmp_path / "data" / "registry.jsonl"


# ── Test 1: import jpg cria cópia ─────────────────────────────────────────────

def test_import_jpg_creates_copy(tmp_path, storage, registry_path):
    src = make_file(tmp_path, "photo.jpg")
    result = import_asset(str(src), storage_root=storage, registry_path=registry_path)
    assert result.status == IMPORT_STATUS_IMPORTED
    assert result.asset is not None
    assert Path(result.asset.stored_path).exists()


# ── Test 2: import mp4 cria cópia ────────────────────────────────────────────

def test_import_mp4_creates_copy(tmp_path, storage, registry_path):
    src = make_file(tmp_path, "clip.mp4", b"fake video data")
    result = import_asset(str(src), storage_root=storage, registry_path=registry_path)
    assert result.status == IMPORT_STATUS_IMPORTED
    assert Path(result.asset.stored_path).exists()


# ── Test 3: original permanece intocado ──────────────────────────────────────

def test_original_unchanged_after_import(tmp_path, storage, registry_path):
    content = b"original content untouched"
    src = make_file(tmp_path, "photo.jpg", content)
    import_asset(str(src), storage_root=storage, registry_path=registry_path)
    assert src.exists()
    assert src.read_bytes() == content


# ── Test 4: original não é alterado ──────────────────────────────────────────

def test_original_not_modified(tmp_path, storage, registry_path):
    src = make_file(tmp_path, "img.png", b"data")
    mtime_before = src.stat().st_mtime
    import_asset(str(src), storage_root=storage, registry_path=registry_path)
    # original mtime unchanged (copy2 doesn't touch source)
    assert src.stat().st_mtime == mtime_before


# ── Test 5: fingerprint original = fingerprint cópia ────────────────────────

def test_fingerprint_match_after_import(tmp_path, storage, registry_path):
    src = make_file(tmp_path, "photo.jpg", b"content to verify")
    result = import_asset(str(src), storage_root=storage, registry_path=registry_path)
    assert result.asset.fingerprint_match is True
    assert result.asset.source_fingerprint == result.asset.stored_fingerprint


# ── Test 6: duplicata retorna 'duplicate' ────────────────────────────────────

def test_duplicate_returns_duplicate_status(tmp_path, storage, registry_path):
    src = make_file(tmp_path, "photo.jpg")
    import_asset(str(src), storage_root=storage, registry_path=registry_path)
    result2 = import_asset(str(src), storage_root=storage, registry_path=registry_path)
    assert result2.status == IMPORT_STATUS_DUPLICATE
    assert result2.asset is not None  # returns existing asset


# ── Test 7: extensão proibida bloqueia ───────────────────────────────────────

def test_unsupported_extension_blocked(tmp_path, storage, registry_path):
    src = make_file(tmp_path, "doc.pdf")
    result = import_asset(str(src), storage_root=storage, registry_path=registry_path)
    assert result.status == IMPORT_STATUS_UNSUPPORTED
    assert result.asset is None


# ── Test 8: path inexistente retorna missing_source ──────────────────────────

def test_missing_source_returns_error(tmp_path, storage, registry_path):
    result = import_asset(str(tmp_path / "ghost.jpg"), storage_root=storage, registry_path=registry_path)
    assert result.status == IMPORT_STATUS_MISSING_SOURCE
    assert result.asset is None


# ── Test 9: arquivo acima do limite bloqueia sem copiar ──────────────────────

def test_too_large_file_blocked(tmp_path, storage, registry_path):
    src = make_file(tmp_path, "big.mp4", b"x" * 200)
    result = import_asset(str(src), storage_root=storage, registry_path=registry_path, max_size_bytes=100)
    assert result.status == IMPORT_STATUS_TOO_LARGE
    # storage dir for this asset should NOT exist
    asset_dirs = list(storage.iterdir()) if storage.exists() else []
    assert len(asset_dirs) == 0


# ── Test 10: asset_id baseado em fingerprint ─────────────────────────────────

def test_asset_id_based_on_fingerprint(tmp_path, storage, registry_path):
    src = make_file(tmp_path, "photo.jpg", b"unique content for id test")
    result = import_asset(str(src), storage_root=storage, registry_path=registry_path)
    assert result.asset.asset_id.startswith("ai_")
    assert len(result.asset.asset_id) > 8


# ── Test 11: import não faz assign ───────────────────────────────────────────

def test_import_does_not_assign(tmp_path, storage, registry_path):
    src = make_file(tmp_path, "photo.jpg")
    result = import_asset(str(src), storage_root=storage, registry_path=registry_path)
    assert result.status == IMPORT_STATUS_IMPORTED
    # no queue_id or mission_id in the result
    d = result.to_dict()
    assert "queue_id" not in (d.get("asset") or {})
    assert "mission_id" not in (d.get("asset") or {})


# ── Test 12: import não mexe em queue ────────────────────────────────────────

def test_import_does_not_touch_queue(tmp_path, storage, registry_path):
    src = make_file(tmp_path, "photo.jpg")
    # No queue files should be created
    import_asset(str(src), storage_root=storage, registry_path=registry_path)
    queue_files = list(tmp_path.rglob("*queue*"))
    assert not queue_files


# ── Test 13: import não mexe em mission package ──────────────────────────────

def test_import_does_not_touch_mission_package(tmp_path, storage, registry_path):
    src = make_file(tmp_path, "photo.jpg")
    import_asset(str(src), storage_root=storage, registry_path=registry_path)
    mission_files = list(tmp_path.rglob("*mission_manifest*"))
    assert not mission_files


# ── Test 14–20 são cobertos em test_registry.py e test_storage.py ──────────

# ── Test: nenhum teste chama internet ────────────────────────────────────────

def test_importer_no_network(tmp_path, storage, registry_path, monkeypatch):
    import socket
    def _blocked(*args, **kwargs):
        raise AssertionError("Network call blocked")
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    src = make_file(tmp_path, "photo.jpg")
    result = import_asset(str(src), storage_root=storage, registry_path=registry_path)
    assert result.status == IMPORT_STATUS_IMPORTED


# ── Test: nenhum teste lê .env ───────────────────────────────────────────────

def test_importer_no_env_reads(tmp_path, storage, registry_path, monkeypatch):
    import os
    original = os.getenv
    def _assert_no_secret(key, *args, **kwargs):
        assert not key.startswith("META_") and not key.startswith("INSTAGRAM_")
        return original(key, *args, **kwargs)
    monkeypatch.setattr(os, "getenv", _assert_no_secret)
    src = make_file(tmp_path, "photo.jpg")
    import_asset(str(src), storage_root=storage, registry_path=registry_path)

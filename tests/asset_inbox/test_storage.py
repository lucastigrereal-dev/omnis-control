"""Tests for asset storage — copy, manifest, existence checks."""
import json
import pytest
from pathlib import Path
from src.asset_inbox.storage import (
    get_asset_dir,
    asset_exists,
    store_copy,
    write_import_manifest,
    read_import_manifest,
)


def test_get_asset_dir(tmp_path):
    d = get_asset_dir("ai_abc123", tmp_path)
    assert d == tmp_path / "ai_abc123"


def test_asset_exists_false(tmp_path):
    assert not asset_exists("ai_missing", tmp_path)


def test_asset_exists_true(tmp_path):
    (tmp_path / "ai_exists").mkdir()
    assert asset_exists("ai_exists", tmp_path)


def test_store_copy_creates_file(tmp_path):
    src = tmp_path / "source.jpg"
    src.write_bytes(b"image bytes")
    stored = store_copy(src, "ai_test001", tmp_path)
    assert stored.exists()
    assert stored.read_bytes() == b"image bytes"


def test_store_copy_uses_extension(tmp_path):
    src = tmp_path / "clip.mp4"
    src.write_bytes(b"video bytes")
    stored = store_copy(src, "ai_test002", tmp_path)
    assert stored.name == "original_copy.mp4"


def test_store_copy_does_not_modify_source(tmp_path):
    content = b"untouched source"
    src = tmp_path / "photo.jpg"
    src.write_bytes(content)
    store_copy(src, "ai_test003", tmp_path)
    assert src.read_bytes() == content


def test_store_copy_does_not_delete_source(tmp_path):
    src = tmp_path / "photo.jpg"
    src.write_bytes(b"data")
    store_copy(src, "ai_test004", tmp_path)
    assert src.exists()


def test_write_and_read_import_manifest(tmp_path):
    data = {"asset_id": "ai_abc", "status": "imported", "file_name": "test.jpg"}
    write_import_manifest("ai_abc", data, tmp_path)
    read_back = read_import_manifest("ai_abc", tmp_path)
    assert read_back["asset_id"] == "ai_abc"
    assert read_back["status"] == "imported"


def test_read_import_manifest_missing_returns_none(tmp_path):
    assert read_import_manifest("ai_nonexistent", tmp_path) is None

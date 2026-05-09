"""Tests for AssetInboxRegistry — JSONL, no external DB."""
import json
import pytest
from pathlib import Path
from src.asset_inbox.registry import AssetInboxRegistry
from src.asset_inbox.models import ImportedAsset, IMPORT_STATUS_IMPORTED


def make_asset(suffix: str = "001") -> ImportedAsset:
    return ImportedAsset(
        asset_id=f"ai_{suffix}abc1234567890",
        source_path=f"/tmp/photo_{suffix}.jpg",
        stored_path=f"/storage/ai_{suffix}/original_copy.jpg",
        file_name=f"photo_{suffix}.jpg",
        extension=".jpg",
        media_type="image",
        size_bytes=1024,
        source_fingerprint=f"fp{suffix}" + "a" * 58,
        stored_fingerprint=f"fp{suffix}" + "a" * 58,
        fingerprint_match=True,
        status=IMPORT_STATUS_IMPORTED,
    )


def test_registry_add_and_list(tmp_path):
    reg = AssetInboxRegistry(tmp_path / "reg.jsonl")
    asset = make_asset("001")
    reg.add(asset)
    entries = reg.list()
    assert len(entries) == 1
    assert entries[0].asset_id == asset.asset_id


def test_registry_get(tmp_path):
    reg = AssetInboxRegistry(tmp_path / "reg.jsonl")
    a1 = make_asset("aaa")
    a2 = make_asset("bbb")
    reg.add(a1)
    reg.add(a2)
    found = reg.get(a1.asset_id)
    assert found is not None
    assert found.asset_id == a1.asset_id


def test_registry_get_missing_returns_none(tmp_path):
    reg = AssetInboxRegistry(tmp_path / "reg.jsonl")
    assert reg.get("ai_nonexistent") is None


def test_registry_find_by_fingerprint(tmp_path):
    reg = AssetInboxRegistry(tmp_path / "reg.jsonl")
    asset = make_asset("ccc")
    reg.add(asset)
    found = reg.find_by_fingerprint(asset.source_fingerprint)
    assert found is not None
    assert found.asset_id == asset.asset_id


def test_registry_find_by_fingerprint_missing(tmp_path):
    reg = AssetInboxRegistry(tmp_path / "reg.jsonl")
    assert reg.find_by_fingerprint("nonexistent_fp") is None


def test_registry_exists(tmp_path):
    reg = AssetInboxRegistry(tmp_path / "reg.jsonl")
    asset = make_asset("ddd")
    assert not reg.exists(asset.asset_id)
    reg.add(asset)
    assert reg.exists(asset.asset_id)


def test_registry_empty_when_no_file(tmp_path):
    reg = AssetInboxRegistry(tmp_path / "nonexistent.jsonl")
    assert reg.list() == []


def test_registry_tolerates_corrupt_lines(tmp_path):
    path = tmp_path / "reg.jsonl"
    asset = make_asset("eee")
    path.write_text(
        'INVALID_JSON\n' + json.dumps(asset.to_dict(), ensure_ascii=False) + '\n',
        encoding="utf-8",
    )
    reg = AssetInboxRegistry(path)
    entries = reg.list()
    assert len(entries) == 1  # corrupt line skipped, valid line loaded
    assert entries[0].asset_id == asset.asset_id


def test_registry_newest_first(tmp_path):
    reg = AssetInboxRegistry(tmp_path / "reg.jsonl")
    a1 = make_asset("001")
    a2 = make_asset("002")
    reg.add(a1)
    reg.add(a2)
    entries = reg.list()
    assert entries[0].asset_id == a2.asset_id  # newest first

"""Tests for AssetInboxItem and AssetInboxScanResult models."""
import pytest
from src.asset_inbox.models import (
    AssetInboxItem,
    AssetInboxScanResult,
    SUPPORTED_EXTENSIONS,
    STATUS_CANDIDATE,
    STATUS_IGNORED,
)


def test_supported_extensions_map_media_type():
    assert SUPPORTED_EXTENSIONS[".jpg"] == "image"
    assert SUPPORTED_EXTENSIONS[".jpeg"] == "image"
    assert SUPPORTED_EXTENSIONS[".png"] == "image"
    assert SUPPORTED_EXTENSIONS[".webp"] == "image"
    assert SUPPORTED_EXTENSIONS[".mp4"] == "video"
    assert SUPPORTED_EXTENSIONS[".mov"] == "video"
    assert SUPPORTED_EXTENSIONS[".m4v"] == "video"


def test_scan_result_new():
    r = AssetInboxScanResult.new("/some/path")
    assert r.scan_id.startswith("scan_")
    assert r.root_path == "/some/path"
    assert r.total_seen == 0
    assert r.total_supported == 0
    assert r.total_ignored == 0
    assert r.total_too_large == 0


def test_scan_result_to_dict():
    r = AssetInboxScanResult.new("/some/path")
    d = r.to_dict()
    assert "scan_id" in d
    assert d["next_actions"] == ["B8B Safe Import Registry"]
    assert isinstance(d["items"], list)
    assert isinstance(d["warnings"], list)


def test_asset_inbox_item_to_dict():
    item = AssetInboxItem(
        path="/tmp/photo.jpg",
        file_name="photo.jpg",
        extension=".jpg",
        size_bytes=1024,
        media_type="image",
        fingerprint="abc123",
        exists_on_disk=True,
        status=STATUS_CANDIDATE,
    )
    d = item.to_dict()
    assert d["file_name"] == "photo.jpg"
    assert d["media_type"] == "image"
    assert d["status"] == STATUS_CANDIDATE
    assert d["fingerprint"] == "abc123"

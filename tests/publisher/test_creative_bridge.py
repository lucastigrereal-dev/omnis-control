"""Tests for publisher creative bridge (W086)."""
from __future__ import annotations

from src.publisher.creative_bridge import (
    CreativeAsset,
    CreativeBridge,
    CreativeFormat,
    CreativeStatus,
)


class TestCreativeAsset:
    def test_defaults(self):
        a = CreativeAsset(asset_id="a1", content_id="c1")
        assert a.format == CreativeFormat.SINGLE_IMAGE
        assert a.status == CreativeStatus.PENDING
        assert a.media_urls == []

    def test_mark_ready(self):
        a = CreativeAsset(asset_id="a1", content_id="c1")
        a.mark_ready()
        assert a.status == CreativeStatus.READY

    def test_mark_failed(self):
        a = CreativeAsset(asset_id="a1", content_id="c1")
        a.mark_failed("render error")
        assert a.status == CreativeStatus.FAILED
        assert a.notes == "render error"

    def test_to_dict_roundtrip(self):
        a = CreativeAsset(
            asset_id="a1", content_id="c1",
            format=CreativeFormat.CAROUSEL,
            media_urls=["http://example.com/1.jpg"],
            status=CreativeStatus.READY,
        )
        restored = CreativeAsset.from_dict(a.to_dict())
        assert restored.asset_id == "a1"
        assert restored.format == CreativeFormat.CAROUSEL
        assert restored.media_urls == ["http://example.com/1.jpg"]
        assert restored.status == CreativeStatus.READY


class TestCreativeBridge:
    def test_request_asset_creates_placeholder(self):
        bridge = CreativeBridge()
        asset = bridge.request_asset("c1", CreativeFormat.REEL)
        assert asset.content_id == "c1"
        assert asset.format == CreativeFormat.REEL
        assert asset.status == CreativeStatus.READY
        assert len(asset.media_urls) == 3

    def test_get_asset(self):
        bridge = CreativeBridge()
        bridge.request_asset("c1")
        a = bridge.get_asset("c1")
        assert a is not None
        assert a.content_id == "c1"

    def test_get_asset_unknown_returns_none(self):
        bridge = CreativeBridge()
        assert bridge.get_asset("nonexistent") is None

    def test_is_ready(self):
        bridge = CreativeBridge()
        bridge.request_asset("c1")
        assert bridge.is_ready("c1") is True

    def test_is_ready_unknown_returns_false(self):
        bridge = CreativeBridge()
        assert bridge.is_ready("nonexistent") is False

    def test_to_dict(self):
        bridge = CreativeBridge()
        bridge.request_asset("c1", CreativeFormat.CAROUSEL)
        d = bridge.to_dict()
        assert "assets" in d
        assert "c1" in d["assets"]

"""Tests for W101 — Video Asset Registry."""
from __future__ import annotations

import pytest

from src.video_studio.assets import VideoAsset, VideoAssetRegistry, AssetStatus


class TestVideoAsset:
    def test_create_asset_minimal(self):
        asset = VideoAsset(asset_id="a1")
        assert asset.asset_id == "a1"
        assert asset.filename == ""
        assert asset.status == AssetStatus.PENDING
        assert asset.dry_run is True

    def test_create_full_asset(self):
        asset = VideoAsset(
            asset_id="a2",
            filename="tour_natal.mp4",
            extension=".mp4",
            source_path="videos/tour_natal.mp4",
            size_bytes=1048576,
            platform_target="instagram",
            tags=["turismo", "natal"],
            city="Natal",
            location="Ponta Negra",
        )
        assert asset.filename == "tour_natal.mp4"
        assert asset.extension == ".mp4"
        assert asset.size_bytes == 1048576
        assert asset.platform_target == "instagram"
        assert "turismo" in asset.tags
        assert asset.city == "Natal"
        assert asset.location == "Ponta Negra"

    def test_to_dict_roundtrip(self):
        asset = VideoAsset(
            asset_id="a3",
            filename="video.mp4",
            extension=".mp4",
            tags=["test"],
            city="Natal",
        )
        d = asset.to_dict()
        restored = VideoAsset.from_dict(d)
        assert restored.asset_id == asset.asset_id
        assert restored.filename == asset.filename
        assert restored.tags == asset.tags
        assert restored.city == asset.city

    def test_to_markdown(self):
        asset = VideoAsset(
            asset_id="a4",
            filename="test.mp4",
            tags=["turismo"],
            city="Natal",
        )
        md = asset.to_markdown()
        assert "test.mp4" in md
        assert "a4" in md
        assert "Natal" in md

    def test_dry_run_default_true(self):
        asset = VideoAsset(asset_id="a5")
        assert asset.dry_run is True


class TestVideoAssetRegistry:
    def setup_method(self):
        self.registry = VideoAssetRegistry()

    def test_create_asset(self):
        asset = self.registry.create_asset(
            filename="tour_natal.mp4",
            duration_seconds=60.0,
            tags=["turismo", "natal"],
            city="Natal",
        )
        assert asset.asset_id != ""
        assert asset.filename == "tour_natal.mp4"
        assert asset.source is not None
        assert asset.source.duration_seconds == 60.0

    def test_create_asset_blocks_path_traversal(self):
        with pytest.raises(ValueError, match="Path traversal"):
            self.registry.create_asset(
                filename="../../../etc/passwd",
                source_path="../../../etc/passwd",
            )

    def test_create_asset_does_not_require_real_file(self):
        asset = self.registry.create_asset(
            filename="nonexistent.mp4",
            source_path="fake/path/video.mp4",
        )
        assert asset is not None
        assert asset.filename == "nonexistent.mp4"

    def test_register_and_get(self):
        asset = VideoAsset(asset_id="a6", filename="test.mp4")
        self.registry.register(asset)
        retrieved = self.registry.get("a6")
        assert retrieved is not None
        assert retrieved.filename == "test.mp4"

    def test_get_missing_returns_none(self):
        assert self.registry.get("nonexistent") is None

    def test_list_all(self):
        self.registry.create_asset(filename="a.mp4")
        self.registry.create_asset(filename="b.mp4")
        all_assets = self.registry.list_all()
        assert len(all_assets) == 2

    def test_list_by_status(self):
        a1 = self.registry.create_asset(filename="a.mp4")
        a2 = self.registry.create_asset(filename="b.mp4")
        self.registry.update_status(a2.asset_id, AssetStatus.TRANSCRIBED)
        pending = self.registry.list_by_status(AssetStatus.PENDING)
        transcribed = self.registry.list_by_status(AssetStatus.TRANSCRIBED)
        assert len(pending) == 1
        assert len(transcribed) == 1

    def test_list_by_platform(self):
        self.registry.create_asset(filename="a.mp4", platform_target="instagram")
        self.registry.create_asset(filename="b.mp4", platform_target="youtube")
        ig = self.registry.list_by_platform("instagram")
        yt = self.registry.list_by_platform("youtube")
        assert len(ig) == 1
        assert len(yt) == 1

    def test_list_by_tag(self):
        self.registry.create_asset(filename="a.mp4", tags=["turismo", "natal"])
        self.registry.create_asset(filename="b.mp4", tags=["gastronomia"])
        turismo = self.registry.list_by_tag("turismo")
        assert len(turismo) == 1

    def test_list_by_city(self):
        self.registry.create_asset(filename="a.mp4", city="Natal")
        self.registry.create_asset(filename="b.mp4", city="Recife")
        natal = self.registry.list_by_city("Natal")
        recife = self.registry.list_by_city("recife")  # case insensitive
        assert len(natal) == 1
        assert len(recife) == 1

    def test_update_status(self):
        asset = self.registry.create_asset(filename="a.mp4")
        assert self.registry.update_status(asset.asset_id, AssetStatus.SCANNED) is True
        assert self.registry.get(asset.asset_id).status == AssetStatus.SCANNED

    def test_update_status_missing(self):
        assert self.registry.update_status("nonexistent", AssetStatus.SCANNED) is False

    def test_count(self):
        assert self.registry.count == 0
        self.registry.create_asset(filename="a.mp4")
        assert self.registry.count == 1

    def test_to_jsonl(self):
        self.registry.create_asset(filename="a.mp4", tags=["t"])
        j = self.registry.to_jsonl()
        assert "a.mp4" in j
        assert '"dry_run": true' in j.lower()

    def test_to_dict(self):
        self.registry.create_asset(filename="a.mp4")
        d = self.registry.to_dict()
        assert d["count"] == 1
        assert len(d["assets"]) == 1

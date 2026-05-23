from src.video_assets.models import AssetSourceType, VideoAsset
from src.video_assets.registry import Registry
from src.video_assets.status import AssetStatus


def test_registry_add_update_filter_and_stats(tmp_path):
    registry = Registry(str(tmp_path / "video_assets.jsonl"))
    asset = VideoAsset.new(
        asset_id="asset-1",
        source_type=AssetSourceType.LOCAL,
        source_path="C:/tmp/video.mp4",
        file_name="video.mp4",
        extension=".mp4",
        size_bytes=10,
    )

    registry.add(asset)
    updated = registry.update("asset-1", status=AssetStatus.TRIAGED, account_target="@Lucas")
    filtered = registry.filter(status=AssetStatus.TRIAGED, account="@lucas")
    stats = registry.stats()

    assert updated is not None
    assert updated.account_target == "lucas"
    assert filtered == [updated]
    assert stats["total"] == 1

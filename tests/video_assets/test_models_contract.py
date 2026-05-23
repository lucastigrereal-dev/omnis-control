from src.video_assets.models import AssetSourceType, VideoAsset
from src.video_assets.status import AssetStatus


def test_video_asset_round_trip_serializes_status_value():
    asset = VideoAsset.new(
        asset_id="asset-1",
        source_type=AssetSourceType.LOCAL,
        source_path="C:/tmp/video.mp4",
        file_name="video.mp4",
        extension=".mp4",
        size_bytes=10,
        account_target="@LucasTigreReal",
        city="Natal/RN",
        status=AssetStatus.TRIAGED,
    )

    restored = VideoAsset.from_dict(asset.to_dict())

    assert restored.status == AssetStatus.TRIAGED
    assert restored.account_target == "lucastigrereal"
    assert restored.city == "natalrn"


def test_asset_status_terminal_and_active_flags():
    assert AssetStatus.PUBLISHED.is_terminal() is True
    assert AssetStatus.ARCHIVED.is_active() is False
    assert AssetStatus.INBOX.can_transition_to(AssetStatus.TRIAGED) is True

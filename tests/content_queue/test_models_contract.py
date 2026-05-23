from src.content_queue.models import QueueItem, QueueStatus


def test_queue_item_round_trip_preserves_optional_fields():
    item = QueueItem(
        queue_id="queue-1",
        account_handle="lucastigrereal",
        date="2026-05-23",
        time="08:50",
        asset_id="asset-1",
        status=QueueStatus.NEEDS_CAPTION,
        notes="ready",
    )

    restored = QueueItem.from_dict(item.to_dict())

    assert restored == item


def test_queue_item_empty_slot_depends_on_asset_id():
    empty = QueueItem(queue_id="q1", account_handle="lucas", date="2026-05-23", time="08:50")
    filled = QueueItem(
        queue_id="q2",
        account_handle="lucas",
        date="2026-05-23",
        time="08:50",
        asset_id="asset-1",
    )

    assert empty.is_empty_slot is True
    assert filled.is_empty_slot is False

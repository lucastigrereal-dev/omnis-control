from src.content_queue.models import QueueItem, QueueStatus
from src.content_queue.queue import Queue


def test_queue_update_filter_and_stats(tmp_path):
    queue = Queue(str(tmp_path / "content_queue.jsonl"))
    item = QueueItem(
        queue_id="queue-1",
        account_handle="lucastigrereal",
        date="2026-05-23",
        time="08:50",
        status=QueueStatus.NEEDS_ASSET,
    )
    queue._append(item)

    updated = queue.update("queue-1", status=QueueStatus.APPROVED)
    filtered = queue.filter(account="@LucasTigreReal", status=QueueStatus.APPROVED)
    stats = queue.stats()

    assert updated is not None
    assert updated.status == QueueStatus.APPROVED
    assert filtered == [updated]
    assert stats["approved"] == 1


def test_queue_export_empty_writes_header(tmp_path):
    queue = Queue(str(tmp_path / "content_queue.jsonl"))
    csv_path = tmp_path / "queue.csv"

    queue.export_csv(str(csv_path))

    assert csv_path.read_text(encoding="utf-8").startswith("queue_id,account_handle")

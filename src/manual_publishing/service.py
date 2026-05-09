"""Manual publishing tracker service."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.manual_publishing.errors import PublishRecordNotFoundError
from src.manual_publishing.models import PublishRecord
from src.manual_publishing import store as _store

DEFAULT_LOG_PATH = Path("data/manual_publishing_log.jsonl")


def mark_published(
    package_id: str,
    platform: str = "instagram",
    url: Optional[str] = None,
    notes: Optional[str] = None,
    posted_by: str = "lucas",
    log_path: Path = DEFAULT_LOG_PATH,
) -> PublishRecord:
    record = PublishRecord(
        package_id=package_id,
        platform=platform,
        posted_at=datetime.now(timezone.utc).isoformat(),
        posted_by=posted_by,
        url=url,
        notes=notes,
        status="posted",
    )
    _store.append_record(record, log_path=log_path)
    return record


def list_published(log_path: Path = DEFAULT_LOG_PATH) -> list[dict]:
    return [r.to_dict() for r in _store.load_all(log_path=log_path)]


def get_published(package_id: str, log_path: Path = DEFAULT_LOG_PATH) -> dict:
    record = _store.find_by_package_id(package_id, log_path=log_path)
    if not record:
        raise PublishRecordNotFoundError(f"No publish record for '{package_id}'")
    return record.to_dict()

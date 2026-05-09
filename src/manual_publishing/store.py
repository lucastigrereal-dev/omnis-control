"""JSONL store for manual publishing records."""
import json
from pathlib import Path
from typing import Optional

from src.manual_publishing.models import PublishRecord

DEFAULT_LOG_PATH = Path("data/manual_publishing_log.jsonl")


def append_record(record: PublishRecord, log_path: Path = DEFAULT_LOG_PATH) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def load_all(log_path: Path = DEFAULT_LOG_PATH) -> list[PublishRecord]:
    if not log_path.exists():
        return []
    records = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(PublishRecord.from_dict(json.loads(line)))
        except Exception:
            continue
    return records


def find_by_package_id(package_id: str, log_path: Path = DEFAULT_LOG_PATH) -> Optional[PublishRecord]:
    for r in load_all(log_path):
        if r.package_id == package_id or r.package_id.startswith(package_id):
            return r
    return None

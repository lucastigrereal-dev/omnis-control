import uuid
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class QueueItemStatus(str, Enum):
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    DRY_RUN = "DRY_RUN"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    READY = "READY"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


VALID_TRANSITIONS: dict[QueueItemStatus, list[QueueItemStatus]] = {
    QueueItemStatus.QUEUED: [QueueItemStatus.VALIDATING, QueueItemStatus.BLOCKED],
    QueueItemStatus.VALIDATING: [
        QueueItemStatus.DRY_RUN,
        QueueItemStatus.WAITING_APPROVAL,
        QueueItemStatus.BLOCKED,
        QueueItemStatus.FAILED,
    ],
    QueueItemStatus.DRY_RUN: [
        QueueItemStatus.READY,
        QueueItemStatus.WAITING_APPROVAL,
        QueueItemStatus.BLOCKED,
        QueueItemStatus.FAILED,
    ],
    QueueItemStatus.WAITING_APPROVAL: [
        QueueItemStatus.READY,
        QueueItemStatus.BLOCKED,
    ],
    QueueItemStatus.READY: [QueueItemStatus.RUNNING, QueueItemStatus.BLOCKED],
    QueueItemStatus.RUNNING: [QueueItemStatus.DONE, QueueItemStatus.FAILED],
    QueueItemStatus.DONE: [],
    QueueItemStatus.FAILED: [],
    QueueItemStatus.BLOCKED: [],
}


@dataclass
class QueueItem:
    item_id: str = field(default_factory=lambda: _new_id("eqi"))
    contract_id: str = ""
    title: str = ""
    risk_level: str = "LOW"
    requires_approval: bool = False
    dry_run_required: bool = True
    status: QueueItemStatus = QueueItemStatus.QUEUED
    result: str = ""
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            QueueItemStatus.DONE,
            QueueItemStatus.FAILED,
            QueueItemStatus.BLOCKED,
        )

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "contract_id": self.contract_id,
            "title": self.title,
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
            "dry_run_required": self.dry_run_required,
            "status": self.status.value,
            "result": self.result,
            "errors": self.errors,
            "created_at": self.created_at,
        }


@dataclass
class QueueResult:
    result_id: str = field(default_factory=lambda: _new_id("eqr"))
    item_id: str = ""
    status: QueueItemStatus = QueueItemStatus.DONE
    output: str = ""
    tests_run: int = 0
    tests_passed: int = 0
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "item_id": self.item_id,
            "status": self.status.value,
            "output": self.output,
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "errors": self.errors,
            "created_at": self.created_at,
        }

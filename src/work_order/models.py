"""Work Order models — local, deterministic, no-LLM, no-network."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class WorkOrderStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    BLOCKED = "blocked"
    APPROVED = "approved"
    IN_PROGRESS_FUTURE = "in_progress_future"
    OUTPUT_PENDING = "output_pending"
    OUTPUT_SUBMITTED = "output_submitted"
    VALIDATED = "validated"
    REJECTED = "rejected"
    CLOSED = "closed"


class OutputType(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    CSV = "csv"
    HTML_PREVIEW = "html_preview"
    ZIP_PACKAGE = "zip_package"
    IMAGE_ASSET = "image_asset"
    VIDEO_PLAN = "video_plan"
    DELIVERY_PACKAGE = "delivery_package"
    MISSION_REPORT = "mission_report"
    UNKNOWN = "unknown"


VALID_STATUS_TRANSITIONS: dict[WorkOrderStatus, set[WorkOrderStatus]] = {
    WorkOrderStatus.DRAFT: {WorkOrderStatus.READY, WorkOrderStatus.CLOSED},
    WorkOrderStatus.READY: {WorkOrderStatus.BLOCKED, WorkOrderStatus.APPROVED, WorkOrderStatus.IN_PROGRESS_FUTURE, WorkOrderStatus.CLOSED},
    WorkOrderStatus.BLOCKED: {WorkOrderStatus.APPROVED, WorkOrderStatus.REJECTED, WorkOrderStatus.CLOSED},
    WorkOrderStatus.APPROVED: {WorkOrderStatus.IN_PROGRESS_FUTURE, WorkOrderStatus.OUTPUT_PENDING, WorkOrderStatus.CLOSED},
    WorkOrderStatus.IN_PROGRESS_FUTURE: {WorkOrderStatus.OUTPUT_PENDING, WorkOrderStatus.CLOSED},
    WorkOrderStatus.OUTPUT_PENDING: {WorkOrderStatus.OUTPUT_SUBMITTED, WorkOrderStatus.CLOSED},
    WorkOrderStatus.OUTPUT_SUBMITTED: {WorkOrderStatus.VALIDATED, WorkOrderStatus.REJECTED, WorkOrderStatus.CLOSED},
    WorkOrderStatus.VALIDATED: {WorkOrderStatus.CLOSED},
    WorkOrderStatus.REJECTED: {WorkOrderStatus.OUTPUT_PENDING, WorkOrderStatus.CLOSED},
    WorkOrderStatus.CLOSED: set(),
}


def make_work_order_id() -> str:
    raw = os.urandom(8)
    return "wo_" + hashlib.sha256(raw).hexdigest()[:10]


def make_output_id() -> str:
    raw = os.urandom(6)
    return "out_" + hashlib.sha256(raw).hexdigest()[:8]


@dataclass
class OutputContract:
    """What output a work order must produce."""
    contract_id: str
    output_type: OutputType
    description: str
    required: bool = True
    min_count: int = 1
    max_count: int = 1

    def to_dict(self) -> dict:
        return {
            "contract_id": self.contract_id,
            "output_type": self.output_type.value,
            "description": self.description,
            "required": self.required,
            "min_count": self.min_count,
            "max_count": self.max_count,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OutputContract":
        return cls(
            contract_id=d["contract_id"],
            output_type=OutputType(d["output_type"]),
            description=d["description"],
            required=d.get("required", True),
            min_count=int(d.get("min_count", 1)),
            max_count=int(d.get("max_count", 1)),
        )


@dataclass
class OutputEntry:
    """A collected output that fulfills a contract."""
    output_id: str
    output_type: OutputType
    contract_id: str
    file_path: str = ""
    status: str = "submitted"
    submitted_at: str = ""
    validated_at: str | None = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "output_id": self.output_id,
            "output_type": self.output_type.value,
            "contract_id": self.contract_id,
            "file_path": self.file_path,
            "status": self.status,
            "submitted_at": self.submitted_at,
            "validated_at": self.validated_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OutputEntry":
        return cls(
            output_id=d["output_id"],
            output_type=OutputType(d["output_type"]),
            contract_id=d["contract_id"],
            file_path=d.get("file_path", ""),
            status=d.get("status", "submitted"),
            submitted_at=d.get("submitted_at", ""),
            validated_at=d.get("validated_at"),
            notes=d.get("notes", ""),
        )


@dataclass
class WorkOrder:
    """A tracked unit of work derived from an execution graph step."""
    work_order_id: str
    graph_step_id: str
    graph_run_id: str
    role: str
    step_label: str
    status: WorkOrderStatus = WorkOrderStatus.DRAFT
    contracts: list[OutputContract] = field(default_factory=list)
    outputs: list[OutputEntry] = field(default_factory=list)
    approval_id: str | None = None
    created_at: str = ""
    updated_at: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        ts = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = ts
        if not self.updated_at:
            self.updated_at = ts

    def can_transition_to(self, target: WorkOrderStatus) -> bool:
        return target in VALID_STATUS_TRANSITIONS.get(self.status, set())

    def transition_to(self, target: WorkOrderStatus) -> "WorkOrder":
        if not self.can_transition_to(target):
            allowed = VALID_STATUS_TRANSITIONS.get(self.status, set())
            raise ValueError(
                f"Cannot transition {self.work_order_id} from {self.status.value} "
                f"to {target.value}. Allowed: {[s.value for s in allowed]}"
            )
        self.status = target
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return self

    def add_output(self, entry: OutputEntry) -> "WorkOrder":
        self.outputs.append(entry)
        if self.status == WorkOrderStatus.OUTPUT_PENDING:
            matched = {c.contract_id for c in self.contracts if c.required}
            submitted = {o.contract_id for o in self.outputs}
            if matched <= submitted:
                self.status = WorkOrderStatus.OUTPUT_SUBMITTED
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return self

    def to_dict(self) -> dict:
        return {
            "work_order_id": self.work_order_id,
            "graph_step_id": self.graph_step_id,
            "graph_run_id": self.graph_run_id,
            "role": self.role,
            "step_label": self.step_label,
            "status": self.status.value,
            "contracts": [c.to_dict() for c in self.contracts],
            "outputs": [o.to_dict() for o in self.outputs],
            "approval_id": self.approval_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WorkOrder":
        return cls(
            work_order_id=d["work_order_id"],
            graph_step_id=d["graph_step_id"],
            graph_run_id=d["graph_run_id"],
            role=d["role"],
            step_label=d["step_label"],
            status=WorkOrderStatus(d["status"]),
            contracts=[OutputContract.from_dict(c) for c in d.get("contracts", [])],
            outputs=[OutputEntry.from_dict(o) for o in d.get("outputs", [])],
            approval_id=d.get("approval_id"),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            metadata=d.get("metadata", {}),
        )

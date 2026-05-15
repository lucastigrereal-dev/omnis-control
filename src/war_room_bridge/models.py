import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    WAITING = "WAITING"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


@dataclass
class WarRoomOrder:
    order_id: str = field(default_factory=lambda: _new_id("wro"))
    title: str = ""
    aba: str = ""
    type: str = ""
    status: OrderStatus = OrderStatus.DRAFT
    risk: str = "LOW"
    project: str = ""
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    requires_approval: bool = False
    dry_run: bool = True
    description: str = ""
    body: str = ""
    source_file: str = ""
    created_at: str = field(default_factory=_now_iso)

    @property
    def is_executable(self) -> bool:
        return self.status in (OrderStatus.READY, OrderStatus.IN_PROGRESS)

    @property
    def is_high_risk(self) -> bool:
        return self.risk.upper() in ("HIGH", "CRITICAL")

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "title": self.title,
            "aba": self.aba,
            "type": self.type,
            "status": self.status.value,
            "risk": self.risk,
            "project": self.project,
            "allowed_paths": self.allowed_paths,
            "forbidden_paths": self.forbidden_paths,
            "requires_approval": self.requires_approval,
            "dry_run": self.dry_run,
            "description": self.description,
            "body": self.body,
            "source_file": self.source_file,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WarRoomOrder":
        return cls(
            order_id=data.get("order_id", ""),
            title=data.get("title", ""),
            aba=data.get("aba", ""),
            type=data.get("type", ""),
            status=OrderStatus(data.get("status", "DRAFT")),
            risk=data.get("risk", "LOW"),
            project=data.get("project", ""),
            allowed_paths=data.get("allowed_paths", []),
            forbidden_paths=data.get("forbidden_paths", []),
            requires_approval=data.get("requires_approval", False),
            dry_run=data.get("dry_run", True),
            description=data.get("description", ""),
            body=data.get("body", ""),
            source_file=data.get("source_file", ""),
            created_at=data.get("created_at", ""),
        )


@dataclass
class WarRoomReport:
    report_id: str = field(default_factory=lambda: _new_id("wrr"))
    order_id: str = ""
    title: str = ""
    status: str = ""
    summary: str = ""
    changed_files: list[str] = field(default_factory=list)
    tests_run: int = 0
    tests_passed: int = 0
    next_recommendation: str = ""
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    @property
    def all_tests_passed(self) -> bool:
        return self.tests_run > 0 and self.tests_run == self.tests_passed

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "order_id": self.order_id,
            "title": self.title,
            "status": self.status,
            "summary": self.summary,
            "changed_files": self.changed_files,
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "next_recommendation": self.next_recommendation,
            "errors": self.errors,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WarRoomReport":
        return cls(
            report_id=data.get("report_id", ""),
            order_id=data.get("order_id", ""),
            title=data.get("title", ""),
            status=data.get("status", ""),
            summary=data.get("summary", ""),
            changed_files=data.get("changed_files", []),
            tests_run=data.get("tests_run", 0),
            tests_passed=data.get("tests_passed", 0),
            next_recommendation=data.get("next_recommendation", ""),
            errors=data.get("errors", []),
            created_at=data.get("created_at", ""),
        )

    def to_markdown(self) -> str:
        lines = [
            f"# War Room Report: {self.title}",
            "",
            f"**Report ID:** {self.report_id}",
            f"**Order ID:** {self.order_id}",
            f"**Status:** {self.status}",
            f"**Created:** {self.created_at}",
            "",
            "## Summary",
            self.summary,
            "",
        ]
        if self.changed_files:
            lines.append("## Changed Files")
            for f in self.changed_files:
                lines.append(f"- `{f}`")
            lines.append("")
        lines.append("## Tests")
        lines.append(f"- Run: {self.tests_run}")
        lines.append(f"- Passed: {self.tests_passed}")
        lines.append("")
        if self.errors:
            lines.append("## Errors")
            for e in self.errors:
                lines.append(f"- {e}")
            lines.append("")
        if self.next_recommendation:
            lines.append("## Next Recommendation")
            lines.append(self.next_recommendation)
        return "\n".join(lines)

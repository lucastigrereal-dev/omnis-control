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


class LogEventType(str, Enum):
    DECISION_CREATED = "DecisionCreated"
    WORK_ORDER_PARSED = "WorkOrderParsed"
    CONTRACT_VALIDATED = "ContractValidated"
    RISK_BLOCKED = "RiskBlocked"
    DRY_RUN_COMPLETED = "DryRunCompleted"
    APPROVAL_REQUIRED = "ApprovalRequired"
    EXECUTION_COMPLETED = "ExecutionCompleted"
    EXECUTION_FAILED = "ExecutionFailed"


@dataclass
class LogEvent:
    event_id: str = field(default_factory=lambda: _new_id("evt"))
    event_type: LogEventType = LogEventType.DECISION_CREATED
    timestamp: str = field(default_factory=_now_iso)
    source: str = "omnis"
    project: str = ""
    correlation_id: str = ""
    summary: str = ""
    evidence: dict = field(default_factory=dict)
    next_action: str = ""

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "project": self.project,
            "correlation_id": self.correlation_id,
            "summary": self.summary,
            "evidence": self.evidence,
            "next_action": self.next_action,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LogEvent":
        return cls(
            event_id=data.get("event_id", ""),
            event_type=LogEventType(data.get("event_type", "DecisionCreated")),
            timestamp=data.get("timestamp", ""),
            source=data.get("source", "omnis"),
            project=data.get("project", ""),
            correlation_id=data.get("correlation_id", ""),
            summary=data.get("summary", ""),
            evidence=data.get("evidence", {}),
            next_action=data.get("next_action", ""),
        )


@dataclass
class BaseEvent:
    event: LogEvent = field(default_factory=LogEvent)

    def to_dict(self) -> dict:
        return self.event.to_dict()

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class DecisionCreatedEvent(BaseEvent):
    decision_id: str = ""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["decision_id"] = self.decision_id
        return d


@dataclass
class WorkOrderParsedEvent(BaseEvent):
    order_id: str = ""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["order_id"] = self.order_id
        return d


@dataclass
class ContractValidatedEvent(BaseEvent):
    contract_id: str = ""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["contract_id"] = self.contract_id
        return d


@dataclass
class RiskBlockedEvent(BaseEvent):
    risk_level: str = ""
    reason: str = ""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["risk_level"] = self.risk_level
        d["reason"] = self.reason
        return d


@dataclass
class DryRunCompletedEvent(BaseEvent):
    request_id: str = ""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["request_id"] = self.request_id
        return d


@dataclass
class ApprovalRequiredEvent(BaseEvent):
    item_id: str = ""
    risk_level: str = ""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["item_id"] = self.item_id
        d["risk_level"] = self.risk_level
        return d


@dataclass
class ExecutionCompletedEvent(BaseEvent):
    item_id: str = ""
    tests_run: int = 0
    tests_passed: int = 0

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["item_id"] = self.item_id
        d["tests_run"] = self.tests_run
        d["tests_passed"] = self.tests_passed
        return d


@dataclass
class ExecutionFailedEvent(BaseEvent):
    item_id: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["item_id"] = self.item_id
        d["error"] = self.error
        return d

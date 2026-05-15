from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


class CommandSource(str, Enum):
    CLI = "CLI"
    TELEGRAM = "TELEGRAM"
    WHATSAPP = "WHATSAPP"
    KRATOS = "KRATOS"
    OMNIS = "OMNIS"


class CommandRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CommandStatus(str, Enum):
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"


@dataclass
class RemoteCommand:
    command_id: str = field(default_factory=lambda: _new_id("rc_"))
    source: CommandSource = CommandSource.CLI
    source_user_id: str = ""
    source_chat_id: str = ""
    command: str = ""
    args: dict = field(default_factory=dict)
    risk: CommandRisk = CommandRisk.LOW
    status: CommandStatus = CommandStatus.RECEIVED
    requires_approval: bool = False
    approval_token: str = ""
    approval_token_expires_at: str = ""
    dry_run: bool = True
    metadata: dict = field(default_factory=dict)
    received_at: str = field(default_factory=_now_iso)

    @property
    def is_safe(self) -> bool:
        return self.risk in (CommandRisk.LOW, CommandRisk.MEDIUM)

    @property
    def needs_human(self) -> bool:
        return self.risk in (CommandRisk.HIGH, CommandRisk.CRITICAL) or self.requires_approval

    @property
    def token_expired(self) -> bool:
        if not self.approval_token_expires_at:
            return False
        from datetime import datetime, timezone
        try:
            expiry = datetime.fromisoformat(self.approval_token_expires_at)
            return datetime.now(timezone.utc) > expiry
        except (ValueError, TypeError):
            return True

    def to_dict(self) -> dict:
        return {
            "command_id": self.command_id,
            "source": self.source.value,
            "source_user_id": self.source_user_id,
            "source_chat_id": self.source_chat_id,
            "command": self.command,
            "args": self.args,
            "risk": self.risk.value,
            "status": self.status.value,
            "requires_approval": self.requires_approval,
            "approval_token": self.approval_token,
            "approval_token_expires_at": self.approval_token_expires_at,
            "dry_run": self.dry_run,
            "metadata": self.metadata,
            "received_at": self.received_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RemoteCommand":
        return cls(
            command_id=data.get("command_id", ""),
            source=CommandSource(data.get("source", "CLI")),
            source_user_id=data.get("source_user_id", ""),
            source_chat_id=data.get("source_chat_id", ""),
            command=data.get("command", ""),
            args=data.get("args", {}),
            risk=CommandRisk(data.get("risk", "LOW")),
            status=CommandStatus(data.get("status", "RECEIVED")),
            requires_approval=data.get("requires_approval", False),
            approval_token=data.get("approval_token", ""),
            approval_token_expires_at=data.get("approval_token_expires_at", ""),
            dry_run=data.get("dry_run", True),
            metadata=data.get("metadata", {}),
            received_at=data.get("received_at", ""),
        )


@dataclass
class RemoteCommandResult:
    result_id: str = field(default_factory=lambda: _new_id("rcr"))
    command_id: str = ""
    ok: bool = False
    status: CommandStatus = CommandStatus.RECEIVED
    output: str = ""
    error: str = ""
    artifacts: list[dict] = field(default_factory=list)
    completed_at: str = field(default_factory=_now_iso)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "command_id": self.command_id,
            "ok": self.ok,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "artifacts": self.artifacts,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RemoteCommandResult":
        return cls(
            result_id=data.get("result_id", ""),
            command_id=data.get("command_id", ""),
            ok=data.get("ok", False),
            status=CommandStatus(data.get("status", "RECEIVED")),
            output=data.get("output", ""),
            error=data.get("error", ""),
            artifacts=data.get("artifacts", []),
            completed_at=data.get("completed_at", ""),
            metadata=data.get("metadata", {}),
        )

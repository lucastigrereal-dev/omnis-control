from dataclasses import dataclass, field

from src.remote_control.models import RemoteCommand, CommandSource, CommandRisk, CommandStatus


@dataclass
class WhitelistEntry:
    command: str
    allowed_sources: list[str] = field(default_factory=lambda: ["CLI"])
    max_risk: str = "LOW"
    requires_token: bool = False
    max_per_hour: int = 10
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "allowed_sources": self.allowed_sources,
            "max_risk": self.max_risk,
            "requires_token": self.requires_token,
            "max_per_hour": self.max_per_hour,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WhitelistEntry":
        return cls(
            command=data.get("command", ""),
            allowed_sources=data.get("allowed_sources", ["CLI"]),
            max_risk=data.get("max_risk", "LOW"),
            requires_token=data.get("requires_token", False),
            max_per_hour=data.get("max_per_hour", 10),
            description=data.get("description", ""),
        )


BUILT_IN_WHITELIST: dict[str, WhitelistEntry] = {
    "status": WhitelistEntry(
        command="status", allowed_sources=["CLI", "TELEGRAM", "WHATSAPP", "KRATOS"],
        max_risk="LOW", description="System status",
    ),
    "briefing": WhitelistEntry(
        command="briefing", allowed_sources=["CLI", "TELEGRAM", "WHATSAPP", "KRATOS"],
        max_risk="LOW", description="Daily briefing",
    ),
    "pending": WhitelistEntry(
        command="pending", allowed_sources=["CLI", "TELEGRAM", "WHATSAPP", "KRATOS"],
        max_risk="LOW", description="Pending approvals",
    ),
    "approve": WhitelistEntry(
        command="approve", allowed_sources=["CLI", "KRATOS"],
        max_risk="HIGH", requires_token=True, description="Approve action",
    ),
    "reject": WhitelistEntry(
        command="reject", allowed_sources=["CLI", "KRATOS"],
        max_risk="HIGH", requires_token=True, description="Reject action",
    ),
    "run": WhitelistEntry(
        command="run", allowed_sources=["CLI"],
        max_risk="MEDIUM", requires_token=True, description="Run skill",
    ),
    "deploy": WhitelistEntry(
        command="deploy", allowed_sources=["CLI"],
        max_risk="CRITICAL", requires_token=True, max_per_hour=1, description="Deploy to production",
    ),
    "push": WhitelistEntry(
        command="push", allowed_sources=["CLI"],
        max_risk="CRITICAL", requires_token=True, max_per_hour=1, description="Push to origin",
    ),
}


class CommandWhitelist:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._entries: dict[str, WhitelistEntry] = dict(BUILT_IN_WHITELIST)
        self._usage: dict[str, list[str]] = {}

    def register(self, entry: WhitelistEntry) -> None:
        self._entries[entry.command] = entry

    def validate(self, cmd: RemoteCommand) -> tuple[bool, str]:
        entry = self._entries.get(cmd.command)
        if entry is None:
            return False, f"command '{cmd.command}' not in whitelist"

        if cmd.source.value not in entry.allowed_sources:
            return False, f"source '{cmd.source.value}' not allowed for '{cmd.command}'"

        risk_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        max_risk_idx = risk_order.index(entry.max_risk)
        cmd_risk_idx = risk_order.index(cmd.risk.value)
        if cmd_risk_idx > max_risk_idx:
            return False, f"risk {cmd.risk.value} exceeds max {entry.max_risk} for '{cmd.command}'"

        if entry.requires_token and not cmd.approval_token:
            return False, f"approval token required for '{cmd.command}'"

        if entry.requires_token and cmd.token_expired:
            return False, f"approval token expired for '{cmd.command}'"

        if self._is_rate_limited(entry, cmd):
            return False, f"rate limit exceeded for '{cmd.command}' (max {entry.max_per_hour}/hour)"

        self._record_usage(cmd)
        return True, "ok"

    def _is_rate_limited(self, entry: WhitelistEntry, cmd: RemoteCommand) -> bool:
        from datetime import datetime, timezone
        key = f"{cmd.source.value}:{cmd.command}"
        now = datetime.now(timezone.utc)
        timestamps = [
            ts for ts in self._usage.get(key, [])
            if (now - datetime.fromisoformat(ts)).total_seconds() < 3600
        ]
        self._usage[key] = timestamps
        return len(timestamps) >= entry.max_per_hour

    def _record_usage(self, cmd: RemoteCommand) -> None:
        key = f"{cmd.source.value}:{cmd.command}"
        self._usage.setdefault(key, []).append(cmd.received_at)

    def is_whitelisted(self, command_name: str) -> bool:
        return command_name in self._entries

    def get_entry(self, command_name: str) -> WhitelistEntry | None:
        return self._entries.get(command_name)

    @property
    def entry_count(self) -> int:
        return len(self._entries)

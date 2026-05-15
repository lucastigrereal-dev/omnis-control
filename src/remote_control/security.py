from dataclasses import dataclass, field

from src.remote_control.models import RemoteCommand, CommandSource, CommandRisk


@dataclass
class TrustedSource:
    source_type: str = ""
    identifier: str = ""
    label: str = ""
    max_command_risk: str = "LOW"
    requires_challenge: bool = False
    enabled: bool = True

    def matches(self, cmd: RemoteCommand) -> bool:
        if not self.enabled:
            return False
        if cmd.source.value != self.source_type:
            return False
        if self.identifier and cmd.source_user_id != self.identifier:
            return False
        return True


class RemoteSecurityModel:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._trusted_sources: list[TrustedSource] = []
        self._blocked_users: set[str] = set()
        self._allowed_networks: list[str] = []

    def add_trusted(self, source: TrustedSource) -> None:
        self._trusted_sources.append(source)

    def block_user(self, user_id: str) -> None:
        self._blocked_users.add(user_id)

    def unblock_user(self, user_id: str) -> bool:
        if user_id in self._blocked_users:
            self._blocked_users.discard(user_id)
            return True
        return False

    def is_blocked(self, cmd: RemoteCommand) -> bool:
        return cmd.source_user_id in self._blocked_users

    def find_trusted(self, cmd: RemoteCommand) -> TrustedSource | None:
        for ts in self._trusted_sources:
            if ts.matches(cmd):
                return ts
        return None

    def validate_remote(self, cmd: RemoteCommand) -> tuple[bool, str]:
        if cmd.source == CommandSource.CLI:
            return True, "local command"

        if self.is_blocked(cmd):
            return False, "user is blocked"

        trusted = self.find_trusted(cmd)
        if trusted is None:
            return False, "source not trusted"

        risk_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        max_idx = risk_order.index(trusted.max_command_risk)
        cmd_idx = risk_order.index(cmd.risk.value)
        if cmd_idx > max_idx:
            return False, f"command risk {cmd.risk.value} exceeds trust level {trusted.max_command_risk}"

        if trusted.requires_challenge and not cmd.approval_token:
            return False, "approval challenge required"

        return True, "ok"

    @property
    def trusted_count(self) -> int:
        return len(self._trusted_sources)

    @property
    def blocked_count(self) -> int:
        return len(self._blocked_users)

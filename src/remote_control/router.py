from src.remote_control.models import (
    RemoteCommand, RemoteCommandResult, CommandSource, CommandRisk, CommandStatus,
)
from src.remote_control.whitelist import CommandWhitelist
from src.remote_control.security import RemoteSecurityModel
from src.remote_control.approval import ApprovalChallengeEngine


class RemoteCommandRouter:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.whitelist = CommandWhitelist(dry_run=dry_run)
        self.security = RemoteSecurityModel(dry_run=dry_run)
        self.approval = ApprovalChallengeEngine(dry_run=dry_run)
        self._results: list[RemoteCommandResult] = []

    def route(self, cmd: RemoteCommand) -> RemoteCommandResult:
        if not self.dry_run:
            return RemoteCommandResult(
                command_id=cmd.command_id, ok=False,
                status=CommandStatus.BLOCKED, error="real remote execution disabled",
            )

        valid, reason = self.security.validate_remote(cmd)
        if not valid:
            return RemoteCommandResult(
                command_id=cmd.command_id, ok=False,
                status=CommandStatus.BLOCKED, error=reason,
            )

        whitelist_ok, whitelist_msg = self.whitelist.validate(cmd)
        if not whitelist_ok:
            if "token" in whitelist_msg.lower():
                challenge = self.approval.issue_challenge(cmd)
                return RemoteCommandResult(
                    command_id=cmd.command_id, ok=False,
                    status=CommandStatus.RECEIVED,
                    error="approval required",
                    metadata={"challenge_token": challenge.token, "challenge_id": challenge.challenge_id},
                )
            return RemoteCommandResult(
                command_id=cmd.command_id, ok=False,
                status=CommandStatus.BLOCKED, error=whitelist_msg,
            )

        if cmd.needs_human and not cmd.approval_token:
            challenge = self.approval.issue_challenge(cmd)
            return RemoteCommandResult(
                command_id=cmd.command_id, ok=False,
                status=CommandStatus.RECEIVED,
                error="approval required",
                metadata={"challenge_token": challenge.token, "challenge_id": challenge.challenge_id},
            )

        result = RemoteCommandResult(
            command_id=cmd.command_id, ok=True,
            status=CommandStatus.EXECUTED,
            output=f"[DRY-RUN] executed '{cmd.command}' from {cmd.source.value}",
        )
        self._results.append(result)
        return result

    def approve(self, token: str) -> tuple[bool, str]:
        return self.approval.resolve(token, approved=True)

    def reject(self, token: str, reason: str = "") -> tuple[bool, str]:
        return self.approval.resolve(token, approved=False, reason=reason)

    def get_pending(self) -> list[dict]:
        return [c.to_dict() for c in self.approval.get_pending()]

    @property
    def result_count(self) -> int:
        return len(self._results)

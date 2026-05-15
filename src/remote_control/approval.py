from dataclasses import dataclass, field
from uuid import uuid4

from src.remote_control.models import RemoteCommand, CommandStatus


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ApprovalChallenge:
    challenge_id: str = field(default_factory=lambda: _new_id("ac_"))
    command_id: str = ""
    challenge_message: str = ""
    token: str = ""
    token_expires_at: str = ""
    challenged_at: str = field(default_factory=_now_iso)
    resolved: bool = False
    resolution: str = ""
    resolved_at: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if not self.token_expires_at:
            return False
        from datetime import datetime, timezone
        try:
            expiry = datetime.fromisoformat(self.token_expires_at)
            return datetime.now(timezone.utc) >= expiry
        except (ValueError, TypeError):
            return True

    @property
    def is_pending(self) -> bool:
        return not self.resolved and not self.is_expired

    def to_dict(self) -> dict:
        return {
            "challenge_id": self.challenge_id,
            "command_id": self.command_id,
            "challenge_message": self.challenge_message,
            "token": self.token,
            "token_expires_at": self.token_expires_at,
            "challenged_at": self.challenged_at,
            "resolved": self.resolved,
            "resolution": self.resolution,
            "resolved_at": self.resolved_at,
            "metadata": self.metadata,
        }


class ApprovalChallengeEngine:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._challenges: dict[str, ApprovalChallenge] = {}
        self._tokens: dict[str, str] = {}

    def issue_challenge(self, cmd: RemoteCommand, ttl_minutes: int = 15) -> ApprovalChallenge:
        token = _new_id("tok")
        from datetime import datetime, timezone, timedelta
        expires = (datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).isoformat()

        challenge = ApprovalChallenge(
            command_id=cmd.command_id,
            challenge_message=f"Approve '{cmd.command}' from {cmd.source.value}? [{cmd.risk.value} risk]",
            token=token,
            token_expires_at=expires,
        )
        self._challenges[challenge.challenge_id] = challenge
        self._tokens[token] = challenge.challenge_id
        return challenge

    def resolve(self, token: str, approved: bool, reason: str = "") -> tuple[bool, str]:
        challenge_id = self._tokens.get(token)
        if challenge_id is None:
            return False, "invalid or unknown token"

        challenge = self._challenges.get(challenge_id)
        if challenge is None:
            return False, "challenge not found"

        if challenge.is_expired:
            return False, "token expired"

        if challenge.resolved:
            return False, "challenge already resolved"

        challenge.resolved = True
        challenge.resolution = "approved" if approved else "rejected"
        challenge.resolved_at = _now_iso()

        if approved:
            return True, "approved"
        return True, f"rejected: {reason}" if reason else "rejected"

    def get_challenge_by_token(self, token: str) -> ApprovalChallenge | None:
        challenge_id = self._tokens.get(token)
        if challenge_id:
            return self._challenges.get(challenge_id)
        return None

    def get_challenge(self, challenge_id: str) -> ApprovalChallenge | None:
        return self._challenges.get(challenge_id)

    def get_pending(self) -> list[ApprovalChallenge]:
        return [c for c in self._challenges.values() if c.is_pending]

    def expire_challenges(self) -> int:
        count = 0
        for c in self._challenges.values():
            if c.is_expired and not c.resolved:
                c.resolved = True
                c.resolution = "expired"
                count += 1
        return count

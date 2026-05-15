from src.remote_control.models import RemoteCommand, CommandSource, CommandRisk
from src.remote_control.approval import ApprovalChallenge, ApprovalChallengeEngine


class TestApprovalChallenge:
    def test_defaults(self):
        c = ApprovalChallenge()
        assert c.challenge_id.startswith("ac_")
        assert c.resolved is False

    def test_not_expired(self):
        c = ApprovalChallenge(token_expires_at="2099-01-01T00:00:00+00:00")
        assert c.is_expired is False
        assert c.is_pending is True

    def test_expired(self):
        c = ApprovalChallenge(token_expires_at="2020-01-01T00:00:00+00:00")
        assert c.is_expired is True
        assert c.is_pending is False

    def test_resolved_not_pending(self):
        c = ApprovalChallenge(resolved=True, resolution="approved", token_expires_at="2099-01-01T00:00:00+00:00")
        assert c.is_pending is False


class TestApprovalChallengeEngine:
    def test_issue_challenge(self):
        engine = ApprovalChallengeEngine()
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, command="run", risk=CommandRisk.MEDIUM)
        challenge = engine.issue_challenge(cmd)
        assert challenge.token.startswith("tok_")
        assert challenge.is_pending is True
        assert "run" in challenge.challenge_message
        assert "MEDIUM" in challenge.challenge_message

    def test_resolve_approved(self):
        engine = ApprovalChallengeEngine()
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, command="run", risk=CommandRisk.MEDIUM)
        challenge = engine.issue_challenge(cmd)
        ok, msg = engine.resolve(challenge.token, approved=True)
        assert ok is True
        assert msg == "approved"
        assert challenge.resolved is True
        assert challenge.resolution == "approved"

    def test_resolve_rejected(self):
        engine = ApprovalChallengeEngine()
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, command="run", risk=CommandRisk.MEDIUM)
        challenge = engine.issue_challenge(cmd)
        ok, msg = engine.resolve(challenge.token, approved=False, reason="too risky")
        assert ok is True
        assert "rejected" in msg
        assert challenge.resolution == "rejected"

    def test_resolve_invalid_token(self):
        engine = ApprovalChallengeEngine()
        ok, msg = engine.resolve("invalid_token", approved=True)
        assert ok is False
        assert "invalid" in msg

    def test_resolve_already_resolved(self):
        engine = ApprovalChallengeEngine()
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, command="run", risk=CommandRisk.LOW)
        challenge = engine.issue_challenge(cmd)
        engine.resolve(challenge.token, approved=True)
        ok, msg = engine.resolve(challenge.token, approved=False)
        assert ok is False
        assert "already resolved" in msg

    def test_get_challenge_by_token(self):
        engine = ApprovalChallengeEngine()
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, command="status", risk=CommandRisk.LOW)
        challenge = engine.issue_challenge(cmd)
        found = engine.get_challenge_by_token(challenge.token)
        assert found is not None
        assert found.command_id == cmd.command_id

    def test_get_pending(self):
        engine = ApprovalChallengeEngine()
        cmd1 = RemoteCommand(source=CommandSource.TELEGRAM, command="a", risk=CommandRisk.LOW)
        cmd2 = RemoteCommand(source=CommandSource.TELEGRAM, command="b", risk=CommandRisk.LOW)
        c1 = engine.issue_challenge(cmd1)
        c2 = engine.issue_challenge(cmd2)
        engine.resolve(c1.token, approved=True)
        pending = engine.get_pending()
        assert len(pending) == 1
        assert pending[0].challenge_id == c2.challenge_id

    def test_expire_challenges(self):
        engine = ApprovalChallengeEngine()
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, command="x", risk=CommandRisk.LOW)
        c = engine.issue_challenge(cmd, ttl_minutes=0)
        expired = engine.expire_challenges()
        assert expired == 1
        assert c.resolution == "expired"

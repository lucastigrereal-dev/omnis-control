from src.remote_control.models import RemoteCommand, CommandSource, CommandRisk, CommandStatus
from src.remote_control.security import TrustedSource
from src.remote_control.router import RemoteCommandRouter


class TestRemoteCommandRouter:
    def test_route_low_risk_telegram_command(self):
        router = RemoteCommandRouter(dry_run=True)
        router.security.add_trusted(TrustedSource(
            source_type="TELEGRAM", identifier="user123", max_command_risk="LOW",
        ))
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="user123",
                            command="status", risk=CommandRisk.LOW)
        result = router.route(cmd)
        assert result.ok is True
        assert result.status == CommandStatus.EXECUTED

    def test_route_untrusted_source_blocked(self):
        router = RemoteCommandRouter(dry_run=True)
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="unknown",
                            command="status", risk=CommandRisk.LOW)
        result = router.route(cmd)
        assert result.ok is False
        assert result.status == CommandStatus.BLOCKED

    def test_route_high_risk_no_token_creates_challenge(self):
        router = RemoteCommandRouter(dry_run=True)
        cmd = RemoteCommand(source=CommandSource.CLI, command="run", risk=CommandRisk.MEDIUM)
        result = router.route(cmd)
        assert result.ok is False
        assert result.status == CommandStatus.RECEIVED
        assert "challenge_token" in result.metadata

    def test_route_not_whitelisted(self):
        router = RemoteCommandRouter(dry_run=True)
        router.security.add_trusted(TrustedSource(
            source_type="TELEGRAM", identifier="user123", max_command_risk="LOW",
        ))
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="user123",
                            command="nonexistent", risk=CommandRisk.LOW)
        result = router.route(cmd)
        assert result.ok is False
        assert result.status == CommandStatus.BLOCKED

    def test_route_blocked_risk_exceeds_whitelist(self):
        router = RemoteCommandRouter(dry_run=True)
        router.security.add_trusted(TrustedSource(
            source_type="TELEGRAM", identifier="user123", max_command_risk="HIGH",
        ))
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="user123",
                            command="status", risk=CommandRisk.HIGH)
        result = router.route(cmd)
        assert result.ok is False

    def test_real_mode_blocked(self):
        router = RemoteCommandRouter(dry_run=False)
        cmd = RemoteCommand(source=CommandSource.CLI, command="status", risk=CommandRisk.LOW)
        result = router.route(cmd)
        assert result.ok is False
        assert "real remote execution disabled" in result.error

    def test_approve_and_route_happy_path(self):
        router = RemoteCommandRouter(dry_run=True)
        cmd = RemoteCommand(source=CommandSource.CLI, command="run", risk=CommandRisk.MEDIUM)
        result = router.route(cmd)
        token = result.metadata["challenge_token"]

        ok, msg = router.approve(token)
        assert ok is True

        cmd.approval_token = token
        cmd.approval_token_expires_at = "2099-01-01T00:00:00+00:00"
        result2 = router.route(cmd)
        assert result2.ok is True

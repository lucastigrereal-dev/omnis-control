from src.remote_control.models import RemoteCommand, CommandSource, CommandRisk
from src.remote_control.whitelist import CommandWhitelist, WhitelistEntry


class TestCommandWhitelist:
    def test_builtin_status_allowed_from_telegram(self):
        wl = CommandWhitelist()
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, command="status", risk=CommandRisk.LOW)
        ok, msg = wl.validate(cmd)
        assert ok is True

    def test_push_not_allowed_from_telegram(self):
        wl = CommandWhitelist()
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, command="push", risk=CommandRisk.LOW)
        ok, msg = wl.validate(cmd)
        assert ok is False
        assert "not allowed" in msg

    def test_unknown_command_rejected(self):
        wl = CommandWhitelist()
        cmd = RemoteCommand(command="delete_everything", risk=CommandRisk.LOW)
        ok, msg = wl.validate(cmd)
        assert ok is False
        assert "not in whitelist" in msg

    def test_risk_exceeds_max(self):
        wl = CommandWhitelist()
        cmd = RemoteCommand(command="status", risk=CommandRisk.HIGH)
        ok, msg = wl.validate(cmd)
        assert ok is False
        assert "exceeds max" in msg

    def test_approve_requires_token(self):
        wl = CommandWhitelist()
        cmd = RemoteCommand(source=CommandSource.CLI, command="approve", risk=CommandRisk.HIGH)
        ok, msg = wl.validate(cmd)
        assert ok is False
        assert "token required" in msg

    def test_approve_with_token_succeeds(self):
        wl = CommandWhitelist()
        cmd = RemoteCommand(
            source=CommandSource.CLI, command="approve", risk=CommandRisk.HIGH,
            approval_token="tok_valid", approval_token_expires_at="2099-01-01T00:00:00+00:00",
        )
        ok, msg = wl.validate(cmd)
        assert ok is True

    def test_approve_with_expired_token_fails(self):
        wl = CommandWhitelist()
        cmd = RemoteCommand(
            source=CommandSource.CLI, command="approve", risk=CommandRisk.HIGH,
            approval_token="tok_expired", approval_token_expires_at="2020-01-01T00:00:00+00:00",
        )
        ok, msg = wl.validate(cmd)
        assert ok is False
        assert "expired" in msg

    def test_is_whitelisted(self):
        wl = CommandWhitelist()
        assert wl.is_whitelisted("status") is True
        assert wl.is_whitelisted("nonexistent") is False

    def test_register_custom_command(self):
        wl = CommandWhitelist()
        wl.register(WhitelistEntry(
            command="custom", allowed_sources=["TELEGRAM"],
            max_risk="LOW", description="Custom command",
        ))
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, command="custom", risk=CommandRisk.LOW)
        ok, msg = wl.validate(cmd)
        assert ok is True

    def test_get_entry(self):
        wl = CommandWhitelist()
        entry = wl.get_entry("status")
        assert entry is not None
        assert entry.command == "status"
        assert wl.get_entry("nonexistent") is None

    def test_entry_count(self):
        wl = CommandWhitelist()
        assert wl.entry_count >= 8

    def test_rate_limit(self):
        wl = CommandWhitelist()
        cmd = RemoteCommand(source=CommandSource.CLI, command="status", risk=CommandRisk.LOW)
        # Status has max 10/hour built-in, so validate 10 times
        for _ in range(10):
            ok, _ = wl.validate(cmd)
            assert ok is True
        # 11th should fail
        ok, msg = wl.validate(cmd)
        assert ok is False
        assert "rate limit" in msg

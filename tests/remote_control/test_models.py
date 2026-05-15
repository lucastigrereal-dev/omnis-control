from src.remote_control.models import (
    RemoteCommand,
    RemoteCommandResult,
    CommandSource,
    CommandRisk,
    CommandStatus,
)


class TestRemoteCommand:
    def test_defaults(self):
        c = RemoteCommand()
        assert c.command_id.startswith("rc_")
        assert c.source == CommandSource.CLI
        assert c.dry_run is True
        assert c.risk == CommandRisk.LOW

    def test_telegram_source(self):
        c = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="user123")
        assert c.source == CommandSource.TELEGRAM
        assert c.source_user_id == "user123"

    def test_is_safe_low(self):
        c = RemoteCommand(risk=CommandRisk.LOW)
        assert c.is_safe is True
        assert c.needs_human is False

    def test_is_safe_medium(self):
        c = RemoteCommand(risk=CommandRisk.MEDIUM)
        assert c.is_safe is True

    def test_needs_human_high(self):
        c = RemoteCommand(risk=CommandRisk.HIGH)
        assert c.needs_human is True
        assert c.is_safe is False

    def test_needs_human_critical(self):
        c = RemoteCommand(risk=CommandRisk.CRITICAL)
        assert c.needs_human is True

    def test_token_not_expired(self):
        c = RemoteCommand(approval_token_expires_at="2099-01-01T00:00:00+00:00")
        assert c.token_expired is False

    def test_token_expired(self):
        c = RemoteCommand(approval_token_expires_at="2020-01-01T00:00:00+00:00")
        assert c.token_expired is True

    def test_no_token_not_expired(self):
        c = RemoteCommand()
        assert c.token_expired is False

    def test_roundtrip(self):
        c = RemoteCommand(
            source=CommandSource.WHATSAPP,
            source_user_id="wa_user",
            command="status",
            risk=CommandRisk.MEDIUM,
            requires_approval=True,
            approval_token="tok_abc",
        )
        d = c.to_dict()
        c2 = RemoteCommand.from_dict(d)
        assert c2.source == CommandSource.WHATSAPP
        assert c2.command == "status"
        assert c2.risk == CommandRisk.MEDIUM
        assert c2.requires_approval is True
        assert c2.approval_token == "tok_abc"


class TestRemoteCommandResult:
    def test_defaults(self):
        r = RemoteCommandResult()
        assert r.result_id.startswith("rcr_")
        assert r.ok is False

    def test_ok_result(self):
        r = RemoteCommandResult(ok=True, status=CommandStatus.EXECUTED, output="done")
        assert r.ok is True
        assert r.output == "done"

    def test_error_result(self):
        r = RemoteCommandResult(ok=False, status=CommandStatus.FAILED, error="timeout")
        assert r.ok is False
        assert r.error == "timeout"

    def test_roundtrip(self):
        r = RemoteCommandResult(
            command_id="rc_abc", ok=True, status=CommandStatus.EXECUTED,
            output="result", artifacts=[{"type": "log"}],
        )
        d = r.to_dict()
        r2 = RemoteCommandResult.from_dict(d)
        assert r2.command_id == "rc_abc"
        assert r2.ok is True
        assert r2.artifacts[0]["type"] == "log"

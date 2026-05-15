from src.remote_control.models import RemoteCommand, CommandSource, CommandRisk, CommandStatus
from src.remote_control.security import TrustedSource
from src.remote_control.router import RemoteCommandRouter
from src.remote_control.event_log import RemoteEventLog, RemoteEventType
from src.remote_control.telegram_adapter import TelegramAdapter
from src.remote_control.whatsapp_adapter import WhatsAppAdapter


class TestRemoteControlE2E:
    def test_telegram_status_flow(self):
        adapter = TelegramAdapter()
        router = RemoteCommandRouter(dry_run=True)
        event_log = RemoteEventLog()
        router.security.add_trusted(TrustedSource(
            source_type="TELEGRAM", identifier="user123", max_command_risk="LOW",
        ))

        raw = {"chat_id": 123, "user_id": "user123", "text": "/status"}
        cmd = adapter.parse_incoming(raw)
        event_log.record(RemoteEventType.COMMAND_RECEIVED, cmd)

        result = router.route(cmd)
        if result.ok:
            event_log.record(RemoteEventType.EXECUTED, cmd, {"ok": True})
        else:
            event_log.record(RemoteEventType.BLOCKED, cmd, {"error": result.error})

        adapter.send_result(cmd.source_chat_id, result)

        assert result.ok is True
        assert adapter.sent_count == 1
        assert event_log.event_count == 2

    def test_whatsapp_status_flow(self):
        adapter = WhatsAppAdapter()
        router = RemoteCommandRouter(dry_run=True)
        router.security.add_trusted(TrustedSource(
            source_type="WHATSAPP", identifier="+5511", max_command_risk="LOW",
        ))

        raw = {"phone_number": "+5511", "text": "!status"}
        cmd = adapter.parse_incoming(raw)

        result = router.route(cmd)
        adapter.send_result(cmd.source_chat_id, result)

        assert result.ok is True
        assert adapter.sent_count == 1

    def test_telegram_untrusted_blocked(self):
        adapter = TelegramAdapter()
        router = RemoteCommandRouter(dry_run=True)

        raw = {"chat_id": 123, "user_id": "unknown", "text": "/status"}
        cmd = adapter.parse_incoming(raw)
        result = router.route(cmd)

        assert result.ok is False
        assert result.status == CommandStatus.BLOCKED

    def test_approval_challenge_full_flow(self):
        router = RemoteCommandRouter(dry_run=True)
        cmd = RemoteCommand(source=CommandSource.CLI, command="run", risk=CommandRisk.MEDIUM)

        result1 = router.route(cmd)
        assert result1.status == CommandStatus.RECEIVED
        token = result1.metadata["challenge_token"]

        ok, _ = router.approve(token)
        assert ok is True

        cmd.approval_token = token
        cmd.approval_token_expires_at = "2099-01-01T00:00:00+00:00"
        result2 = router.route(cmd)
        assert result2.ok is True
        assert result2.status == CommandStatus.EXECUTED

    def test_push_from_telegram_blocked(self):
        adapter = TelegramAdapter()
        router = RemoteCommandRouter(dry_run=True)
        router.security.add_trusted(TrustedSource(
            source_type="TELEGRAM", identifier="user123", max_command_risk="LOW",
        ))

        raw = {"chat_id": 123, "user_id": "user123", "text": "/push"}
        cmd = adapter.parse_incoming(raw)
        result = router.route(cmd)

        assert result.ok is False
        assert result.status == CommandStatus.BLOCKED

    def test_rapid_fire_rate_limit(self):
        router = RemoteCommandRouter(dry_run=True)
        cmd = RemoteCommand(source=CommandSource.CLI, command="status", risk=CommandRisk.LOW)

        results = [router.route(cmd) for _ in range(11)]
        assert all(r.ok for r in results[:10])
        assert not results[10].ok
        assert "rate limit" in results[10].error

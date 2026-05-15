from src.remote_control.models import RemoteCommandResult, CommandStatus
from src.remote_control.telegram_adapter import TelegramMessage, TelegramAdapter


class TestTelegramMessage:
    def test_parse_bot_command(self):
        raw = {"chat_id": 123, "user_id": 456, "text": "/status"}
        msg = TelegramMessage.parse(raw)
        assert msg.command == "status"
        assert msg.is_bot_command is True

    def test_parse_command_with_args(self):
        raw = {"chat_id": 123, "user_id": 456, "text": "/run seogram"}
        msg = TelegramMessage.parse(raw)
        assert msg.command == "run"
        assert msg.args == ["seogram"]

    def test_parse_plain_text(self):
        raw = {"chat_id": 123, "user_id": 456, "text": "hello"}
        msg = TelegramMessage.parse(raw)
        assert msg.command == ""
        assert msg.is_bot_command is False


class TestTelegramAdapter:
    def test_parse_incoming_status(self):
        adapter = TelegramAdapter()
        cmd = adapter.parse_incoming({"chat_id": 123, "user_id": 456, "text": "/status"})
        assert cmd.source.value == "TELEGRAM"
        assert cmd.command == "status"
        assert cmd.risk.value == "LOW"

    def test_parse_incoming_deploy(self):
        adapter = TelegramAdapter()
        cmd = adapter.parse_incoming({"chat_id": 123, "user_id": 456, "text": "/deploy"})
        assert cmd.risk.value == "CRITICAL"

    def test_send_result(self):
        adapter = TelegramAdapter()
        result = RemoteCommandResult(ok=True, status=CommandStatus.EXECUTED, output="done")
        msg_id = adapter.send_result("chat_1", result)
        assert adapter.sent_count == 1
        assert adapter.last_sent["output"] == "done"

    def test_send_challenge(self):
        adapter = TelegramAdapter()
        msg_id = adapter.send_challenge("chat_1", "Approve this?")
        assert adapter.sent_count == 1
        assert adapter.last_sent["type"] == "challenge"

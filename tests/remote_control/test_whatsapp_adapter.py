from src.remote_control.models import RemoteCommandResult, CommandStatus
from src.remote_control.whatsapp_adapter import WhatsAppMessage, WhatsAppAdapter


class TestWhatsAppMessage:
    def test_parse_exclamation_command(self):
        raw = {"phone_number": "+5511999999999", "text": "!status"}
        msg = WhatsAppMessage.parse(raw)
        assert msg.command == "status"

    def test_parse_keyword_command(self):
        raw = {"phone_number": "+5511999999999", "text": "briefing"}
        msg = WhatsAppMessage.parse(raw)
        assert msg.command == "briefing"

    def test_parse_plain_text(self):
        raw = {"phone_number": "+5511999999999", "text": "olá tudo bem"}
        msg = WhatsAppMessage.parse(raw)
        assert msg.command == ""


class TestWhatsAppAdapter:
    def test_parse_incoming_status(self):
        adapter = WhatsAppAdapter()
        cmd = adapter.parse_incoming({"phone_number": "+5511", "text": "!status"})
        assert cmd.source.value == "WHATSAPP"
        assert cmd.command == "status"
        assert cmd.risk.value == "LOW"

    def test_parse_incoming_deploy(self):
        adapter = WhatsAppAdapter()
        cmd = adapter.parse_incoming({"phone_number": "+5511", "text": "!deploy"})
        assert cmd.risk.value == "CRITICAL"

    def test_send_result(self):
        adapter = WhatsAppAdapter()
        result = RemoteCommandResult(ok=True, status=CommandStatus.EXECUTED, output="ok")
        msg_id = adapter.send_result("+5511", result)
        assert adapter.sent_count == 1

    def test_send_template(self):
        adapter = WhatsAppAdapter()
        msg_id = adapter.send_template("+5511", "approval_challenge", ["run", "HIGH"])
        assert adapter.sent_count == 1
        assert adapter._sent_messages[0]["template_name"] == "approval_challenge"

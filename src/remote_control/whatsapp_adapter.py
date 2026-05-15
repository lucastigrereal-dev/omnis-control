from dataclasses import dataclass, field
from uuid import uuid4

from src.remote_control.models import RemoteCommand, RemoteCommandResult, CommandSource, CommandRisk


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WhatsAppMessage:
    message_id: str = field(default_factory=lambda: _new_id("wam_"))
    phone_number: str = ""
    text: str = ""
    command: str = ""
    media_urls: list[str] = field(default_factory=list)
    is_template: bool = False
    received_at: str = field(default_factory=_now_iso)
    metadata: dict = field(default_factory=dict)

    @classmethod
    def parse(cls, raw: dict) -> "WhatsAppMessage":
        text = raw.get("text", "")
        command = ""
        if text.startswith("!"):
            command = text[1:].strip()
        elif text.lower() in ("status", "briefing", "pending"):
            command = text.lower()
        return cls(
            phone_number=str(raw.get("phone_number", "")),
            text=text,
            command=command,
            media_urls=raw.get("media_urls", []),
            is_template=raw.get("is_template", False),
        )


class WhatsAppAdapter:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._sent_messages: list[dict] = []
        self._phone_id: str = ""
        self._token: str = ""

    def parse_incoming(self, raw: dict) -> RemoteCommand:
        msg = WhatsAppMessage.parse(raw)
        risk = CommandRisk.LOW
        if msg.command in ("run",):
            risk = CommandRisk.MEDIUM
        elif msg.command in ("deploy", "push"):
            risk = CommandRisk.CRITICAL

        return RemoteCommand(
            source=CommandSource.WHATSAPP,
            source_user_id=msg.phone_number,
            source_chat_id=msg.phone_number,
            command=msg.command,
            args={"has_media": bool(msg.media_urls), "is_template": msg.is_template},
            risk=risk,
            metadata={"raw_text": msg.text},
        )

    def send_result(self, phone: str, result: RemoteCommandResult) -> str:
        msg_id = _new_id("sent")
        self._sent_messages.append({
            "message_id": msg_id, "phone": phone,
            "ok": result.ok, "output": result.output, "error": result.error,
        })
        return msg_id

    def send_template(self, phone: str, template_name: str, params: list[str] | None = None) -> str:
        msg_id = _new_id("sent")
        self._sent_messages.append({
            "message_id": msg_id, "phone": phone,
            "type": "template", "template_name": template_name,
            "params": params or [],
        })
        return msg_id

    @property
    def sent_count(self) -> int:
        return len(self._sent_messages)

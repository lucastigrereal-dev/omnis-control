from dataclasses import dataclass, field
from uuid import uuid4

from src.remote_control.models import RemoteCommand, RemoteCommandResult, CommandSource, CommandRisk, CommandStatus


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TelegramMessage:
    message_id: str = field(default_factory=lambda: _new_id("tgm_"))
    chat_id: str = ""
    user_id: str = ""
    text: str = ""
    command: str = ""
    args: list[str] = field(default_factory=list)
    is_bot_command: bool = True
    received_at: str = field(default_factory=_now_iso)
    metadata: dict = field(default_factory=dict)

    @classmethod
    def parse(cls, raw: dict) -> "TelegramMessage":
        text = raw.get("text", "")
        command = ""
        args: list[str] = []
        if text.startswith("/"):
            parts = text[1:].split()
            command = parts[0] if parts else ""
            args = parts[1:] if len(parts) > 1 else []
        return cls(
            chat_id=str(raw.get("chat_id", "")),
            user_id=str(raw.get("user_id", "")),
            text=text,
            command=command,
            args=args,
            is_bot_command=text.startswith("/"),
        )


class TelegramAdapter:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._sent_messages: list[dict] = []
        self._webhook_url: str = ""

    def parse_incoming(self, raw: dict) -> RemoteCommand:
        msg = TelegramMessage.parse(raw)
        risk = CommandRisk.LOW
        if msg.command in ("run", "approve"):
            risk = CommandRisk.MEDIUM
        elif msg.command in ("deploy", "push"):
            risk = CommandRisk.CRITICAL

        return RemoteCommand(
            source=CommandSource.TELEGRAM,
            source_user_id=msg.user_id,
            source_chat_id=msg.chat_id,
            command=msg.command,
            args={"raw_args": msg.args},
            risk=risk,
            metadata={"raw_text": msg.text},
        )

    def send_result(self, chat_id: str, result: RemoteCommandResult) -> str:
        msg_id = _new_id("sent")
        self._sent_messages.append({
            "message_id": msg_id, "chat_id": chat_id,
            "ok": result.ok, "output": result.output, "error": result.error,
        })
        return msg_id

    def send_challenge(self, chat_id: str, challenge_message: str) -> str:
        msg_id = _new_id("sent")
        self._sent_messages.append({
            "message_id": msg_id, "chat_id": chat_id,
            "type": "challenge", "text": challenge_message,
        })
        return msg_id

    @property
    def sent_count(self) -> int:
        return len(self._sent_messages)

    @property
    def last_sent(self) -> dict | None:
        return self._sent_messages[-1] if self._sent_messages else None

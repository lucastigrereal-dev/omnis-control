"""W157 — Webhook Ingestion Gateway (parses inbound HTTP payloads into RemoteCommands, dry-run)."""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from typing import Optional

from .models import (
    CommandSource,
    CommandRisk,
    CommandStatus,
    RemoteCommand,
    _new_id,
    _now_iso,
)

# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------

_HIGH_RISK_KEYWORDS = {"rm_rf", "reset_hard", "force_push", "drop_db", "shutdown", "delete"}
_MEDIUM_RISK_KEYWORDS = {"deploy", "publish", "send", "post", "update", "patch"}


def _classify_risk(command: str) -> CommandRisk:
    cmd_lower = command.lower()
    if any(k in cmd_lower for k in _HIGH_RISK_KEYWORDS):
        return CommandRisk.HIGH
    if any(k in cmd_lower for k in _MEDIUM_RISK_KEYWORDS):
        return CommandRisk.MEDIUM
    return CommandRisk.LOW


# ---------------------------------------------------------------------------
# Webhook payload model
# ---------------------------------------------------------------------------

@dataclass
class WebhookPayload:
    """Raw inbound webhook from any HTTP source."""
    payload_id: str = field(default_factory=lambda: _new_id("wbp"))
    source: str = "UNKNOWN"
    headers: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)
    received_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "payload_id": self.payload_id,
            "source": self.source,
            "headers": self.headers,
            "body": self.body,
            "received_at": self.received_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WebhookPayload":
        return cls(
            payload_id=data.get("payload_id", _new_id("wbp")),
            source=data.get("source", "UNKNOWN"),
            headers=data.get("headers", {}),
            body=data.get("body", {}),
            received_at=data.get("received_at", _now_iso()),
        )


@dataclass
class WebhookIngestResult:
    result_id: str = field(default_factory=lambda: _new_id("wir"))
    payload_id: str = ""
    ok: bool = False
    command: Optional[RemoteCommand] = None
    error: str = ""
    rejected_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "payload_id": self.payload_id,
            "ok": self.ok,
            "command": self.command.to_dict() if self.command else None,
            "error": self.error,
            "rejected_reason": self.rejected_reason,
        }


# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------

def _verify_hmac(payload_body: bytes, signature: str, secret: str) -> bool:
    """Constant-time HMAC-SHA256 verification."""
    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.lstrip("sha256="))


# ---------------------------------------------------------------------------
# Source-specific parsers
# ---------------------------------------------------------------------------

def _parse_telegram(body: dict) -> tuple[str, dict, str, str]:
    """Returns (command, args, user_id, chat_id)."""
    message = body.get("message", {})
    text = message.get("text", "")
    user = message.get("from", {})
    chat = message.get("chat", {})
    parts = text.strip().lstrip("/").split(maxsplit=1)
    command = parts[0] if parts else ""
    args = {"text": parts[1]} if len(parts) > 1 else {}
    return command, args, str(user.get("id", "")), str(chat.get("id", ""))


def _parse_whatsapp(body: dict) -> tuple[str, dict, str, str]:
    entry = body.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value = changes.get("value", {})
    messages = value.get("messages", [{}])[0]
    text = messages.get("text", {}).get("body", "")
    user_id = messages.get("from", "")
    chat_id = value.get("metadata", {}).get("phone_number_id", "")
    parts = text.strip().lstrip("/").split(maxsplit=1)
    command = parts[0] if parts else ""
    args = {"text": parts[1]} if len(parts) > 1 else {}
    return command, args, user_id, chat_id


def _parse_generic(body: dict) -> tuple[str, dict, str, str]:
    command = body.get("command", "")
    args = body.get("args", {})
    user_id = body.get("user_id", "")
    chat_id = body.get("chat_id", "")
    return command, args, user_id, chat_id


_PARSERS = {
    "TELEGRAM": _parse_telegram,
    "WHATSAPP": _parse_whatsapp,
    "GENERIC": _parse_generic,
    "KRATOS": _parse_generic,
}

# ---------------------------------------------------------------------------
# Gateway
# ---------------------------------------------------------------------------

class WebhookGateway:
    """Ingests raw webhook payloads and emits RemoteCommand objects."""

    def __init__(
        self,
        webhook_secret: str = "",
        dry_run: bool = True,
        allowed_sources: Optional[list[str]] = None,
    ) -> None:
        self.webhook_secret = webhook_secret
        self.dry_run = dry_run
        self.allowed_sources = set(allowed_sources or ["TELEGRAM", "WHATSAPP", "GENERIC", "KRATOS"])
        self._ingested: list[WebhookPayload] = []
        self._commands: list[RemoteCommand] = []

    # ------------------------------------------------------------------
    def ingest(self, payload: WebhookPayload, raw_body: bytes = b"") -> WebhookIngestResult:
        self._ingested.append(payload)
        result = WebhookIngestResult(payload_id=payload.payload_id)

        # Source allow-list
        if payload.source not in self.allowed_sources:
            result.rejected_reason = f"source_not_allowed:{payload.source}"
            return result

        # Signature check (optional — only when secret configured)
        if self.webhook_secret:
            sig = payload.headers.get("X-Hub-Signature-256", "")
            if not sig:
                result.rejected_reason = "missing_signature"
                return result
            if not _verify_hmac(raw_body, sig, self.webhook_secret):
                result.rejected_reason = "invalid_signature"
                return result

        # Parse
        parser = _PARSERS.get(payload.source, _parse_generic)
        try:
            command_str, args, user_id, chat_id = parser(payload.body)
        except Exception as exc:
            result.error = f"parse_error:{exc}"
            return result

        if not command_str:
            result.rejected_reason = "empty_command"
            return result

        risk = _classify_risk(command_str)
        source_enum = CommandSource(payload.source) if payload.source in CommandSource._value2member_map_ else CommandSource.CLI

        cmd = RemoteCommand(
            source=source_enum,
            source_user_id=user_id,
            source_chat_id=chat_id,
            command=command_str,
            args=args,
            risk=risk,
            status=CommandStatus.RECEIVED,
            requires_approval=risk in (CommandRisk.HIGH, CommandRisk.CRITICAL),
            dry_run=self.dry_run,
            metadata={"payload_id": payload.payload_id, "source_raw": payload.source},
        )
        self._commands.append(cmd)
        result.ok = True
        result.command = cmd
        return result

    def get_ingested(self) -> list[WebhookPayload]:
        return list(self._ingested)

    def get_commands(self) -> list[RemoteCommand]:
        return list(self._commands)

    def stats(self) -> dict:
        return {
            "total_ingested": len(self._ingested),
            "total_commands": len(self._commands),
            "dry_run": self.dry_run,
        }

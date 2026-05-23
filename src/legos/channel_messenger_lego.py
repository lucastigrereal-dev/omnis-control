"""ChannelMessengerLego — dispatch outbound multi-canal (WhatsApp + Telegram).

Outbound counterpart dos adapters inbound em remote_control/.
Envia conteúdo (relatórios, alerts, notificações) para canais configurados.

APIs usadas:
  WhatsApp — Meta Cloud API (graph.facebook.com/v20.0)
  Telegram  — Bot API (api.telegram.org/bot{token}/sendMessage)

Ambas via urllib.request — sem dependência nova.

Regras OMNIS:
  - dry_run=True por padrão — registra intenção, não chama API
  - Approval gate para envios "broadcast" / "massa"
  - Semaphore(2) — no máximo 2 dispatches simultâneos (WA + TG em paralelo)
  - cost_local_pct=100 (nenhuma chamada LLM)
  - Não lê .env — consome env vars via os.getenv com fallback vazio
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone

from src.interfaces.channel_messenger import (
    ChannelMessenger, MessageSpec, MessageResult, ChannelDelivery,
)

_logger = logging.getLogger("omnis.legos.messenger")

# ── env vars (sem defaults que exponham credenciais) ──────────────────────────
WA_PHONE_ID = os.getenv("WA_PHONE_ID", "")
WA_API_TOKEN = os.getenv("WA_API_TOKEN", "")
WA_API_URL = os.getenv("WA_API_URL", "https://graph.facebook.com/v20.0")
WA_DEFAULT_RECIPIENT = os.getenv("WA_DEFAULT_RECIPIENT", "")

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_DEFAULT_CHAT_ID = os.getenv("TG_DEFAULT_CHAT_ID", "")
TG_API_URL = "https://api.telegram.org"

_DISPATCH_SEMAPHORE = threading.Semaphore(2)

_SUPPORTED_CHANNELS = frozenset({"whatsapp", "telegram"})

_BROADCAST_KEYWORDS = frozenset({
    "broadcast", "massa", "mass", "todos os contatos", "all contacts",
    "promoção", "promocao", "bulk", "lista",
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _requires_broadcast_approval(content: str) -> bool:
    low = content.lower()
    return any(kw in low for kw in _BROADCAST_KEYWORDS)


def _expand_channels(channels: list[str]) -> list[str]:
    """Expande 'all' para todos os canais suportados."""
    if "all" in channels:
        return list(_SUPPORTED_CHANNELS)
    return [c.lower() for c in channels if c.lower() in _SUPPORTED_CHANNELS]


# ── ChannelMessengerLego ──────────────────────────────────────────────────────

class ChannelMessengerLego:
    """Implementação do Protocol ChannelMessenger.

    dispatch outbound multi-canal: WhatsApp (Meta Cloud API) + Telegram (Bot API).
    Injeção de dependência para mocking nos testes via _http_post.
    """

    def __init__(self, _http_post=None) -> None:
        # Permite injetar um mock de HTTP em testes sem monkeypatch global
        self._http_post = _http_post or _real_http_post

    def health_check(self) -> bool:
        """Retorna True se ao menos um canal está configurado."""
        wa_ready = bool(WA_PHONE_ID and WA_API_TOKEN)
        tg_ready = bool(TG_BOT_TOKEN)
        return wa_ready or tg_ready

    def send(self, spec: MessageSpec) -> MessageResult:
        """Despacha mensagem para os canais em spec.channels."""
        if not spec.dry_run and _requires_broadcast_approval(spec.content):
            _logger.warning("[messenger] APPROVAL REQUIRED — broadcast keywords detected")
            return MessageResult(
                success=False, dry_run=False,
                error="approval_required",
                artifacts={"approval_required": True},
            )

        if spec.dry_run:
            return self._dry_run_send(spec)

        channels = _expand_channels(spec.channels)
        if not channels:
            return MessageResult(
                success=False, dry_run=False,
                error="no_valid_channels",
                artifacts={"requested": spec.channels},
            )

        acquired = _DISPATCH_SEMAPHORE.acquire(timeout=10)
        if not acquired:
            return MessageResult(
                success=False, dry_run=False,
                error="dispatch_semaphore_timeout",
            )

        try:
            deliveries: list[ChannelDelivery] = []
            for channel in channels:
                if channel == "whatsapp":
                    deliveries.append(self._send_whatsapp(spec))
                elif channel == "telegram":
                    deliveries.append(self._send_telegram(spec))

            success = any(d.success for d in deliveries)
            return MessageResult(
                success=success,
                deliveries=deliveries,
                dry_run=False,
                artifacts={
                    "channels_attempted": channels,
                    "delivered": [d.channel for d in deliveries if d.success],
                    "failed": [d.channel for d in deliveries if not d.success],
                    "cost_local_pct": 100,
                },
            )
        finally:
            _DISPATCH_SEMAPHORE.release()

    async def send_async(self, spec: MessageSpec) -> MessageResult:
        """Wrapper async — não trava o runtime OMNIS."""
        return await asyncio.to_thread(self.send, spec)

    # ── channel implementations ───────────────────────────────────────────────

    def _send_whatsapp(self, spec: MessageSpec) -> ChannelDelivery:
        if not (WA_PHONE_ID and WA_API_TOKEN):
            return ChannelDelivery(channel="whatsapp", success=False, error="whatsapp_not_configured")

        recipient = spec.recipient or WA_DEFAULT_RECIPIENT
        if not recipient:
            return ChannelDelivery(channel="whatsapp", success=False, error="whatsapp_no_recipient")

        payload = json.dumps({
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": spec.content[:4096]},
        }).encode("utf-8")

        url = f"{WA_API_URL}/{WA_PHONE_ID}/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {WA_API_TOKEN}",
        }

        try:
            data = self._http_post(url, payload, headers, timeout=10)
            msg_id = (data.get("messages") or [{}])[0].get("id", "")
            _logger.info("[messenger][%s] WA sent: %s → msg_id=%s", _now_iso(), recipient[:6] + "...", msg_id)
            return ChannelDelivery(channel="whatsapp", success=True, message_id=msg_id)
        except Exception as exc:
            _logger.error("[messenger] WA send failed: %s", exc)
            return ChannelDelivery(channel="whatsapp", success=False, error=str(exc)[:200])

    def _send_telegram(self, spec: MessageSpec) -> ChannelDelivery:
        if not TG_BOT_TOKEN:
            return ChannelDelivery(channel="telegram", success=False, error="telegram_not_configured")

        chat_id = spec.recipient or TG_DEFAULT_CHAT_ID
        if not chat_id:
            return ChannelDelivery(channel="telegram", success=False, error="telegram_no_chat_id")

        payload_dict: dict = {"chat_id": chat_id, "text": spec.content[:4096]}
        if spec.parse_mode == "markdown":
            payload_dict["parse_mode"] = "Markdown"

        payload = json.dumps(payload_dict).encode("utf-8")
        url = f"{TG_API_URL}/bot{TG_BOT_TOKEN}/sendMessage"
        headers = {"Content-Type": "application/json"}

        try:
            data = self._http_post(url, payload, headers, timeout=10)
            msg_id = str(data.get("result", {}).get("message_id", ""))
            _logger.info("[messenger][%s] TG sent: chat=%s msg_id=%s", _now_iso(), chat_id, msg_id)
            return ChannelDelivery(channel="telegram", success=True, message_id=msg_id)
        except Exception as exc:
            _logger.error("[messenger] TG send failed: %s", exc)
            return ChannelDelivery(channel="telegram", success=False, error=str(exc)[:200])

    def _dry_run_send(self, spec: MessageSpec) -> MessageResult:
        channels = _expand_channels(spec.channels)
        deliveries = [
            ChannelDelivery(channel=ch, success=True, message_id=f"dry_{ch}_sim")
            for ch in (channels or list(_SUPPORTED_CHANNELS))
        ]
        return MessageResult(
            success=True,
            deliveries=deliveries,
            dry_run=True,
            artifacts={
                "mode": "dry_run",
                "channels": [d.channel for d in deliveries],
                "content_len": len(spec.content),
                "cost_local_pct": 100,
            },
        )


# ── HTTP helper ───────────────────────────────────────────────────────────────

def _real_http_post(url: str, data: bytes, headers: dict, timeout: int = 10) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

"""Testes do ChannelMessengerLego — OMNIS dispatch outbound multi-canal."""
from __future__ import annotations

import asyncio

import pytest

from src.interfaces.channel_messenger import (
    MessageSpec, MessageResult, ChannelDelivery,
)
from src.legos.channel_messenger_lego import (
    ChannelMessengerLego,
    _requires_broadcast_approval,
    _expand_channels,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _wa_http_ok(url, data, headers, timeout=10):
    return {"messages": [{"id": "wamid_abc123"}]}


def _tg_http_ok(url, data, headers, timeout=10):
    return {"ok": True, "result": {"message_id": 42}}


def _http_fail(url, data, headers, timeout=10):
    raise ConnectionError("API offline")


def _make_lego(http_post=None):
    return ChannelMessengerLego(_http_post=http_post or _wa_http_ok)


# ── utility functions ─────────────────────────────────────────────────────────

def test_broadcast_keyword_blocked():
    assert _requires_broadcast_approval("enviar broadcast para todos") is True

def test_mass_keyword_blocked():
    assert _requires_broadcast_approval("envio em massa para lista") is True

def test_normal_content_not_blocked():
    assert _requires_broadcast_approval("relatório de pesquisa semanal") is False

def test_expand_channels_all():
    channels = _expand_channels(["all"])
    assert "whatsapp" in channels
    assert "telegram" in channels

def test_expand_channels_explicit():
    assert _expand_channels(["whatsapp"]) == ["whatsapp"]

def test_expand_channels_unknown_filtered():
    assert _expand_channels(["sms", "email"]) == []

def test_expand_channels_case_insensitive():
    assert _expand_channels(["WhatsApp"]) == ["whatsapp"]


# ── approval gate ─────────────────────────────────────────────────────────────

def test_broadcast_approval_required(monkeypatch):
    monkeypatch.setenv("WA_PHONE_ID", "1234")
    monkeypatch.setenv("WA_API_TOKEN", "token")
    lego = _make_lego()
    spec = MessageSpec(content="bulk broadcast para todos os contatos", dry_run=False)
    result = lego.send(spec)
    assert result.success is False
    assert result.error == "approval_required"
    assert result.artifacts.get("approval_required") is True


def test_dry_run_not_blocked_by_broadcast():
    lego = _make_lego()
    spec = MessageSpec(content="bulk broadcast para todos os contatos", dry_run=True)
    result = lego.send(spec)
    assert result.error != "approval_required"
    assert result.success is True


# ── health_check ──────────────────────────────────────────────────────────────

def test_health_check_returns_bool():
    assert isinstance(ChannelMessengerLego().health_check(), bool)


def test_health_check_true_when_wa_configured(monkeypatch):
    monkeypatch.setenv("WA_PHONE_ID", "1234")
    monkeypatch.setenv("WA_API_TOKEN", "mytoken")
    import importlib
    import src.legos.channel_messenger_lego as mod
    monkeypatch.setattr(mod, "WA_PHONE_ID", "1234")
    monkeypatch.setattr(mod, "WA_API_TOKEN", "mytoken")
    assert ChannelMessengerLego().health_check() is True


def test_health_check_true_when_tg_configured(monkeypatch):
    import src.legos.channel_messenger_lego as mod
    monkeypatch.setattr(mod, "TG_BOT_TOKEN", "bot_token_xyz")
    monkeypatch.setattr(mod, "WA_PHONE_ID", "")
    monkeypatch.setattr(mod, "WA_API_TOKEN", "")
    assert ChannelMessengerLego().health_check() is True


def test_health_check_false_when_nothing_configured(monkeypatch):
    import src.legos.channel_messenger_lego as mod
    monkeypatch.setattr(mod, "WA_PHONE_ID", "")
    monkeypatch.setattr(mod, "WA_API_TOKEN", "")
    monkeypatch.setattr(mod, "TG_BOT_TOKEN", "")
    assert ChannelMessengerLego().health_check() is False


# ── dry_run ───────────────────────────────────────────────────────────────────

def test_dry_run_returns_success():
    lego = _make_lego()
    result = lego.send(MessageSpec(content="hello", dry_run=True))
    assert result.success is True
    assert result.dry_run is True


def test_dry_run_no_real_http_called():
    called = []
    def _sentinel(*_a, **_kw):
        called.append(True)
        return {}
    lego = ChannelMessengerLego(_http_post=_sentinel)
    lego.send(MessageSpec(content="test", dry_run=True, channels=["all"]))
    assert called == []


def test_dry_run_deliveries_recorded():
    lego = _make_lego()
    result = lego.send(MessageSpec(content="msg", dry_run=True, channels=["whatsapp"]))
    assert len(result.deliveries) >= 1
    assert all(d.success for d in result.deliveries)


def test_dry_run_artifacts_has_mode():
    lego = _make_lego()
    result = lego.send(MessageSpec(content="x", dry_run=True))
    assert result.artifacts.get("mode") == "dry_run"


def test_dry_run_artifacts_cost_local_pct():
    lego = _make_lego()
    result = lego.send(MessageSpec(content="x", dry_run=True))
    assert result.artifacts.get("cost_local_pct") == 100


# ── WhatsApp real send ────────────────────────────────────────────────────────

def test_whatsapp_send_success(monkeypatch):
    import src.legos.channel_messenger_lego as mod
    monkeypatch.setattr(mod, "WA_PHONE_ID", "111")
    monkeypatch.setattr(mod, "WA_API_TOKEN", "tok")
    monkeypatch.setattr(mod, "WA_DEFAULT_RECIPIENT", "")
    lego = ChannelMessengerLego(_http_post=_wa_http_ok)
    spec = MessageSpec(
        content="Relatório semanal pronto",
        channels=["whatsapp"],
        recipient="5584999999999",
        dry_run=False,
    )
    result = lego.send(spec)
    assert result.success is True
    wa = next(d for d in result.deliveries if d.channel == "whatsapp")
    assert wa.message_id == "wamid_abc123"


def test_whatsapp_not_configured_returns_error(monkeypatch):
    import src.legos.channel_messenger_lego as mod
    monkeypatch.setattr(mod, "WA_PHONE_ID", "")
    monkeypatch.setattr(mod, "WA_API_TOKEN", "")
    lego = ChannelMessengerLego(_http_post=_wa_http_ok)
    spec = MessageSpec(content="msg", channels=["whatsapp"], recipient="5584x", dry_run=False)
    result = lego.send(spec)
    wa = next(d for d in result.deliveries if d.channel == "whatsapp")
    assert wa.success is False
    assert "not_configured" in (wa.error or "")


def test_whatsapp_no_recipient_returns_error(monkeypatch):
    import src.legos.channel_messenger_lego as mod
    monkeypatch.setattr(mod, "WA_PHONE_ID", "111")
    monkeypatch.setattr(mod, "WA_API_TOKEN", "tok")
    monkeypatch.setattr(mod, "WA_DEFAULT_RECIPIENT", "")
    lego = ChannelMessengerLego(_http_post=_wa_http_ok)
    spec = MessageSpec(content="msg", channels=["whatsapp"], recipient="", dry_run=False)
    result = lego.send(spec)
    wa = next(d for d in result.deliveries if d.channel == "whatsapp")
    assert wa.success is False
    assert "no_recipient" in (wa.error or "")


def test_whatsapp_api_failure_returns_error(monkeypatch):
    import src.legos.channel_messenger_lego as mod
    monkeypatch.setattr(mod, "WA_PHONE_ID", "111")
    monkeypatch.setattr(mod, "WA_API_TOKEN", "tok")
    lego = ChannelMessengerLego(_http_post=_http_fail)
    spec = MessageSpec(content="msg", channels=["whatsapp"], recipient="5584x", dry_run=False)
    result = lego.send(spec)
    wa = next(d for d in result.deliveries if d.channel == "whatsapp")
    assert wa.success is False
    assert wa.error is not None


# ── Telegram real send ────────────────────────────────────────────────────────

def test_telegram_send_success(monkeypatch):
    import src.legos.channel_messenger_lego as mod
    monkeypatch.setattr(mod, "TG_BOT_TOKEN", "bot123")
    monkeypatch.setattr(mod, "TG_DEFAULT_CHAT_ID", "")
    lego = ChannelMessengerLego(_http_post=_tg_http_ok)
    spec = MessageSpec(
        content="Alert: pipeline concluído",
        channels=["telegram"],
        recipient="987654",
        dry_run=False,
    )
    result = lego.send(spec)
    assert result.success is True
    tg = next(d for d in result.deliveries if d.channel == "telegram")
    assert tg.message_id == "42"


def test_telegram_not_configured_returns_error(monkeypatch):
    import src.legos.channel_messenger_lego as mod
    monkeypatch.setattr(mod, "TG_BOT_TOKEN", "")
    lego = ChannelMessengerLego(_http_post=_tg_http_ok)
    spec = MessageSpec(content="msg", channels=["telegram"], recipient="123", dry_run=False)
    result = lego.send(spec)
    tg = next(d for d in result.deliveries if d.channel == "telegram")
    assert tg.success is False
    assert "not_configured" in (tg.error or "")


def test_telegram_no_chat_id_returns_error(monkeypatch):
    import src.legos.channel_messenger_lego as mod
    monkeypatch.setattr(mod, "TG_BOT_TOKEN", "bot123")
    monkeypatch.setattr(mod, "TG_DEFAULT_CHAT_ID", "")
    lego = ChannelMessengerLego(_http_post=_tg_http_ok)
    spec = MessageSpec(content="msg", channels=["telegram"], recipient="", dry_run=False)
    result = lego.send(spec)
    tg = next(d for d in result.deliveries if d.channel == "telegram")
    assert tg.success is False
    assert "no_chat_id" in (tg.error or "")


# ── multi-canal fan-out ───────────────────────────────────────────────────────

def test_all_channels_dispatched(monkeypatch):
    import src.legos.channel_messenger_lego as mod
    monkeypatch.setattr(mod, "WA_PHONE_ID", "111")
    monkeypatch.setattr(mod, "WA_API_TOKEN", "tok")
    monkeypatch.setattr(mod, "TG_BOT_TOKEN", "bot")
    monkeypatch.setattr(mod, "WA_DEFAULT_RECIPIENT", "5584x")
    monkeypatch.setattr(mod, "TG_DEFAULT_CHAT_ID", "chat1")

    responses = {
        "whatsapp": {"messages": [{"id": "wa_id"}]},
        "telegram": {"ok": True, "result": {"message_id": 1}},
    }

    def _smart_http(url, data, headers, timeout=10):
        if "graph.facebook" in url:
            return responses["whatsapp"]
        return responses["telegram"]

    lego = ChannelMessengerLego(_http_post=_smart_http)
    spec = MessageSpec(content="news", channels=["all"], dry_run=False)
    result = lego.send(spec)
    assert result.delivered_count == 2
    assert result.failed_count == 0


def test_partial_success_when_one_channel_fails(monkeypatch):
    import src.legos.channel_messenger_lego as mod
    monkeypatch.setattr(mod, "WA_PHONE_ID", "111")
    monkeypatch.setattr(mod, "WA_API_TOKEN", "tok")
    monkeypatch.setattr(mod, "TG_BOT_TOKEN", "bot")
    monkeypatch.setattr(mod, "WA_DEFAULT_RECIPIENT", "5584x")
    monkeypatch.setattr(mod, "TG_DEFAULT_CHAT_ID", "chat1")

    def _wa_ok_tg_fail(url, data, headers, timeout=10):
        if "graph.facebook" in url:
            return {"messages": [{"id": "wa_id"}]}
        raise ConnectionError("TG offline")

    lego = ChannelMessengerLego(_http_post=_wa_ok_tg_fail)
    spec = MessageSpec(content="news", channels=["all"], dry_run=False)
    result = lego.send(spec)
    # At least WA succeeded — overall success=True
    assert result.success is True
    assert result.delivered_count >= 1


def test_no_valid_channels_returns_error():
    lego = _make_lego()
    spec = MessageSpec(content="msg", channels=["sms", "email"], dry_run=False)
    result = lego.send(spec)
    assert result.success is False
    assert result.error == "no_valid_channels"


def test_non_broadcast_real_flow_not_blocked_by_approval():
    """Mensagem normal em modo real não deve cair no gate de broadcast."""
    lego = _make_lego()
    spec = MessageSpec(content="status semanal pronto", channels=["sms"], dry_run=False)
    result = lego.send(spec)
    assert result.error != "approval_required"
    assert result.error == "no_valid_channels"


def test_send_returns_timeout_when_dispatch_semaphore_busy(monkeypatch):
    import src.legos.channel_messenger_lego as mod

    class _BusySemaphore:
        def acquire(self, timeout=10):
            return False

        def release(self):
            return None

    monkeypatch.setattr(mod, "_DISPATCH_SEMAPHORE", _BusySemaphore())
    lego = ChannelMessengerLego(_http_post=_wa_http_ok)
    result = lego.send(MessageSpec(content="msg", channels=["all"], dry_run=False))
    assert result.success is False
    assert result.error == "dispatch_semaphore_timeout"


# ── MessageResult properties ──────────────────────────────────────────────────

def test_delivered_count_property():
    result = MessageResult(
        success=True,
        deliveries=[
            ChannelDelivery("whatsapp", True),
            ChannelDelivery("telegram", False, error="fail"),
        ],
    )
    assert result.delivered_count == 1
    assert result.failed_count == 1


# ── async wrapper ─────────────────────────────────────────────────────────────

def test_send_async_returns_result():
    lego = _make_lego()
    spec = MessageSpec(content="async test", dry_run=True)
    result = asyncio.get_event_loop().run_until_complete(lego.send_async(spec))
    assert isinstance(result, MessageResult)
    assert result.success is True


# ── Protocol compliance ───────────────────────────────────────────────────────

def test_lego_satisfies_channel_messenger_protocol():
    from src.interfaces.channel_messenger import ChannelMessenger
    lego: ChannelMessenger = ChannelMessengerLego()
    assert hasattr(lego, "send")
    assert hasattr(lego, "health_check")

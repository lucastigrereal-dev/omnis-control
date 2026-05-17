"""W157 — Tests for WebhookGateway."""
import pytest
from src.remote_control.webhook_gateway import (
    WebhookGateway,
    WebhookPayload,
    _classify_risk,
    _verify_hmac,
)
from src.remote_control.models import CommandRisk, CommandSource, CommandStatus


# ---------------------------------------------------------------------------
# Risk classifier
# ---------------------------------------------------------------------------

def test_classify_low_risk():
    assert _classify_risk("status") == CommandRisk.LOW


def test_classify_medium_risk():
    assert _classify_risk("publish_post") == CommandRisk.MEDIUM


def test_classify_high_risk():
    assert _classify_risk("rm_rf /tmp") == CommandRisk.HIGH


def test_classify_delete_high():
    assert _classify_risk("delete_app") == CommandRisk.HIGH


# ---------------------------------------------------------------------------
# HMAC verification
# ---------------------------------------------------------------------------

def test_hmac_valid():
    import hashlib, hmac as hmac_mod
    secret = "mysecret"
    body = b'{"command":"status"}'
    sig = hmac_mod.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert _verify_hmac(body, sig, secret)


def test_hmac_invalid():
    assert not _verify_hmac(b"body", "badsig", "secret")


def test_hmac_sha256_prefix_stripped():
    import hashlib, hmac as hmac_mod
    secret = "mysecret"
    body = b'{"command":"status"}'
    sig = "sha256=" + hmac_mod.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert _verify_hmac(body, sig, secret)


# ---------------------------------------------------------------------------
# WebhookPayload round-trip
# ---------------------------------------------------------------------------

def test_payload_round_trip():
    p = WebhookPayload(source="TELEGRAM", body={"message": {"text": "/status"}})
    d = p.to_dict()
    p2 = WebhookPayload.from_dict(d)
    assert p2.source == "TELEGRAM"
    assert p2.body == p.body


# ---------------------------------------------------------------------------
# Gateway — basic ingestion
# ---------------------------------------------------------------------------

def _make_gateway(**kwargs) -> WebhookGateway:
    return WebhookGateway(dry_run=True, **kwargs)


def _telegram_payload(text: str) -> WebhookPayload:
    return WebhookPayload(
        source="TELEGRAM",
        body={"message": {"text": text, "from": {"id": 111}, "chat": {"id": 222}}},
    )


def test_ingest_telegram_status():
    gw = _make_gateway()
    result = gw.ingest(_telegram_payload("/status"))
    assert result.ok
    assert result.command is not None
    assert result.command.command == "status"
    assert result.command.source == CommandSource.TELEGRAM
    assert result.command.dry_run is True


def test_ingest_telegram_low_risk():
    gw = _make_gateway()
    result = gw.ingest(_telegram_payload("/ping"))
    assert result.command.risk == CommandRisk.LOW
    assert result.command.requires_approval is False


def test_ingest_telegram_high_risk_requires_approval():
    gw = _make_gateway()
    result = gw.ingest(_telegram_payload("/rm_rf /data"))
    assert result.command.risk == CommandRisk.HIGH
    assert result.command.requires_approval is True


def test_ingest_telegram_medium_risk():
    gw = _make_gateway()
    result = gw.ingest(_telegram_payload("/publish daily"))
    assert result.command.risk == CommandRisk.MEDIUM


def test_ingest_telegram_args():
    gw = _make_gateway()
    result = gw.ingest(_telegram_payload("/run_wave W157"))
    assert result.command.args == {"text": "W157"}


def test_ingest_telegram_empty_text():
    gw = _make_gateway()
    p = WebhookPayload(source="TELEGRAM", body={"message": {"text": ""}})
    result = gw.ingest(p)
    assert not result.ok
    assert result.rejected_reason == "empty_command"


# ---------------------------------------------------------------------------
# WhatsApp
# ---------------------------------------------------------------------------

def _whatsapp_payload(text: str) -> WebhookPayload:
    return WebhookPayload(
        source="WHATSAPP",
        body={
            "entry": [{"changes": [{"value": {
                "messages": [{"text": {"body": text}, "from": "5511999999999"}],
                "metadata": {"phone_number_id": "phone_001"},
            }}]}]
        },
    )


def test_ingest_whatsapp_command():
    gw = _make_gateway()
    result = gw.ingest(_whatsapp_payload("/briefing"))
    assert result.ok
    assert result.command.command == "briefing"
    assert result.command.source == CommandSource.WHATSAPP


# ---------------------------------------------------------------------------
# Generic / KRATOS
# ---------------------------------------------------------------------------

def test_ingest_generic():
    gw = _make_gateway()
    p = WebhookPayload(source="GENERIC", body={"command": "health_check", "args": {"verbose": True}})
    result = gw.ingest(p)
    assert result.ok
    assert result.command.command == "health_check"
    assert result.command.args == {"verbose": True}


def test_ingest_kratos():
    gw = _make_gateway()
    p = WebhookPayload(source="KRATOS", body={"command": "deploy", "user_id": "kratos_1"})
    result = gw.ingest(p)
    assert result.ok
    assert result.command.risk == CommandRisk.MEDIUM


# ---------------------------------------------------------------------------
# Source allow-list
# ---------------------------------------------------------------------------

def test_reject_unknown_source():
    gw = _make_gateway()
    p = WebhookPayload(source="SLACK", body={"command": "status"})
    result = gw.ingest(p)
    assert not result.ok
    assert "source_not_allowed" in result.rejected_reason


def test_custom_allowed_sources():
    gw = WebhookGateway(allowed_sources=["SLACK"], dry_run=True)
    p = WebhookPayload(source="SLACK", body={"command": "status"})
    result = gw.ingest(p)
    assert result.ok


# ---------------------------------------------------------------------------
# Signature enforcement
# ---------------------------------------------------------------------------

def test_signature_required_when_secret_set():
    gw = WebhookGateway(webhook_secret="s3cr3t", dry_run=True)
    p = WebhookPayload(source="GENERIC", body={"command": "status"})
    result = gw.ingest(p, raw_body=b'{"command":"status"}')
    assert not result.ok
    assert result.rejected_reason == "missing_signature"


def test_signature_valid_passes():
    import hashlib, hmac as hmac_mod
    secret = "s3cr3t"
    body = b'{"command":"status"}'
    sig = hmac_mod.new(secret.encode(), body, hashlib.sha256).hexdigest()
    gw = WebhookGateway(webhook_secret=secret, dry_run=True)
    p = WebhookPayload(
        source="GENERIC",
        headers={"X-Hub-Signature-256": sig},
        body={"command": "status"},
    )
    result = gw.ingest(p, raw_body=body)
    assert result.ok


def test_signature_invalid_rejects():
    gw = WebhookGateway(webhook_secret="s3cr3t", dry_run=True)
    p = WebhookPayload(
        source="GENERIC",
        headers={"X-Hub-Signature-256": "bad"},
        body={"command": "status"},
    )
    result = gw.ingest(p, raw_body=b'{"command":"status"}')
    assert not result.ok
    assert result.rejected_reason == "invalid_signature"


# ---------------------------------------------------------------------------
# Stats and collections
# ---------------------------------------------------------------------------

def test_gateway_stats():
    gw = _make_gateway()
    gw.ingest(_telegram_payload("/ping"))
    gw.ingest(_telegram_payload("/status"))
    stats = gw.stats()
    assert stats["total_ingested"] == 2
    assert stats["total_commands"] == 2
    assert stats["dry_run"] is True


def test_get_commands():
    gw = _make_gateway()
    gw.ingest(_telegram_payload("/ping"))
    cmds = gw.get_commands()
    assert len(cmds) == 1
    assert cmds[0].command == "ping"


def test_get_ingested():
    gw = _make_gateway()
    p = _telegram_payload("/status")
    gw.ingest(p)
    ingested = gw.get_ingested()
    assert len(ingested) == 1
    assert ingested[0].payload_id == p.payload_id


def test_rejected_not_added_to_commands():
    gw = _make_gateway()
    p = WebhookPayload(source="SLACK", body={"command": "status"})
    gw.ingest(p)
    assert gw.get_commands() == []
    assert len(gw.get_ingested()) == 1


# ---------------------------------------------------------------------------
# to_dict round-trips
# ---------------------------------------------------------------------------

def test_ingest_result_to_dict():
    gw = _make_gateway()
    result = gw.ingest(_telegram_payload("/briefing"))
    d = result.to_dict()
    assert d["ok"] is True
    assert d["command"] is not None
    assert d["command"]["source"] == "TELEGRAM"


def test_command_status_is_received():
    gw = _make_gateway()
    result = gw.ingest(_telegram_payload("/run"))
    assert result.command.status == CommandStatus.RECEIVED


def test_metadata_payload_id_linked():
    gw = _make_gateway()
    p = _telegram_payload("/wave")
    result = gw.ingest(p)
    assert result.command.metadata["payload_id"] == p.payload_id

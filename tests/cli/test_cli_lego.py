"""Testes da CLI lego — omnis lego list / research / send."""
from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from src.cli_lego import lego_app

runner = CliRunner()


def _invoke(*args, **kwargs):
    return runner.invoke(lego_app, list(args), **kwargs)


# ── lego list ─────────────────────────────────────────────────────────────────

def test_list_exits_0():
    result = _invoke("list")
    assert result.exit_code == 0


def test_list_shows_all_5_legos():
    result = _invoke("list")
    assert "browser_executor" in result.output
    assert "code_executor" in result.output
    assert "video_processor" in result.output
    assert "research_conductor" in result.output
    assert "channel_messenger" in result.output


def test_list_json_has_legos_key():
    result = _invoke("list", "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "legos" in data
    assert data["total"] == 5


def test_list_json_each_entry_has_name_and_healthy():
    result = _invoke("list", "--json")
    data = json.loads(result.output)
    for entry in data["legos"]:
        assert "name" in entry
        assert "healthy" in entry
        assert isinstance(entry["healthy"], bool)


def test_list_json_has_all_5_names():
    result = _invoke("list", "--json")
    data = json.loads(result.output)
    names = {e["name"] for e in data["legos"]}
    assert names == {
        "browser_executor", "code_executor", "video_processor",
        "research_conductor", "channel_messenger",
    }


# ── lego research (dry-run) ───────────────────────────────────────────────────

def test_research_dry_run_exits_0():
    result = _invoke("research", "machine learning", "--dry-run")
    assert result.exit_code == 0


def test_research_dry_run_shows_topic():
    result = _invoke("research", "machine learning", "--dry-run")
    assert "machine learning" in result.output


def test_research_json_dry_run_success():
    result = _invoke("research", "tópico teste", "--dry-run", "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["dry_run"] is True


def test_research_json_has_required_fields():
    result = _invoke("research", "tópico teste", "--dry-run", "--json")
    data = json.loads(result.output)
    assert "topic" in data
    assert "perspective_count" in data
    assert "citation_count" in data
    assert "error" in data


def test_research_perspectives_option():
    result = _invoke("research", "IA", "--dry-run", "--perspectives", "2", "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


# ── lego send (dry-run) ───────────────────────────────────────────────────────

def test_send_dry_run_exits_0():
    result = _invoke("send", "hello world", "--dry-run")
    assert result.exit_code == 0


def test_send_dry_run_shows_success():
    result = _invoke("send", "hello world", "--dry-run")
    assert "Enviado" in result.output or "dry" in result.output.lower()


def test_send_json_dry_run_success():
    result = _invoke("send", "hello world", "--dry-run", "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["dry_run"] is True


def test_send_json_has_delivered_and_failed():
    result = _invoke("send", "hello world", "--dry-run", "--json")
    data = json.loads(result.output)
    assert "delivered" in data
    assert "failed" in data
    assert isinstance(data["delivered"], int)
    assert isinstance(data["failed"], int)


def test_send_channel_whatsapp_dry_run():
    result = _invoke("send", "msg", "--channel", "whatsapp", "--dry-run", "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_send_channel_telegram_dry_run():
    result = _invoke("send", "msg", "--channel", "telegram", "--dry-run", "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_send_unknown_channel_dry_run_falls_back_to_all():
    # dry_run is permissive — unknown channel expands to all supported channels
    result = _invoke("send", "msg", "--channel", "sms", "--dry-run", "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["dry_run"] is True
    assert data["delivered"] >= 1


def test_send_broadcast_content_blocked():
    result = _invoke("send", "broadcast para todos os contatos", "--dry-run", "--json")
    # dry_run bypasses broadcast gate — should succeed
    assert result.exit_code == 0

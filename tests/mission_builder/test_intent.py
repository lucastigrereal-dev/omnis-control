"""Tests for intent detection — deterministic, no LLM, no network."""
import pytest
from pathlib import Path
from src.mission_builder.intent import detect_intent, _normalize

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "intents.yaml"


def test_detects_carousel():
    intent, deliverable, _ = detect_intent("cria um carrossel sobre turismo em Natal")
    assert intent == "carousel"
    assert deliverable == "carousel_package"


def test_detects_carousel_with_accent_variant():
    intent, deliverable, _ = detect_intent("quero um carousel de fotos da praia")
    assert intent == "carousel"


def test_detects_campaign():
    intent, deliverable, _ = detect_intent("preciso de uma campanha de 10 posts para o hotel")
    assert intent == "campaign"
    assert deliverable == "campaign_package"


def test_detects_post():
    intent, deliverable, _ = detect_intent("faz um post simples para o feed")
    assert intent == "post"
    assert deliverable == "single_post_package"


def test_detects_reels():
    intent, deliverable, _ = detect_intent("cria um reel de 30 segundos mostrando o restaurante")
    assert intent == "reels"
    assert deliverable == "reels_package"


def test_detects_story():
    intent, deliverable, _ = detect_intent("preciso de stories para o Instagram")
    assert intent == "story"
    assert deliverable == "story_package"


def test_fallback_unknown():
    intent, deliverable, description = detect_intent("faça algo incrível sobre viagens")
    assert intent == "unknown"
    assert deliverable == "unknown"
    assert description == ""


def test_loads_intents_yaml():
    assert CONFIG_PATH.exists(), "config/intents.yaml deve existir"
    intent, _, _ = detect_intent("carrossel sobre culinária", config_path=CONFIG_PATH)
    assert intent == "carousel"


def test_normalize_strips_accents():
    assert _normalize("Carrossel") == "carrossel"
    assert _normalize("campanha") == "campanha"
    assert _normalize("histórias") == "historias"


def test_no_network_calls(monkeypatch):
    """detect_intent must never make network calls."""
    import socket
    original_connect = socket.socket.connect

    def _blocked_connect(*args, **kwargs):
        raise AssertionError("Network call detected — not allowed in detect_intent")

    monkeypatch.setattr(socket.socket, "connect", _blocked_connect)
    intent, _, _ = detect_intent("cria carrossel", config_path=CONFIG_PATH)
    assert intent == "carousel"


def test_no_env_reads(monkeypatch):
    """detect_intent must not read .env variables."""
    import os
    original_getenv = os.getenv

    def _assert_no_secret(key, *args, **kwargs):
        assert not key.startswith("META_") and not key.startswith("INSTAGRAM_"), (
            f"detect_intent should not read env var {key}"
        )
        return original_getenv(key, *args, **kwargs)

    monkeypatch.setattr(os, "getenv", _assert_no_secret)
    detect_intent("cria reel", config_path=CONFIG_PATH)

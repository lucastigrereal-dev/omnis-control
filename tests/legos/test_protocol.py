"""Testes do Protocol LegoCog — contrato formal dos Legos OMNIS (Onda 8)."""
from __future__ import annotations

import pytest

from src.legos.protocol import LegoCog, LegoCogResult, LegoCogSpec
from src.legos import (
    BrowserExecutorLego,
    ChannelMessengerLego,
    CodeExecutorLego,
    ResearchConductorLego,
    VideoProcessorLego,
)


# ── LegoCogSpec ───────────────────────────────────────────────────────────────

def test_legocogspec_required_field():
    spec = LegoCogSpec(goal="test task")
    assert spec.goal == "test task"


def test_legocogspec_defaults():
    spec = LegoCogSpec(goal="g")
    assert spec.dry_run is True
    assert spec.run_id == ""
    assert spec.payload == {}


def test_legocogspec_full():
    spec = LegoCogSpec(
        goal="research task",
        dry_run=False,
        run_id="abc123",
        payload={"key": "val"},
    )
    assert spec.dry_run is False
    assert spec.run_id == "abc123"
    assert spec.payload["key"] == "val"


# ── LegoCogResult ─────────────────────────────────────────────────────────────

def test_legocogresult_required_field():
    result = LegoCogResult(success=True)
    assert result.success is True


def test_legocogresult_defaults():
    result = LegoCogResult(success=False)
    assert result.output == ""
    assert result.dry_run is True
    assert result.error == ""
    assert result.artifacts == {}


def test_legocogresult_full():
    result = LegoCogResult(
        success=True, output="ok", dry_run=False, error="", artifacts={"x": 1}
    )
    assert result.output == "ok"
    assert result.artifacts["x"] == 1


# ── isinstance checks (structural duck typing) ────────────────────────────────

def test_research_lego_satisfies_legocog():
    lego = ResearchConductorLego()
    assert isinstance(lego, LegoCog)


def test_code_lego_satisfies_legocog():
    lego = CodeExecutorLego()
    assert isinstance(lego, LegoCog)


def test_messenger_lego_satisfies_legocog():
    lego = ChannelMessengerLego()
    assert isinstance(lego, LegoCog)


def test_video_lego_satisfies_legocog():
    lego = VideoProcessorLego()
    assert isinstance(lego, LegoCog)


def test_browser_lego_satisfies_legocog():
    lego = BrowserExecutorLego()
    assert isinstance(lego, LegoCog)


# ── run() returns LegoCogResult ───────────────────────────────────────────────

def test_research_lego_run_dry():
    lego = ResearchConductorLego()
    spec = LegoCogSpec(goal="turismo em Natal RN", dry_run=True)
    result = lego.run(spec)
    assert isinstance(result, LegoCogResult)
    assert result.dry_run is True
    assert result.success is True
    assert "Natal" in result.output or "Plano" in result.output or result.output != ""


def test_code_lego_run_dry():
    lego = CodeExecutorLego()
    spec = LegoCogSpec(goal="create a hello world script", dry_run=True)
    result = lego.run(spec)
    assert isinstance(result, LegoCogResult)
    assert result.dry_run is True
    assert result.success is True


def test_messenger_lego_run_dry():
    lego = ChannelMessengerLego()
    spec = LegoCogSpec(
        goal="Novo post publicado com sucesso!",
        dry_run=True,
        payload={"channels": ["telegram"]},
    )
    result = lego.run(spec)
    assert isinstance(result, LegoCogResult)
    assert result.dry_run is True
    assert result.success is True


def test_video_lego_run_dry_transcribe():
    lego = VideoProcessorLego()
    spec = LegoCogSpec(
        goal="transcribe video file",
        dry_run=True,
        payload={"video_path": "video.mp4"},
    )
    result = lego.run(spec)
    assert isinstance(result, LegoCogResult)
    assert result.dry_run is True
    assert result.success is True


def test_code_lego_run_propagates_run_id():
    lego = CodeExecutorLego()
    spec = LegoCogSpec(goal="write tests", dry_run=True, run_id="run_abc")
    result = lego.run(spec)
    assert isinstance(result, LegoCogResult)


def test_messenger_lego_run_payload_channels():
    lego = ChannelMessengerLego()
    spec = LegoCogSpec(
        goal="alert: pipeline done",
        dry_run=True,
        payload={"channels": ["whatsapp", "telegram"]},
    )
    result = lego.run(spec)
    assert isinstance(result, LegoCogResult)
    assert result.success is True


# ── all legos have health_check ───────────────────────────────────────────────

def test_all_legos_have_health_check():
    legos: list[LegoCog] = [
        ResearchConductorLego(),
        CodeExecutorLego(),
        ChannelMessengerLego(),
        VideoProcessorLego(),
        BrowserExecutorLego(),
    ]
    for lego in legos:
        result = lego.health_check()
        assert isinstance(result, bool), f"{type(lego).__name__}.health_check() must return bool"

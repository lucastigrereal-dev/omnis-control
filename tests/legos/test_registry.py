"""Testes do LegoRegistry — catálogo dos Legos externos OMNIS."""
from __future__ import annotations

import pytest

from src.legos.registry import LegoRegistry, default_registry, _KNOWN_LEGO_NAMES


# ── stub legos ────────────────────────────────────────────────────────────────

class _HealthyLego:
    def health_check(self) -> bool:
        return True


class _UnhealthyLego:
    def health_check(self) -> bool:
        return False


class _BrokenLego:
    def health_check(self) -> bool:
        raise RuntimeError("health check explodiu")


# ── register + get ────────────────────────────────────────────────────────────

def test_register_and_get_roundtrip():
    reg = LegoRegistry()
    lego = _HealthyLego()
    reg.register("browser_executor", lego)
    assert reg.get("browser_executor") is lego


def test_get_unknown_returns_none():
    reg = LegoRegistry()
    assert reg.get("nonexistent") is None


def test_contains_after_register():
    reg = LegoRegistry()
    reg.register("code_executor", _HealthyLego())
    assert "code_executor" in reg


def test_not_contains_before_register():
    reg = LegoRegistry()
    assert "code_executor" not in reg


def test_register_overwrites_previous():
    reg = LegoRegistry()
    first = _HealthyLego()
    second = _HealthyLego()
    reg.register("browser_executor", first)
    reg.register("browser_executor", second)
    assert reg.get("browser_executor") is second


def test_register_unknown_name_allowed():
    reg = LegoRegistry()
    reg.register("custom_lego", _HealthyLego())
    assert "custom_lego" in reg


# ── list_available ────────────────────────────────────────────────────────────

def test_list_available_empty():
    reg = LegoRegistry()
    assert reg.list_available() == []


def test_list_available_sorted():
    reg = LegoRegistry()
    reg.register("video_processor", _HealthyLego())
    reg.register("browser_executor", _HealthyLego())
    assert reg.list_available() == ["browser_executor", "video_processor"]


def test_len_empty():
    reg = LegoRegistry()
    assert len(reg) == 0


def test_len_after_registrations():
    reg = LegoRegistry()
    reg.register("code_executor", _HealthyLego())
    reg.register("video_processor", _HealthyLego())
    assert len(reg) == 2


# ── health_check_all ──────────────────────────────────────────────────────────

def test_health_check_all_empty():
    assert LegoRegistry().health_check_all() == {}


def test_health_check_all_all_healthy():
    reg = LegoRegistry()
    reg.register("browser_executor", _HealthyLego())
    reg.register("code_executor", _HealthyLego())
    result = reg.health_check_all()
    assert result == {"browser_executor": True, "code_executor": True}


def test_health_check_all_unhealthy_returns_false():
    reg = LegoRegistry()
    reg.register("channel_messenger", _UnhealthyLego())
    assert reg.health_check_all()["channel_messenger"] is False


def test_health_check_all_partial_failure():
    reg = LegoRegistry()
    reg.register("browser_executor", _HealthyLego())
    reg.register("channel_messenger", _UnhealthyLego())
    result = reg.health_check_all()
    assert result["browser_executor"] is True
    assert result["channel_messenger"] is False


def test_health_check_all_exception_becomes_false():
    reg = LegoRegistry()
    reg.register("broken", _BrokenLego())
    result = reg.health_check_all()
    assert result["broken"] is False


def test_health_check_all_exception_does_not_abort_others():
    reg = LegoRegistry()
    reg.register("broken", _BrokenLego())
    reg.register("healthy", _HealthyLego())
    result = reg.health_check_all()
    assert result["broken"] is False
    assert result["healthy"] is True


def test_health_check_all_keys_match_registered():
    reg = LegoRegistry()
    reg.register("a", _HealthyLego())
    reg.register("b", _UnhealthyLego())
    assert set(reg.health_check_all().keys()) == {"a", "b"}


# ── known lego names ──────────────────────────────────────────────────────────

def test_known_lego_names_has_all_5():
    assert "browser_executor" in _KNOWN_LEGO_NAMES
    assert "code_executor" in _KNOWN_LEGO_NAMES
    assert "video_processor" in _KNOWN_LEGO_NAMES
    assert "research_conductor" in _KNOWN_LEGO_NAMES
    assert "channel_messenger" in _KNOWN_LEGO_NAMES


# ── default_registry ──────────────────────────────────────────────────────────

def test_default_registry_has_all_5_legos():
    reg = default_registry()
    assert len(reg) == 5
    for name in _KNOWN_LEGO_NAMES:
        assert name in reg, f"Missing: {name}"


def test_default_registry_list_available_has_all():
    reg = default_registry()
    available = reg.list_available()
    assert len(available) == 5
    for name in _KNOWN_LEGO_NAMES:
        assert name in available


def test_default_registry_health_check_returns_dict_of_5():
    reg = default_registry()
    result = reg.health_check_all()
    assert isinstance(result, dict)
    assert len(result) == 5


def test_default_registry_all_values_are_bool():
    reg = default_registry()
    for name, val in reg.health_check_all().items():
        assert isinstance(val, bool), f"{name} health_check returned non-bool"


def test_default_registry_get_returns_lego_instances():
    reg = default_registry()
    for name in _KNOWN_LEGO_NAMES:
        lego = reg.get(name)
        assert lego is not None
        assert hasattr(lego, "health_check")

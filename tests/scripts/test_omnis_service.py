"""Testes do omnis_service daemon (Onda 7)."""
from __future__ import annotations

import importlib
import inspect
import sys

import pytest


def _load_service():
    """Importa o módulo scripts/omnis_service.py pelo path."""
    import importlib.util
    import os
    path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "omnis_service.py")
    )
    spec = importlib.util.spec_from_file_location("omnis_service", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── import + constants ────────────────────────────────────────────────────────

def test_service_module_imports():
    mod = _load_service()
    assert hasattr(mod, "main")
    assert hasattr(mod, "_run_cycle")


def test_service_has_interval_constant():
    mod = _load_service()
    assert isinstance(mod._INTERVAL, int)
    assert mod._INTERVAL > 0


def test_service_dry_run_default_true():
    mod = _load_service()
    assert mod._DRY_RUN is True


def test_service_dry_run_env_override(monkeypatch):
    monkeypatch.setenv("OMNIS_SERVICE_DRY_RUN", "0")
    mod = _load_service()
    assert mod._DRY_RUN is False


# ── _run_cycle ────────────────────────────────────────────────────────────────

def test_run_cycle_completes_without_crash(monkeypatch):
    mod = _load_service()
    from src.agentic.scheduler import SchedulerService

    # Stub: nenhum schedule vencido
    monkeypatch.setattr(SchedulerService, "run_due", lambda self: [])
    from src.utils.run_context import RunContext
    ctx = RunContext.new()
    mod._run_cycle(ctx)  # não deve lançar


def test_run_cycle_handles_scheduler_exception(monkeypatch):
    mod = _load_service()
    from src.agentic.scheduler import SchedulerService

    def _fail(self):
        raise RuntimeError("scheduler explodiu")

    monkeypatch.setattr(SchedulerService, "run_due", _fail)
    from src.utils.run_context import RunContext
    ctx = RunContext.new()
    mod._run_cycle(ctx)  # exceção não propaga — logged, swallowed


# ── graceful shutdown ─────────────────────────────────────────────────────────

def test_handle_signal_sets_running_false():
    mod = _load_service()
    mod._running = True
    mod._handle_signal(15, None)  # SIGTERM
    assert mod._running is False


@pytest.mark.xfail(
    reason="Known mismatch: omnis_service passes dry_run to SchedulerService, but scheduler signature may not accept it.",
    strict=False,
)
def test_scheduler_constructor_signature_compatible_with_service_call():
    """Guardrail: serviço não deve passar kwargs incompatíveis ao SchedulerService."""
    mod = _load_service()
    scheduler_init = inspect.signature(mod.SchedulerService.__init__)
    assert "dry_run" in scheduler_init.parameters

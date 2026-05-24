"""Testes do BrowserExecutorLego — OMNIS Lego Web."""
from __future__ import annotations

import sys
import types
import threading

import pytest

from src.interfaces.browser_executor import BrowserTask, BrowserResult
from src.legos.browser_executor_lego import (
    BrowserExecutorLego,
    _is_critical,
    _BROWSER_SEMAPHORE,
)


# ── _is_critical ──────────────────────────────────────────────────────────────

def test_is_critical_detects_login():
    assert _is_critical("fazer login na conta") is True

def test_is_critical_detects_buy():
    assert _is_critical("comprar pacote premium") is True

def test_is_critical_detects_send():
    assert _is_critical("enviar mensagem ao cliente") is True

def test_is_critical_safe_goal():
    assert _is_critical("extrair título da página") is False

def test_is_critical_case_insensitive():
    assert _is_critical("DELETAR conta") is True


# ── approval gate (sem browser) ───────────────────────────────────────────────

def test_real_critical_goal_blocked_without_approval():
    lego = BrowserExecutorLego()
    task = BrowserTask(url="https://example.com", goal="fazer login na conta", dry_run=False)
    result = lego.execute(task)
    assert result.success is False
    assert result.error == "approval_required"
    assert result.artifacts.get("approval_required") is True


def test_dry_run_critical_goal_not_blocked():
    """dry_run=True ignora o approval gate — intencionalmente seguro."""
    lego = BrowserExecutorLego()
    task = BrowserTask(url="https://example.com", goal="login test", dry_run=True, timeout_seconds=15)
    # Não precisamos rodar o browser — só confirmamos que não bloqueia na gate
    # (pode falhar por outros motivos, mas não por approval_required)
    result = lego.execute(task)
    assert result.error != "approval_required"


# ── health_check ─────────────────────────────────────────────────────────────

def test_health_check_returns_bool():
    lego = BrowserExecutorLego()
    result = lego.health_check()
    assert isinstance(result, bool)


def test_health_check_true_when_playwright_available():
    lego = BrowserExecutorLego()
    assert lego.health_check() is True


def test_health_check_false_when_playwright_unavailable(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def _block_playwright(name, *args, **kwargs):
        if name.startswith("playwright"):
            raise ImportError("playwright missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_playwright)
    lego = BrowserExecutorLego()
    assert lego.health_check() is False


# ── real extraction (dry_run=True, página estática via data: URL) ─────────────

def test_execute_extracts_title_from_static_page():
    """Tarefa web real simples: carrega página HTML estática e extrai conteúdo."""
    lego = BrowserExecutorLego()
    html = "<html><head><title>OMNIS Test</title></head><body><h1>Motor OK</h1></body></html>"
    task = BrowserTask(
        url=f"data:text/html,{html}",
        goal="extrair título da página",
        dry_run=True,
        timeout_seconds=15,
    )
    result = lego.execute(task)
    assert result.success is True
    assert "Motor OK" in result.output
    assert result.artifacts.get("title") == "OMNIS Test"
    assert result.dry_run is True


def test_execute_returns_browser_result_type():
    lego = BrowserExecutorLego()
    task = BrowserTask(
        url="data:text/html,<html><body>ok</body></html>",
        goal="verificar conteúdo",
        dry_run=True,
        timeout_seconds=10,
    )
    result = lego.execute(task)
    assert isinstance(result, BrowserResult)


def test_execute_artifacts_has_char_count():
    lego = BrowserExecutorLego()
    task = BrowserTask(
        url="data:text/html,<html><body>hello world</body></html>",
        goal="extrair texto",
        dry_run=True,
        timeout_seconds=10,
    )
    result = lego.execute(task)
    assert result.success is True
    assert "char_count" in result.artifacts
    assert result.artifacts["char_count"] > 0


# ── Protocol compliance ───────────────────────────────────────────────────────

def test_lego_satisfies_browser_executor_protocol():
    from src.interfaces.browser_executor import BrowserExecutor
    lego: BrowserExecutor = BrowserExecutorLego()
    assert hasattr(lego, "execute")
    assert hasattr(lego, "health_check")


# ── Semáforo RAM — 1 browser at a time ───────────────────────────────────────

def test_semaphore_timeout_when_held():
    """Se o semáforo estiver ocupado, execute() retorna erro de timeout."""
    lego = BrowserExecutorLego()
    task = BrowserTask(
        url="data:text/html,<html><body>x</body></html>",
        goal="extrair",
        dry_run=True,
        timeout_seconds=1,  # timeout curto
    )
    acquired = _BROWSER_SEMAPHORE.acquire(blocking=False)
    assert acquired, "semaphore should be free before test"
    try:
        result = lego.execute(task)
        assert result.success is False
        assert "semaphore_timeout" in (result.error or "")
    finally:
        _BROWSER_SEMAPHORE.release()


def test_execute_returns_sandbox_blocked_when_url_invalid(monkeypatch):
    lego = BrowserExecutorLego()

    def _raise_invalid(_url: str):
        raise ValueError("invalid_url")

    monkeypatch.setattr(lego._sandbox, "validate_url", _raise_invalid)
    task = BrowserTask(url="javascript:alert(1)", goal="extrair", dry_run=True)

    result = lego.execute(task)
    assert result.success is False
    assert "sandbox_blocked" in (result.error or "")


def test_run_browser_timeout_branch(monkeypatch):
    lego = BrowserExecutorLego()
    task = BrowserTask(
        url="https://example.com",
        goal="extrair título",
        dry_run=True,
        timeout_seconds=1,
    )

    class FakePWTimeout(Exception):
        pass

    class _FakePage:
        def set_default_timeout(self, _ms: int):
            pass

        def goto(self, *_args, **_kwargs):
            raise FakePWTimeout("timeout")

    class _FakeBrowser:
        def new_page(self):
            return _FakePage()

        def close(self):
            pass

    class _FakeChromium:
        def launch(self, headless=True):
            return _FakeBrowser()

    class _FakePlayCtx:
        chromium = _FakeChromium()

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

    fake_sync_module = types.SimpleNamespace(
        sync_playwright=lambda: _FakePlayCtx(),
        TimeoutError=FakePWTimeout,
    )
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake_sync_module)
    monkeypatch.setitem(sys.modules, "playwright", types.SimpleNamespace(sync_api=fake_sync_module))

    result = lego._run_browser(task)
    assert result.success is False
    assert "timeout" in (result.error or "")


def test_run_browser_generic_exception_branch(monkeypatch):
    lego = BrowserExecutorLego()
    task = BrowserTask(
        url="https://example.com",
        goal="extrair título",
        dry_run=True,
        timeout_seconds=1,
    )

    class FakePWTimeout(Exception):
        pass

    class _FakePage:
        def set_default_timeout(self, _ms: int):
            pass

        def goto(self, *_args, **_kwargs):
            raise RuntimeError("boom")

    class _FakeBrowser:
        def new_page(self):
            return _FakePage()

        def close(self):
            pass

    class _FakeChromium:
        def launch(self, headless=True):
            return _FakeBrowser()

    class _FakePlayCtx:
        chromium = _FakeChromium()

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

    fake_sync_module = types.SimpleNamespace(
        sync_playwright=lambda: _FakePlayCtx(),
        TimeoutError=FakePWTimeout,
    )
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake_sync_module)
    monkeypatch.setitem(sys.modules, "playwright", types.SimpleNamespace(sync_api=fake_sync_module))

    result = lego._run_browser(task)
    assert result.success is False
    assert "boom" in (result.error or "")

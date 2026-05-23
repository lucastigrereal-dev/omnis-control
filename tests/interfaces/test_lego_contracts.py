"""Testes dos contratos de interface para Legos externos."""
from __future__ import annotations

import pytest
from src.interfaces.browser_executor import BrowserExecutor, BrowserTask, BrowserResult
from src.interfaces.code_executor import CodeExecutor, CodeSpec, CodeResult


# ── BrowserTask / BrowserResult ──────────────────────────────────────────────

def test_browser_task_defaults():
    t = BrowserTask(url="https://example.com", goal="extrair título")
    assert t.dry_run is True
    assert t.timeout_seconds == 30
    assert t.extra == {}


def test_browser_task_real_mode():
    t = BrowserTask(url="https://example.com", goal="clicar em reservar", dry_run=False)
    assert t.dry_run is False


def test_browser_result_success():
    r = BrowserResult(success=True, output="título: Hotel X", url_visited="https://example.com", dry_run=True)
    assert r.error is None
    assert r.artifacts == {}


def test_browser_result_failure():
    r = BrowserResult(success=False, output="", url_visited="", dry_run=False, error="timeout")
    assert r.success is False
    assert r.error == "timeout"


# ── CodeSpec / CodeResult ─────────────────────────────────────────────────────

def test_code_spec_defaults():
    s = CodeSpec(goal="criar relatório de vendas")
    assert s.language == "python"
    assert s.dry_run is True
    assert s.context_files == []
    assert s.output_dir == "output/"


def test_code_spec_custom():
    s = CodeSpec(goal="gerar testes", language="typescript", dry_run=False, output_dir="/tmp/out")
    assert s.language == "typescript"
    assert s.dry_run is False


def test_code_result_success():
    r = CodeResult(success=True, output="ok", files_created=["report.py"], tests_passed=True, dry_run=True)
    assert r.error is None
    assert r.artifacts == {}


def test_code_result_failure():
    r = CodeResult(success=False, output="", files_created=[], tests_passed=False, dry_run=False, error="compile error")
    assert r.success is False
    assert r.error == "compile error"


# ── Protocol compliance (structural subtyping) ────────────────────────────────

def test_browser_executor_protocol_is_satisfied_by_mock():
    class MockBrowser:
        def execute(self, task: BrowserTask) -> BrowserResult:
            return BrowserResult(success=True, output="mock", url_visited=task.url, dry_run=task.dry_run)

        def health_check(self) -> bool:
            return True

    executor: BrowserExecutor = MockBrowser()
    result = executor.execute(BrowserTask(url="https://x.com", goal="test"))
    assert result.success is True
    assert executor.health_check() is True


def test_code_executor_protocol_is_satisfied_by_mock():
    class MockCode:
        def execute(self, spec: CodeSpec) -> CodeResult:
            return CodeResult(success=True, output="mock", files_created=["f.py"], tests_passed=True, dry_run=spec.dry_run)

        def health_check(self) -> bool:
            return True

    executor: CodeExecutor = MockCode()
    result = executor.execute(CodeSpec(goal="test"))
    assert result.success is True
    assert executor.health_check() is True

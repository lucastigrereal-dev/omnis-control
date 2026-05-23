"""Testes do CodeExecutorLego — OMNIS Lego de Código."""
from __future__ import annotations

import pytest

from src.interfaces.code_executor import CodeSpec, CodeResult
from src.legos.code_executor_lego import CodeExecutorLego, _requires_deploy_approval


# ── _requires_deploy_approval ─────────────────────────────────────────────────

def test_deploy_keyword_detected():
    assert _requires_deploy_approval("fazer deploy da aplicação") is True

def test_publish_keyword_detected():
    assert _requires_deploy_approval("publicar no GitHub") is True

def test_safe_goal_not_flagged():
    assert _requires_deploy_approval("criar script de relatório") is False

def test_upload_keyword_detected():
    assert _requires_deploy_approval("upload para servidor") is True


# ── approval gate ─────────────────────────────────────────────────────────────

def test_real_deploy_goal_blocked():
    lego = CodeExecutorLego()
    spec = CodeSpec(goal="fazer deploy da API", dry_run=False)
    result = lego.execute(spec)
    assert result.success is False
    assert result.error == "approval_required"
    assert result.artifacts.get("approval_required") is True


def test_dry_run_deploy_goal_not_blocked():
    lego = CodeExecutorLego()
    spec = CodeSpec(goal="deploy plan", dry_run=True)
    result = lego.execute(spec)
    # dry_run ignora approval gate — retorna plano
    assert result.error != "approval_required"
    assert result.success is True


# ── dry_run plan ─────────────────────────────────────────────────────────────

def test_dry_run_returns_plan():
    lego = CodeExecutorLego()
    spec = CodeSpec(goal="criar relatório de vendas", language="python", dry_run=True)
    result = lego.execute(spec)
    assert result.success is True
    assert result.dry_run is True
    assert "python" in result.output.lower() or "Plano" in result.output
    assert result.files_created == []


def test_dry_run_tests_passed_true():
    lego = CodeExecutorLego()
    result = lego.execute(CodeSpec(goal="gerar testes", dry_run=True))
    assert result.tests_passed is True


def test_dry_run_artifacts_has_mode():
    lego = CodeExecutorLego()
    result = lego.execute(CodeSpec(goal="analisar código", dry_run=True))
    assert result.artifacts.get("mode") == "dry_run_plan"


# ── health_check ─────────────────────────────────────────────────────────────

def test_health_check_returns_bool():
    lego = CodeExecutorLego()
    assert isinstance(lego.health_check(), bool)


def test_health_check_false_when_openhands_unreachable(monkeypatch):
    import urllib.error
    def _fail(*_a, **_kw):
        raise urllib.error.URLError("refused")
    monkeypatch.setattr("urllib.request.urlopen", _fail)
    lego = CodeExecutorLego()
    assert lego.health_check() is False


# ── local_sandbox (dry_run=False, OpenHands offline) ─────────────────────────

def test_local_sandbox_runs_python(monkeypatch):
    monkeypatch.setattr("src.legos.code_executor_lego.CodeExecutorLego.health_check", lambda _: False)
    lego = CodeExecutorLego()
    spec = CodeSpec(goal="gerar script", language="python", dry_run=False, output_dir="/tmp/out")
    result = lego.execute(spec)
    assert result.success is True
    assert "sandbox" in result.output.lower() or "goal" in result.output.lower()
    assert result.artifacts.get("mode") == "local_sandbox"


def test_local_sandbox_rejects_non_python(monkeypatch):
    monkeypatch.setattr("src.legos.code_executor_lego.CodeExecutorLego.health_check", lambda _: False)
    lego = CodeExecutorLego()
    spec = CodeSpec(goal="gerar componente", language="typescript", dry_run=False)
    result = lego.execute(spec)
    assert result.success is False
    assert "local_sandbox" in (result.error or "")


# ── Protocol compliance ───────────────────────────────────────────────────────

def test_lego_satisfies_code_executor_protocol():
    from src.interfaces.code_executor import CodeExecutor
    lego: CodeExecutor = CodeExecutorLego()
    assert hasattr(lego, "execute")
    assert hasattr(lego, "health_check")

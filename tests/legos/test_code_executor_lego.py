"""Testes do CodeExecutorLego — OMNIS Lego de Código."""
from __future__ import annotations

import subprocess

import pytest

from src.interfaces.code_executor import CodeSpec, CodeResult
from src.legos.code_executor_lego import (
    CodeExecutorLego,
    _has_unsafe_goal_payload,
    _requires_deploy_approval,
)


# ── _requires_deploy_approval ─────────────────────────────────────────────────

def test_deploy_keyword_detected():
    assert _requires_deploy_approval("fazer deploy da aplicação") is True

def test_publish_keyword_detected():
    assert _requires_deploy_approval("publicar no GitHub") is True

def test_safe_goal_not_flagged():
    assert _requires_deploy_approval("criar script de relatório") is False

def test_upload_keyword_detected():
    assert _requires_deploy_approval("upload para servidor") is True


def test_unsafe_goal_payload_detects_newline():
    assert _has_unsafe_goal_payload("relatorio\nimport os") is True


def test_unsafe_goal_payload_detects_semicolon():
    assert _has_unsafe_goal_payload("relatorio; import os") is True


def test_unsafe_goal_payload_allows_simple_goal():
    assert _has_unsafe_goal_payload("criar relatório de vendas") is False


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


def test_execute_delegates_to_openhands_when_healthy(monkeypatch):
    lego = CodeExecutorLego()
    sentinel = CodeResult(
        success=True,
        output="from service",
        files_created=["out.py"],
        tests_passed=True,
        dry_run=False,
    )
    monkeypatch.setattr(lego, "health_check", lambda: True)
    monkeypatch.setattr(lego, "_call_openhands_service", lambda _spec: sentinel)

    result = lego.execute(CodeSpec(goal="gerar código", language="python", dry_run=False))
    assert result is sentinel


def test_call_openhands_service_handles_exception(monkeypatch):
    import urllib.error

    def _raise(*_args, **_kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr("urllib.request.urlopen", _raise)
    lego = CodeExecutorLego()
    result = lego._call_openhands_service(CodeSpec(goal="x", dry_run=False))
    assert result.success is False
    assert result.tests_passed is False
    assert result.error


def test_local_sandbox_timeout_branch(monkeypatch):
    monkeypatch.setattr("src.legos.code_executor_lego.CodeExecutorLego.health_check", lambda _: False)

    def _timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="python -c", timeout=30)

    monkeypatch.setattr("subprocess.run", _timeout)
    lego = CodeExecutorLego()
    result = lego.execute(CodeSpec(goal="gerar script", language="python", dry_run=False))
    assert result.success is False
    assert result.error == "local_sandbox: timeout"


def test_local_sandbox_blocks_unsafe_payload_before_subprocess(monkeypatch):
    monkeypatch.setattr("src.legos.code_executor_lego.CodeExecutorLego.health_check", lambda _: False)

    def _should_not_run(*_args, **_kwargs):
        raise AssertionError("subprocess.run should not be called for unsafe payload")

    monkeypatch.setattr("subprocess.run", _should_not_run)
    lego = CodeExecutorLego()
    result = lego.execute(
        CodeSpec(goal="gerar script\nimport os", language="python", dry_run=False)
    )
    assert result.success is False
    assert result.error == "local_sandbox: unsafe_goal_payload"
    assert result.artifacts.get("blocked") is True


# ── RCE hardening: injection unhappy paths ───────────────────────────────────
# Todos devem ser bloqueados — goal nunca é interpolado no código (argv approach)

def test_newline_injection_blocked(monkeypatch):
    """\\n no goal tentaria injetar código via quebra de linha no f-string."""
    monkeypatch.setattr("src.legos.code_executor_lego.CodeExecutorLego.health_check", lambda _: False)
    lego = CodeExecutorLego()
    result = lego.execute(CodeSpec(
        goal="gerar script\nimport os; os.system('echo INJECTED')",
        language="python", dry_run=False,
    ))
    assert result.success is False
    assert result.error == "local_sandbox: unsafe_goal_payload"


def test_semicolon_rm_injection_blocked(monkeypatch):
    """Ponto-e-vírgula + comando destrutivo deve ser bloqueado."""
    monkeypatch.setattr("src.legos.code_executor_lego.CodeExecutorLego.health_check", lambda _: False)
    lego = CodeExecutorLego()
    result = lego.execute(CodeSpec(
        goal="script; rm -rf /tmp/sensitive",
        language="python", dry_run=False,
    ))
    assert result.success is False
    assert result.error == "local_sandbox: unsafe_goal_payload"


def test_dollar_paren_injection_blocked(monkeypatch):
    """$(cmd) shell expansion deve ser bloqueado."""
    monkeypatch.setattr("src.legos.code_executor_lego.CodeExecutorLego.health_check", lambda _: False)
    lego = CodeExecutorLego()
    result = lego.execute(CodeSpec(
        goal="script $(cat /etc/passwd)",
        language="python", dry_run=False,
    ))
    assert result.success is False
    assert result.error == "local_sandbox: unsafe_goal_payload"


def test_backtick_injection_blocked(monkeypatch):
    """Backtick command substitution deve ser bloqueado."""
    monkeypatch.setattr("src.legos.code_executor_lego.CodeExecutorLego.health_check", lambda _: False)
    lego = CodeExecutorLego()
    result = lego.execute(CodeSpec(
        goal="script `evil_command`",
        language="python", dry_run=False,
    ))
    assert result.success is False
    assert result.error == "local_sandbox: unsafe_goal_payload"


def test_clean_goal_runs_after_hardening(monkeypatch):
    """Goal limpo ainda executa normalmente após as correções de segurança."""
    monkeypatch.setattr("src.legos.code_executor_lego.CodeExecutorLego.health_check", lambda _: False)
    lego = CodeExecutorLego()
    result = lego.execute(CodeSpec(
        goal="gerar relatório de vendas do trimestre",
        language="python", dry_run=False, output_dir="/tmp/out",
    ))
    assert result.success is True
    assert result.artifacts.get("mode") == "local_sandbox"


# ── Protocol compliance ───────────────────────────────────────────────────────

def test_lego_satisfies_code_executor_protocol():
    from src.interfaces.code_executor import CodeExecutor
    lego: CodeExecutor = CodeExecutorLego()
    assert hasattr(lego, "execute")
    assert hasattr(lego, "health_check")

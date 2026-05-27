"""Tests for AuroraGuardrail integration in the mission graph execute_node.

Wave 8 — D1-W8: Toda ação que passa pelo execute_node é verificada pelo guardrail.
Ações perigosas (publicar, deploy, push) são bloqueadas.
Ações normais (execute_step) passam normalmente.
Guardrail down → grafo continua (graceful degradation).
"""
from __future__ import annotations

import pytest

from src.mission_graph.runner import run_mission_graph
from src.mission_graph.mission_state import initial_state
from src.mission_graph.nodes.execute_node import execute_node


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(action: str = "execute_step", error: str | None = None) -> dict:
    """Create a minimal state dict for execute_node unit tests."""
    state = initial_state("test-guardrail", action=action)
    if error:
        state["error"] = error
    return state


# ---------------------------------------------------------------------------
# Unit tests — execute_node direto
# ---------------------------------------------------------------------------

class TestExecuteNodeGuardrail:
    """Testa o guardrail diretamente em execute_node (sem LangGraph)."""

    def test_acao_normal_passa(self):
        """execute_step não é bloqueado pelo guardrail → current_step incrementa."""
        state = _make_state(action="execute_step")
        result = execute_node(state)
        # Guardrail não bloqueia → prossegue normalmente
        assert result.get("status") != "failed" or result.get("error") is None
        # current_step incrementado ou nenhum bloqueio
        assert "Guardrail" not in (result.get("error") or "")

    def test_acao_publicar_bloqueada(self):
        """'publicar' é bloqueado pelo guardrail (regra external_publish) → status=failed."""
        state = _make_state(action="publicar")
        result = execute_node(state)
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Guardrail bloqueou" in result["error"]
        assert "publicar" in result["error"]

    def test_acao_deploy_bloqueada(self):
        """'deploy' é bloqueado pelo guardrail (regra git_push_deploy) → status=failed."""
        state = _make_state(action="deploy")
        result = execute_node(state)
        assert result["status"] == "failed"
        assert "Guardrail bloqueou" in result["error"]
        assert "deploy" in result["error"]

    def test_acao_git_push_bloqueada(self):
        """'git push' é bloqueado pelo guardrail → status=failed."""
        state = _make_state(action="git push")
        result = execute_node(state)
        assert result["status"] == "failed"
        assert "Guardrail bloqueou" in result["error"]

    def test_acao_deletar_nao_bloqueada(self):
        """'deletar' não tem regra específica no guardrail → passa normalmente."""
        state = _make_state(action="deletar")
        result = execute_node(state)
        # 'deletar' puro não é capturado por nenhuma regra → ALLOWED
        # current_step incrementado, sem bloqueio de guardrail
        assert "Guardrail bloqueou" not in (result.get("error") or "")

    def test_guardrail_down_nao_quebra_execute(self, monkeypatch):
        """Se AuroraGuardrail lançar exceção, execute_node continua normalmente."""
        import src.aurora.guardrail as g_module

        class BrokenGuardrail:
            def check(self, action):
                raise RuntimeError("guardrail offline")

        monkeypatch.setattr(g_module, "AuroraGuardrail", BrokenGuardrail)
        state = _make_state(action="execute_step")
        result = execute_node(state)
        # Graceful: sem crash, continua normalmente
        assert result.get("status") != "failed"
        assert result.get("current_step", 0) >= 1

    def test_action_default_execute_step(self):
        """State sem campo 'action' usa default 'execute_step' (não bloqueado)."""
        state = initial_state("test-default-action")
        # Remove o campo action para simular estado legado
        state.pop("action", None)
        result = execute_node(state)
        # Deve executar normalmente sem bloqueio
        assert "Guardrail bloqueou" not in (result.get("error") or "")


# ---------------------------------------------------------------------------
# Integration tests — via run_mission_graph (LangGraph completo)
# ---------------------------------------------------------------------------

class TestGuardrailNoGrafo:
    """Testa o guardrail via run_mission_graph (LangGraph completo)."""

    def test_acao_normal_passa(self, monkeypatch, tmp_path):
        """execute_step não é bloqueado pelo guardrail → fluxo completa normalmente."""
        monkeypatch.chdir(tmp_path)
        result = run_mission_graph("g_normal", use_langgraph=True, action="execute_step")
        # Guardrail não bloqueia → fluxo normal
        assert result["status"] in ("completed", "failed")
        assert "Guardrail" not in (result.get("error") or "")

    def test_acao_publicar_bloqueada(self, monkeypatch, tmp_path):
        """Ação 'publicar' deve ser bloqueada pelo guardrail → status=failed."""
        monkeypatch.chdir(tmp_path)
        result = run_mission_graph("g_publicar", use_langgraph=True, action="publicar")
        # Guardrail bloqueia publicar → status failed com mensagem de guardrail
        assert result["status"] == "failed"
        assert result.get("error") is not None
        assert "Guardrail bloqueou" in result["error"]

    def test_acao_deploy_bloqueada(self, monkeypatch, tmp_path):
        """Ação 'deploy' deve ser bloqueada pelo guardrail → status=failed."""
        monkeypatch.chdir(tmp_path)
        result = run_mission_graph("g_deploy", use_langgraph=True, action="deploy")
        assert result["status"] == "failed"
        assert result.get("error") is not None
        assert "Guardrail bloqueou" in result["error"]

    def test_acao_deletar_nao_bloqueada(self, monkeypatch, tmp_path):
        """'deletar' não tem regra no guardrail → grafo completa sem bloqueio."""
        monkeypatch.chdir(tmp_path)
        result = run_mission_graph("g_deletar", use_langgraph=True, action="deletar")
        # Verifica que fluxo não crashou e sem mensagem de guardrail
        assert result["status"] in ("completed", "failed")
        assert "Guardrail bloqueou" not in (result.get("error") or "")

    def test_guardrail_down_nao_quebra_grafo(self, monkeypatch, tmp_path):
        """Se AuroraGuardrail lançar exceção, grafo continua normalmente."""
        monkeypatch.chdir(tmp_path)
        import src.aurora.guardrail as g_module

        class BrokenGuardrail:
            def check(self, action):
                raise RuntimeError("guardrail offline")

        monkeypatch.setattr(g_module, "AuroraGuardrail", BrokenGuardrail)
        result = run_mission_graph("g_down", use_langgraph=True)
        assert result["status"] in ("completed", "failed")

    def test_action_default_quando_nao_especificado(self, monkeypatch, tmp_path):
        """run_mission_graph sem action usa 'execute_step' → não bloqueado."""
        monkeypatch.chdir(tmp_path)
        result = run_mission_graph("g_default_action", use_langgraph=True)
        assert result["status"] in ("completed", "failed")
        assert "Guardrail" not in (result.get("error") or "")


# ---------------------------------------------------------------------------
# Tests — initial_state com campo action
# ---------------------------------------------------------------------------

class TestInitialStateAction:
    """Verifica que initial_state() inclui o campo action corretamente."""

    def test_initial_state_action_default(self):
        """initial_state() inclui action='execute_step' por padrão."""
        state = initial_state("m1")
        assert state["action"] == "execute_step"

    def test_initial_state_action_custom(self):
        """initial_state() aceita action customizado."""
        state = initial_state("m2", action="publicar")
        assert state["action"] == "publicar"

    def test_initial_state_action_round_trip(self):
        """action persiste corretamente no estado."""
        for action in ("execute_step", "publicar", "deploy", "deletar", "git push"):
            state = initial_state(f"m_{action}", action=action)
            assert state["action"] == action

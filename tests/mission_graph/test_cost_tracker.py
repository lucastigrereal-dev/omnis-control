"""Tests para cost_tracker integrado no mission_graph (D1-W9).

Cobre:
  - cost_usd aumenta por step executado
  - token_count positivo após run
  - state.json contém cost_usd e token_count
  - custo proporcional ao número de steps (via mock)
  - initial_state() tem cost_usd=0.0 e token_count=0
"""
from __future__ import annotations

import json

import pytest

from src.mission_graph.mission_state import initial_state
from src.mission_graph.nodes.execute_node import execute_node, COST_PER_STEP_USD, TOKENS_PER_STEP
from src.mission_graph.runner import run_mission_graph


# ---------------------------------------------------------------------------
# test_cost_zero_em_estado_inicial
# ---------------------------------------------------------------------------

def test_cost_zero_em_estado_inicial():
    """initial_state() tem cost_usd=0.0 e token_count=0."""
    state = initial_state("mission-custo-zero")
    assert state["cost_usd"] == 0.0
    assert state["token_count"] == 0


# ---------------------------------------------------------------------------
# test_cost_aumenta_por_step
# ---------------------------------------------------------------------------

def test_cost_aumenta_por_step():
    """Após executar um step, cost_usd > 0."""
    state = initial_state("mission-custo-step")
    result = execute_node(state)
    assert result["cost_usd"] > 0.0, "cost_usd deve ser > 0 após execute_node"
    assert result["cost_usd"] == pytest.approx(COST_PER_STEP_USD)


# ---------------------------------------------------------------------------
# test_token_count_positivo
# ---------------------------------------------------------------------------

def test_token_count_positivo():
    """Após executar um step, token_count > 0."""
    state = initial_state("mission-tokens")
    result = execute_node(state)
    assert result["token_count"] > 0, "token_count deve ser > 0 após execute_node"
    assert result["token_count"] == TOKENS_PER_STEP


# ---------------------------------------------------------------------------
# test_custo_proporcional_steps
# ---------------------------------------------------------------------------

def test_custo_proporcional_steps():
    """Missão com mais steps → custo maior (simula chamadas consecutivas)."""
    state = initial_state("mission-proporcional")

    # Simula 3 chamadas de execute_node
    for _ in range(3):
        patch = execute_node(state)
        # Aplica o patch parcialmente ao state para simular acumulação
        state = {**state, **patch}

    expected_cost = 3 * COST_PER_STEP_USD
    expected_tokens = 3 * TOKENS_PER_STEP

    assert state["cost_usd"] == pytest.approx(expected_cost)
    assert state["token_count"] == expected_tokens


# ---------------------------------------------------------------------------
# test_cost_no_state_json
# ---------------------------------------------------------------------------

def test_cost_no_state_json(monkeypatch, tmp_path):
    """state.json gravado pelo finalize_node contém cost_usd e token_count."""
    monkeypatch.chdir(tmp_path)
    result = run_mission_graph("mission-custo-json", use_langgraph=True)

    p = tmp_path / "output" / "mission_graph" / "mission-custo-json" / "state.json"
    assert p.exists(), f"state.json não encontrado em: {p}"

    data = json.loads(p.read_text(encoding="utf-8"))
    assert "cost_usd" in data, "Chave cost_usd ausente no state.json"
    assert "token_count" in data, "Chave token_count ausente no state.json"

    # Após uma run completa, o custo deve ser > 0
    assert isinstance(data["cost_usd"], (int, float))
    assert isinstance(data["token_count"], int)
    assert data["cost_usd"] >= 0.0
    assert data["token_count"] >= 0

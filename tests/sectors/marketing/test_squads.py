"""Testes para multi-agent squads — Wave 16."""
from __future__ import annotations

import pytest

from src.sectors.marketing.squads.squad_instagram import SQUAD_INSTAGRAM_CONFIG
from src.sectors.marketing.squads.squad_comercial import SQUAD_COMERCIAL_CONFIG
from src.sectors.marketing.squads.squad_growth import SQUAD_GROWTH_CONFIG
from src.mission_graph.nodes.squad_orchestrator import run_squad
from src.sectors.marketing.agents.content_agent import ContentAgent


# --- Config tests ---

def test_squad_instagram_tem_config():
    assert "name" in SQUAD_INSTAGRAM_CONFIG
    assert "parallel" in SQUAD_INSTAGRAM_CONFIG
    assert SQUAD_INSTAGRAM_CONFIG["name"] == "Squad Instagram"


def test_squad_comercial_tem_config():
    assert "sequential" in SQUAD_COMERCIAL_CONFIG
    assert len(SQUAD_COMERCIAL_CONFIG["sequential"]) >= 1


def test_squad_growth_tem_config():
    assert "parallel" in SQUAD_GROWTH_CONFIG
    assert len(SQUAD_GROWTH_CONFIG["parallel"]) == 2


# --- Execution tests ---

def test_run_squad_instagram():
    result = run_squad(
        SQUAD_INSTAGRAM_CONFIG,
        {"goal": "criar post", "squad": "instagram"},
    )
    assert "agent_count" in result
    assert result["agent_count"] >= 1


def test_run_squad_comercial():
    result = run_squad(
        SQUAD_COMERCIAL_CONFIG,
        {"goal": "qualificar lead hotel", "squad": "comercial"},
    )
    assert result.get("total_cost_usd", -1) >= 0


def test_run_squad_paralelo_growth():
    result = run_squad(
        SQUAD_GROWTH_CONFIG,
        {"goal": "crescimento orgânico", "squad": "growth"},
    )
    assert len(result["parallel_results"]) == 2


def test_squad_custo_total():
    result = run_squad(
        SQUAD_GROWTH_CONFIG,
        {"goal": "campanha crescimento", "squad": "growth"},
    )
    expected = sum(r.get("cost_usd", 0.0) for r in result["parallel_results"] + result["sequential_results"])
    assert abs(result["total_cost_usd"] - expected) < 1e-9


def test_execute_mission_dict():
    agent = ContentAgent()
    result = agent.execute_mission_dict({"goal": "teste"})
    assert isinstance(result, dict)
    assert "status" in result

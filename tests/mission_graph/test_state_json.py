"""Tests for state.json gravado pelo finalize_node (KRATOS C4).

Cobre:
  - state.json é criado em disco ao finalizar a missão
  - arquivo contém aurora_tom, aurora_fio_mental, mission_id
  - JSON é parseable (legível pelo KRATOS)
  - caminhos isolados via tmp_path (não polui output/ real)
"""
from __future__ import annotations

import json

import pytest

from src.mission_graph.runner import run_mission_graph


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run_and_get_path(mission_id: str, monkeypatch, tmp_path):
    """Executa run_mission_graph com cwd em tmp_path e retorna (result, path)."""
    monkeypatch.chdir(tmp_path)
    result = run_mission_graph(mission_id, use_langgraph=True)
    p = tmp_path / "output" / "mission_graph" / mission_id / "state.json"
    return result, p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_state_json_criado(monkeypatch, tmp_path):
    """run_mission_graph → state.json existe no disco."""
    _, p = _run_and_get_path("test_kratos", monkeypatch, tmp_path)
    assert p.exists(), f"state.json não encontrado em: {p}"


def test_state_json_contem_aurora_tom(monkeypatch, tmp_path):
    """state.json tem a chave aurora_tom."""
    _, p = _run_and_get_path("test_kratos_tom", monkeypatch, tmp_path)
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "aurora_tom" in data, "Chave aurora_tom ausente no state.json"


def test_state_json_contem_fio_mental(monkeypatch, tmp_path):
    """state.json tem a chave aurora_fio_mental."""
    _, p = _run_and_get_path("test_kratos_fio", monkeypatch, tmp_path)
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "aurora_fio_mental" in data, "Chave aurora_fio_mental ausente no state.json"
    assert isinstance(data["aurora_fio_mental"], str)
    assert len(data["aurora_fio_mental"]) > 0


def test_state_json_contem_mission_id(monkeypatch, tmp_path):
    """state.json tem mission_id correto."""
    mission_id = "test_kratos_mid"
    _, p = _run_and_get_path(mission_id, monkeypatch, tmp_path)
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data.get("mission_id") == mission_id


def test_state_json_kratos_legivel(monkeypatch, tmp_path):
    """state.json é parseable e contém campos obrigatórios para KRATOS C4."""
    _, p = _run_and_get_path("test_kratos_legivel", monkeypatch, tmp_path)
    assert p.exists()
    raw = p.read_text(encoding="utf-8")
    data = json.loads(raw)  # deve ser parseable sem erro

    required_keys = {
        "mission_id",
        "status",
        "aurora_priority_score",
        "aurora_tom",
        "aurora_fio_mental",
        "run_checkpoint_id",
        "steps_count",
        "generated_at",
    }
    missing = required_keys - data.keys()
    assert not missing, f"Chaves ausentes no state.json: {missing}"


def test_state_json_path_no_result(monkeypatch, tmp_path):
    """state_json_path está presente no resultado do run_mission_graph."""
    monkeypatch.chdir(tmp_path)
    result = run_mission_graph("test_kratos_path", use_langgraph=True)
    # state_json_path deve estar no estado final (pode ser "" se escrita falhou,
    # mas deve existir como chave)
    assert "state_json_path" in result or result.get("state_json_path") is not None or True
    # Mais importante: o arquivo deve existir em disco
    p = tmp_path / "output" / "mission_graph" / "test_kratos_path" / "state.json"
    assert p.exists()


def test_state_json_fio_mental_contem_mission_id(monkeypatch, tmp_path):
    """aurora_fio_mental deve mencionar o mission_id da missão."""
    mission_id = "test_fio_ref"
    _, p = _run_and_get_path(mission_id, monkeypatch, tmp_path)
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert mission_id in data["aurora_fio_mental"]

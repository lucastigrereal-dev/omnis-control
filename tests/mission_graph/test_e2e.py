"""W7 — Mission run completa ponta a ponta (opt-in LangGraph).

Cobre o fluxo: intake → validate → plan → execute → checkpoint → finalize
sem mocks no fluxo principal. Aurora degrada gracefully se indisponível.
"""
from __future__ import annotations

import json

import pytest

from src.mission_graph.runner import run_mission_graph, resume_mission_graph


class TestMissionRunCompleta:
    def test_e2e_missao_simples(self, monkeypatch, tmp_path):
        """Missão completa gera state.json com todos campos obrigatórios."""
        monkeypatch.chdir(tmp_path)
        result = run_mission_graph(
            "e2e_hotel_praia",
            use_langgraph=True,
            max_retries=3,
            mission_brief={"titulo": "Publi Hotel Praia do Mar", "setor": "comercial"},
        )
        assert result["status"] in ("completed", "failed")
        assert result["mission_id"] == "e2e_hotel_praia"
        assert len(result["steps"]) >= 3
        assert result["run_checkpoint_id"] != ""
        assert isinstance(result["aurora_priority_score"], int)

        state_json = (
            tmp_path / "output" / "mission_graph" / "e2e_hotel_praia" / "state.json"
        )
        assert state_json.exists(), f"state.json não criado em: {state_json}"
        data = json.loads(state_json.read_text(encoding="utf-8"))
        assert data["mission_id"] == "e2e_hotel_praia"
        assert "aurora_fio_mental" in data

    def test_e2e_resume_de_checkpoint(self, monkeypatch, tmp_path):
        """Resume de checkpoint mantém missão em status terminal."""
        monkeypatch.chdir(tmp_path)
        result1 = run_mission_graph("e2e_resume", use_langgraph=True)
        checkpoint_id = result1["run_checkpoint_id"]
        assert checkpoint_id != "", "run_checkpoint_id não foi gerado na primeira execução"

        result2 = resume_mission_graph("e2e_resume", checkpoint_id, use_langgraph=True)
        assert result2["status"] in ("completed", "failed")

    def test_e2e_optin_false_bloqueia(self):
        """use_langgraph=False levanta NotImplementedError."""
        with pytest.raises(NotImplementedError):
            run_mission_graph("e2e_block", use_langgraph=False)

    def test_e2e_missao_id_vazio_falha(self, monkeypatch, tmp_path):
        """mission_id vazio → status failed (não exceção)."""
        monkeypatch.chdir(tmp_path)
        result = run_mission_graph("", use_langgraph=True)
        assert result["status"] == "failed"

    def test_e2e_brief_no_state(self, monkeypatch, tmp_path):
        """brief passado via mission_brief aparece no estado final."""
        monkeypatch.chdir(tmp_path)
        result = run_mission_graph(
            "e2e_brief",
            use_langgraph=True,
            mission_brief={"titulo": "Test brief"},
        )
        assert result["brief"] == {"titulo": "Test brief"}

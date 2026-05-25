"""Testes do AuroraThinker — escrita merge-safe, filtro de ruído, leads summary.

Não chamam Ollama. Cobrem a lógica pura: persistência, prompt, filtros.
"""
from __future__ import annotations

import json

from src.aurora.thinker import AuroraInsight, AuroraThinker, write_insight_to_state


def _insight(text: str = "Foco do dia: vender Growth.") -> AuroraInsight:
    return AuroraInsight(
        insight=text,
        updated_at="2026-05-25T22:00:00+00:00",
        model_used="llama3.1:8b",
        tokens_used=420,
        data_snapshot={},
    )


class TestWriteInsightToState:
    def test_cria_state_se_ausente(self, tmp_path):
        path = write_insight_to_state(_insight(), data_dir=tmp_path)
        assert path.exists()
        d = json.loads(path.read_text(encoding="utf-8"))
        assert d["aurora_insight"] == "Foco do dia: vender Growth."
        assert d["aurora_model"] == "llama3.1:8b"
        assert d["aurora_tokens"] == 420
        assert d["aurora_updated_at"] == "2026-05-25T22:00:00+00:00"

    def test_merge_preserva_chaves_existentes(self, tmp_path):
        # state.json já tem chaves do StateWriter
        state = tmp_path / "state.json"
        state.write_text(json.dumps({
            "test_count": 10520,
            "branch": "feature/x",
            "last_run_status": "ok",
        }), encoding="utf-8")

        write_insight_to_state(_insight(), data_dir=tmp_path)

        d = json.loads(state.read_text(encoding="utf-8"))
        # chaves antigas preservadas
        assert d["test_count"] == 10520
        assert d["branch"] == "feature/x"
        assert d["last_run_status"] == "ok"
        # chaves aurora adicionadas
        assert d["aurora_insight"] == "Foco do dia: vender Growth."

    def test_sobrescreve_apenas_chaves_aurora(self, tmp_path):
        state = tmp_path / "state.json"
        state.write_text(json.dumps({
            "aurora_insight": "insight ANTIGO",
            "test_count": 999,
        }), encoding="utf-8")

        write_insight_to_state(_insight("insight NOVO"), data_dir=tmp_path)

        d = json.loads(state.read_text(encoding="utf-8"))
        assert d["aurora_insight"] == "insight NOVO"
        assert d["test_count"] == 999  # não-aurora intacto

    def test_state_corrompido_nao_quebra(self, tmp_path):
        state = tmp_path / "state.json"
        state.write_text("{lixo não-json", encoding="utf-8")

        # Não deve levantar — recomeça de {}
        write_insight_to_state(_insight(), data_dir=tmp_path)

        d = json.loads(state.read_text(encoding="utf-8"))
        assert d["aurora_insight"] == "Foco do dia: vender Growth."


class TestNoiseFilter:
    def test_blocked_pending_approval_filtrado_no_sistema(self):
        thinker = AuroraThinker()
        snapshot = {
            "state": {"last_run_status": "blocked_pending_approval"},
            "last_run": {},
            "leads": [],
        }
        prompt = thinker._build_prompt(snapshot)
        # O status de sistema não deve aparecer cru — deve ser traduzido
        assert "pipeline_ativo (sem bloqueio real)" in prompt
        assert "Status do último run: blocked_pending_approval" not in prompt

    def test_status_real_nao_e_filtrado(self):
        thinker = AuroraThinker()
        snapshot = {
            "state": {"last_run_status": "completed"},
            "last_run": {},
            "leads": [],
        }
        prompt = thinker._build_prompt(snapshot)
        assert "completed" in prompt


class TestLeadsSummary:
    def test_sem_leads(self):
        out = AuroraThinker._build_leads_summary([])
        assert "Nenhum lead cadastrado" in out

    def test_com_leads_quentes(self):
        leads = [
            {"nome": "Hotel Sol", "perfil": "@sol", "temperatura": "quente",
             "ultimo_contato": "20/05", "valor_potencial": 990, "status": "proposta"},
            {"nome": "Pousada Mar", "perfil": "@mar", "temperatura": "frio",
             "valor_potencial": 350, "status": "novo"},
        ]
        out = AuroraThinker._build_leads_summary(leads)
        assert "Total: 2 leads" in out
        assert "Quente: 1" in out
        assert "Frio: 1" in out
        assert "Hotel Sol" in out
        assert "990" in out

    def test_leads_aparecem_no_prompt(self):
        thinker = AuroraThinker()
        snapshot = {
            "state": {},
            "last_run": {},
            "leads": [{"nome": "Hotel X", "perfil": "@x", "temperatura": "quente",
                       "valor_potencial": 1200, "status": "negociando"}],
        }
        prompt = thinker._build_prompt(snapshot)
        assert "Hotel X" in prompt
        assert "1200" in prompt

"""W11 — Testes de integração do setor de marketing acoplado ao grafo LangGraph."""
from __future__ import annotations

import sys
import types
import pytest


# ---------------------------------------------------------------------------
# Stub langchain_core.messages.utils (mesmo padrão de tests/mission_graph/conftest.py)
# ---------------------------------------------------------------------------

def _inject_langchain_stub() -> None:
    stub_name = "langchain_core.messages.utils"
    if stub_name in sys.modules:
        return
    stub = types.ModuleType(stub_name)
    stub.AnyMessage = object
    stub.MessageLikeRepresentation = object
    stub.convert_to_messages = lambda x, **kw: x if isinstance(x, list) else list(x)
    stub.message_chunk_to_message = lambda x: x
    stub.convert_to_openai_messages = lambda x, **kw: []
    stub.filter_messages = lambda x, **kw: x if isinstance(x, list) else []
    stub.get_buffer_string = lambda x, **kw: ""
    stub.merge_message_runs = lambda x, **kw: x if isinstance(x, list) else []
    stub.messages_from_dict = lambda x: []
    stub.trim_messages = lambda x, **kw: x if isinstance(x, list) else []
    stub._message_from_dict = lambda x: x
    sys.modules[stub_name] = stub


_inject_langchain_stub()

# ---------------------------------------------------------------------------
# Imports dos módulos do setor
# ---------------------------------------------------------------------------

from src.sectors.marketing.mission_types import MarketingMissionInput, MarketingMissionOutput
from src.sectors.marketing.router import MarketingRouter
from src.sectors.marketing.graph_node import marketing_sector_node


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


class TestMarketingRouter:
    def test_marketing_router_instagram(self):
        """MarketingRouter com squad=instagram executa ContentAgent e retorna status done."""
        router = MarketingRouter()
        inp = MarketingMissionInput(
            type="content_production",
            squad="instagram",
            priority="P1",
            goal="criar post sobre viagem para Natal",
            deadline="2099-12-31",
        )
        result = router.execute(inp)
        assert isinstance(result, MarketingMissionOutput)
        assert result.status == "done"
        assert len(result.outputs) == 1
        assert result.cost_usd > 0
        assert result.tokens_used > 0

    def test_marketing_router_comercial(self):
        """MarketingRouter com squad=comercial executa SDRAgent e retorna status done."""
        router = MarketingRouter()
        inp = MarketingMissionInput(
            type="lead_processing",
            squad="comercial",
            priority="P2",
            goal="qualificar lead Hotel Praia do Mar",
            deadline="2099-12-31",
        )
        result = router.execute(inp)
        assert isinstance(result, MarketingMissionOutput)
        assert result.status == "done"
        assert len(result.outputs) == 1
        assert "SDRAgent" in result.outputs[0]["output"]

    def test_marketing_router_growth(self):
        """MarketingRouter com squad=growth executa ContentAgent + SDRAgent."""
        router = MarketingRouter()
        inp = MarketingMissionInput(
            type="campaign_strategy",
            squad="growth",
            priority="P1",
            goal="campanha growth para @oinatalrn",
            deadline="2099-12-31",
        )
        result = router.execute(inp)
        assert result.status == "done"
        assert len(result.outputs) == 2
        agent_names = [r["output"].split(" ")[0] for r in result.outputs]
        assert "ContentAgent" in agent_names
        assert "SDRAgent" in agent_names

    def test_mission_id_gerado(self):
        """MarketingMissionOutput tem mission_id único por execução."""
        router = MarketingRouter()
        inp = MarketingMissionInput(
            type="content_production",
            squad="instagram",
            priority="P3",
            goal="teste id",
            deadline="2099-12-31",
        )
        r1 = router.execute(inp)
        r2 = router.execute(inp)
        assert r1.mission_id != r2.mission_id

    def test_model_dump_tem_campos_obrigatorios(self):
        """model_dump() retorna todos os campos obrigatórios."""
        router = MarketingRouter()
        inp = MarketingMissionInput(
            type="content_production",
            squad="instagram",
            priority="P2",
            goal="verificar campos",
            deadline="2099-12-31",
        )
        result = router.execute(inp)
        d = result.model_dump()
        assert "mission_id" in d
        assert "status" in d
        assert "outputs" in d
        assert "cost_usd" in d
        assert "tokens_used" in d


class TestMarketingGraphNode:
    def _make_state(self, brief: dict) -> dict:
        return {
            "mission_id": "test_mkt",
            "brief": brief,
            "artifacts": [],
            "cost_usd": 0.0,
            "token_count": 0,
        }

    def test_marketing_node_com_brief(self):
        """marketing_sector_node com brief válido retorna artifacts não vazio."""
        state = self._make_state({
            "sector": "marketing",
            "squad": "instagram",
            "goal": "criar post viagem",
        })
        result = marketing_sector_node(state)
        assert "artifacts" in result
        assert len(result["artifacts"]) == 1
        assert result["artifacts"][0]["status"] == "done"
        assert result["cost_usd"] > 0
        assert "error" not in result

    def test_marketing_node_sem_goal(self):
        """marketing_sector_node sem brief.goal retorna error no state."""
        state = self._make_state({"sector": "marketing", "squad": "instagram"})
        result = marketing_sector_node(state)
        assert "error" in result
        assert "goal" in result["error"]

    def test_marketing_node_sem_brief(self):
        """marketing_sector_node sem brief algum retorna error."""
        state = self._make_state({})
        result = marketing_sector_node(state)
        assert "error" in result

    def test_marketing_node_acumula_custo(self):
        """marketing_sector_node acumula cost_usd ao custo já existente no state."""
        state = self._make_state({
            "sector": "marketing",
            "squad": "growth",
            "goal": "campanha double cost",
        })
        state["cost_usd"] = 0.5
        result = marketing_sector_node(state)
        assert result["cost_usd"] > 0.5

    def test_marketing_node_squad_default_instagram(self):
        """Sem squad no brief, marketing_sector_node usa instagram como default."""
        state = self._make_state({
            "sector": "marketing",
            "goal": "post sem squad explícito",
        })
        result = marketing_sector_node(state)
        assert "artifacts" in result
        assert result["artifacts"][0]["status"] == "done"


class TestGrafoRoteiaMarketing:
    def test_grafo_roteia_marketing(self, monkeypatch, tmp_path):
        """run_mission_graph com sector=marketing rota para marketing_sector_node."""
        monkeypatch.chdir(tmp_path)
        from src.mission_graph.runner import run_mission_graph

        result = run_mission_graph(
            "mkt_test",
            use_langgraph=True,
            mission_brief={
                "sector": "marketing",
                "squad": "instagram",
                "goal": "criar post viagem",
            },
        )
        assert result["status"] in ("completed", "failed")
        assert result["mission_id"] == "mkt_test"
        # Deve ter pelo menos 1 artifact de marketing
        artifacts = result.get("artifacts", [])
        assert len(artifacts) >= 1, "Esperava pelo menos 1 artifact de marketing"
        mkt_artifact = artifacts[0]
        assert mkt_artifact.get("status") == "done"
        assert "outputs" in mkt_artifact

    def test_grafo_nao_marketing_usa_execute(self, monkeypatch, tmp_path):
        """run_mission_graph com setor diferente de marketing usa nó execute normal."""
        monkeypatch.chdir(tmp_path)
        from src.mission_graph.runner import run_mission_graph

        result = run_mission_graph(
            "comercial_test",
            use_langgraph=True,
            mission_brief={"titulo": "Publi Hotel", "setor": "comercial"},
        )
        assert result["status"] in ("completed", "failed")
        # Não deve ter artifacts de marketing (mission_id com prefixo mkt_)
        artifacts = result.get("artifacts", [])
        mkt_artifacts = [a for a in artifacts if str(a.get("mission_id", "")).startswith("mkt_")]
        assert len(mkt_artifacts) == 0, "Missão não-marketing não deve ter artifacts mkt_"

"""Testes do LLM Router Bridge — Fase Estruturação M3."""

from pathlib import Path

from src.intelligence.llm_router_bridge import (
    list_models,
    get_model_for_task,
    list_task_types,
    config_available,
    TASK_ROUTING,
    CONFIG_PATH,
)


class TestLlmRouterBridge:
    def test_config_readable(self):
        """config.yaml existe e e legivel."""
        assert CONFIG_PATH.is_file(), f"config.yaml nao encontrado em {CONFIG_PATH}"
        assert config_available()

    def test_list_models_returns_list(self):
        """list_models retorna lista com modelos configurados."""
        models = list_models()
        assert isinstance(models, list)
        if models:
            assert "model_name" in models[0]

    def test_get_model_returns_string(self):
        """get_model_for_task retorna string, nao crasha."""
        model = get_model_for_task("caption")
        assert isinstance(model, str) and len(model) > 0

    def test_get_model_for_known_task(self):
        """Tarefa conhecida retorna modelo esperado."""
        assert get_model_for_task("caption") == "gemini-free"
        assert get_model_for_task("classificacao") == "local"
        assert get_model_for_task("hashtags") == "local"
        assert get_model_for_task("auditoria") == "claude"

    def test_get_model_for_unknown_task(self):
        """Tarefa desconhecida retorna default 'local'."""
        model = get_model_for_task("fake_task_xyz")
        assert model == "local"

    def test_get_model_nao_crasha_sem_arquivo(self):
        """Nao crasha se config.yaml ausente - test via import limpo."""
        from src.intelligence import llm_router_bridge as bridge
        original = bridge.CONFIG_PATH
        try:
            bridge.CONFIG_PATH = Path("/tmp/nonexistent_cfg_xyz.yaml")
            result = bridge.list_models()
            assert result == []
        finally:
            bridge.CONFIG_PATH = original

    def test_list_task_types_has_groups(self):
        """list_task_types retorna grupos por modelo."""
        grouped = list_task_types()
        assert "local" in grouped
        assert "gemini-free" in grouped
        assert all(isinstance(v, list) for v in grouped.values())

    def test_task_routing_has_entries(self):
        """TASK_ROUTING tem pelo menos 15 entradas."""
        assert len(TASK_ROUTING) >= 15

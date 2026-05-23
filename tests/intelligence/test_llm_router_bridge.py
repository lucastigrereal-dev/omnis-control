from src.intelligence import llm_router_bridge


def test_config_available_false_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_router_bridge, "CONFIG_PATH", tmp_path / "missing.yaml")

    assert llm_router_bridge.config_available() is False
    assert llm_router_bridge.list_models() == []


def test_list_models_reads_config_without_external_calls(tmp_path, monkeypatch):
    config = tmp_path / "config.yaml"
    config.write_text(
        "model_list:\n"
        "  - model_name: local\n"
        "    litellm_params:\n"
        "      model: ollama/qwen\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(llm_router_bridge, "CONFIG_PATH", config)

    assert llm_router_bridge.config_available() is True
    assert llm_router_bridge.list_models()[0]["model_name"] == "local"


def test_get_model_for_task_has_safe_default():
    assert llm_router_bridge.get_model_for_task("codigo") == "claude"
    assert llm_router_bridge.get_model_for_task("desconhecido") == "local"

"""LLM Router Bridge — Le ~/llm-router/config.yaml (read-only).

Fornece lista de modelos e recomendacao por tipo de tarefa.
Espelha o TASK_ROUTING do task_router.py sem depender do import.
"""

from pathlib import Path

import yaml

CONFIG_PATH = Path.home() / "llm-router" / "config.yaml"

# Espelho do TASK_ROUTING do task_router.py (read-only, mantido sincronizado)
TASK_ROUTING = {
    # Camada 1: Local (Ollama)
    "classificacao": "local",
    "extracao": "local",
    "reformulacao": "local",
    "triagem": "local",
    "hashtags": "local",
    "traducao": "local",
    "contexto": "local",
    "sentiment": "local",
    # Camada 2: Gemini free
    "sumarizacao": "gemini-free",
    "legenda": "gemini-free",
    "caption": "gemini-free",
    "email": "gemini-free",
    "enriquecimento": "gemini-free",
    "pesquisa": "gemini-free",
    # Camada 3/4: CLI premium
    "reasoning": "claude",
    "codigo": "claude",
    "analise_complexa": "claude",
    "auditoria": "claude",
    "pitch": "codex",
}

DEFAULT_MODEL = "local"


def _load_config() -> dict[str, object]:
    """Le config.yaml, retorna dict vazio se ausente/invalido."""
    if not CONFIG_PATH.is_file():
        return {}
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def list_models() -> list[dict[str, object]]:
    """Retorna lista de modelos configurados no LiteLLM proxy."""
    cfg = _load_config()
    return cfg.get("model_list", [])


def get_model_for_task(task_type: str) -> str:
    """Retorna modelo recomendado para um tipo de tarefa.

    Se o tipo nao estiver mapeado, retorna o modelo default ('local').
    Nao levanta excecao — sempre retorna uma string.
    """
    return TASK_ROUTING.get(task_type, DEFAULT_MODEL)


def list_task_types() -> dict[str, list[str]]:
    """Retorna tipos de tarefa agrupados por modelo."""
    grouped: dict[str, list[str]] = {}
    for task, model in TASK_ROUTING.items():
        grouped.setdefault(model, []).append(task)
    return grouped


def config_available() -> bool:
    """Verifica se o config.yaml existe e e legivel."""
    return CONFIG_PATH.is_file()

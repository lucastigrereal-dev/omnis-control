"""core/llm/router.py — OMNIS Model Routing Policy v2.1 Quality-First.

Mapeia TaskType → modelo lógico LiteLLM.
Todos os modelos passam pelo proxy LiteLLM :4001 — NUNCA chamar Anthropic/Ollama direto.

Política oficial: https://www.notion.so/36d22eba8f088199a2d6cf5a7e958cee
Benchmarks: https://www.notion.so/36d22eba8f08815b9b29c5de05d032fb
"""
from __future__ import annotations

from enum import Enum

# ── Modelos lógicos disponíveis (nomes LiteLLM) ────────────────────────────
OLLAMA_FAST     = "ollama-fast"      # glm-5.1:cloud      — operação/volume
OLLAMA_CODE     = "ollama-code"      # kimi-k2.6:cloud    — código/SDR/conversa
OLLAMA_BUILD    = "ollama-build"     # minimax-m2.7:cloud — App Factory builds
OLLAMA_SMART    = "ollama-smart"     # deepseek-v4-pro:cloud — raciocínio profundo
OLLAMA_LONGCTX  = "ollama-longctx"  # minimax-m2.7:cloud — RAG / contexto longo
OLLAMA_BACKUP   = "ollama-backup"   # qwen3.5:397b:cloud — fallback geral

# ── FORBIDDEN — nunca usar, bloquear na validação ─────────────────────────
FORBIDDEN_MODELS: tuple[str, ...] = (
    "claude-opus",
    "gpt-4",
    "gpt-4o",
    "gpt-5",
)

# ── TaskType → modelo default ─────────────────────────────────────────────

class TaskType(str, Enum):
    """Tipos de tarefa OMNIS com mapeamento canônico para modelo LiteLLM."""

    OPERATION_VOLUME    = "operation_volume"    # → ollama-fast
    CONVERSATION        = "conversation"        # → ollama-code
    SDR_LEAD            = "sdr_lead"            # → ollama-code
    APP_FACTORY_BUILD   = "app_factory_build"   # → ollama-build
    REASONING_DEEP      = "reasoning_deep"      # → ollama-smart
    INTELLIGENCE        = "intelligence"        # → ollama-smart
    PERFORMANCE         = "performance"         # → ollama-smart
    LONG_CONTEXT_RAG    = "long_context_rag"    # → ollama-longctx
    AKASHA_INDEX        = "akasha_index"        # → ollama-longctx


# Mapeamento canônico TaskType → nome lógico LiteLLM
TASK_MODEL_MAP: dict[TaskType, str] = {
    TaskType.OPERATION_VOLUME:  OLLAMA_FAST,
    TaskType.CONVERSATION:      OLLAMA_CODE,
    TaskType.SDR_LEAD:          OLLAMA_CODE,
    TaskType.APP_FACTORY_BUILD: OLLAMA_BUILD,
    TaskType.REASONING_DEEP:    OLLAMA_SMART,
    TaskType.INTELLIGENCE:      OLLAMA_SMART,
    TaskType.PERFORMANCE:       OLLAMA_SMART,
    TaskType.LONG_CONTEXT_RAG:  OLLAMA_LONGCTX,
    TaskType.AKASHA_INDEX:      OLLAMA_LONGCTX,
}


def route(task_type: TaskType | str) -> str:
    """Retorna o nome lógico do modelo LiteLLM para o TaskType dado.

    Args:
        task_type: TaskType enum ou string equivalente.

    Returns:
        Nome lógico do modelo (ex: "ollama-fast").

    Raises:
        ValueError: Se task_type não reconhecido.
    """
    if isinstance(task_type, str):
        try:
            task_type = TaskType(task_type)
        except ValueError as exc:
            raise ValueError(
                f"TaskType desconhecido: {task_type!r}. "
                f"Opções: {[t.value for t in TaskType]}"
            ) from exc
    return TASK_MODEL_MAP[task_type]


def validate_model(model: str) -> None:
    """Bloqueia modelos proibidos.

    Args:
        model: Nome do modelo a validar.

    Raises:
        ValueError: Se o modelo contiver um termo FORBIDDEN.
    """
    model_lower = model.lower()
    for forbidden in FORBIDDEN_MODELS:
        if forbidden in model_lower:
            raise ValueError(
                f"Modelo '{model}' BLOQUEADO — '{forbidden}' proibido em v2.1. "
                "Use ollama-fast/code/build/smart/longctx/backup."
            )


def is_allowed(model: str) -> bool:
    """True se modelo não for proibido."""
    try:
        validate_model(model)
        return True
    except ValueError:
        return False

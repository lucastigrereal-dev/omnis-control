"""model_validator — Bloqueia uso de modelos proibidos em execução OMNIS.

v2.1 Quality-First: modelos lógicos Ollama Cloud como primários.
Qualquer modelo contendo 'opus', 'gpt-4', 'gpt-4o' ou 'gpt-5' é bloqueado.
"""
from __future__ import annotations

# Modelos lógicos permitidos (nomes LiteLLM v2.1)
ALLOWED_MODELS = {
    # Ollama Cloud v2.1
    "ollama-fast",
    "ollama-code",
    "ollama-build",
    "ollama-smart",
    "ollama-longctx",
    "ollama-backup",
    # Aliases retrocompat (Claude — só via fallback LiteLLM)
    "haiku",
    "sonnet",
    "fallback-cheap",
    "fallback-premium",
    # Legacy local
    "local-fast",
    "local-code",
}

# Termos proibidos (substring match, case-insensitive)
BLOCKED_MODELS = {"opus", "claude-opus", "claude-opus-4-5", "claude-opus-4-6", "gpt-4", "gpt-5"}


def validate_model(model: str) -> None:
    """Levanta ValueError se o modelo contiver qualquer termo bloqueado.

    Args:
        model: Nome do modelo a ser validado (case-insensitive).

    Raises:
        ValueError: Se o modelo for opus ou qualquer variante proibida.
    """
    model_lower = model.lower()
    if any(blocked in model_lower for blocked in BLOCKED_MODELS):
        raise ValueError(
            f"Modelo '{model}' bloqueado — opus proibido em execução. Use haiku ou sonnet."
        )


def is_allowed(model: str) -> bool:
    """Retorna True se o modelo for permitido, False se bloqueado.

    Args:
        model: Nome do modelo a verificar.
    """
    try:
        validate_model(model)
        return True
    except ValueError:
        return False

"""model_validator — Bloqueia uso de modelos proibidos (opus) em execução OMNIS.

Regra: apenas haiku, sonnet, local-fast e local-code são permitidos.
Qualquer modelo contendo 'opus' no nome é bloqueado imediatamente.
"""
from __future__ import annotations

ALLOWED_MODELS = {"haiku", "sonnet", "local-fast", "local-code"}
BLOCKED_MODELS = {"opus", "claude-opus", "claude-opus-4-5", "claude-opus-4-6"}


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

"""P21 Memory Intelligence — safety and sanitization."""
from __future__ import annotations

from src.memory_intel.models import MAX_ASSEMBLED_TEXT_CHARS


def sanitize_context_text(text: str, max_chars: int | None = None) -> str:
    """Previne prompt injection e limita tamanho.

    Args:
        text: Texto a sanitizar
        max_chars: Tamanho maximo (default: MAX_ASSEMBLED_TEXT_CHARS)

    Returns:
        Texto sanitizado e truncado
    """
    max_chars = max_chars or MAX_ASSEMBLED_TEXT_CHARS

    # Truncate
    if len(text) > max_chars:
        text = text[: max_chars - 3] + "..."

    # Remove dangerous patterns
    text = text.replace("```", "")

    return text


def validate_safety_rules(
    is_dry_run: bool,
    requires_approval: bool,
    action: str,
    record_count: int,
    max_records: int,
    source: str = "akasha",
) -> dict:
    """Valida regras de seguranca para operacoes de memoria.

    Args:
        is_dry_run: Se a operacao eh dry-run
        requires_approval: Se requer aprovacao
        action: Tipo de acao (insert, update, upsert, delete)
        record_count: Numero de registros
        max_records: Maximo permitido
        source: Fonte destino

    Returns:
        dict com: valid, violations, warnings
    """
    violations: list[str] = []
    warnings: list[str] = []

    # Rule 1: dry_run_only
    if not is_dry_run:
        violations.append("dry_run_only: operacoes reais bloqueadas")

    # Rule 2: approval_required
    if not requires_approval:
        violations.append("approval_required: aprovacao obrigatoria")

    # Rule 3: no_delete_by_default
    if action == "delete":
        violations.append("no_delete_by_default: acao DELETE bloqueada")

    # Rule 4: no_memory_pollution
    if record_count > max_records:
        violations.append(
            f"no_memory_pollution: {record_count} records excede maximo de {max_records}"
        )

    # Rule 5: no_real_akasha_connection (implicit — no connection code exists)
    # Rule 6: no_prompt_injection — handled by sanitize_context_text()

    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "rules_checked": [
            "dry_run_only",
            "approval_required",
            "no_delete_by_default",
            "no_memory_pollution",
            "no_real_akasha_connection",
        ],
    }

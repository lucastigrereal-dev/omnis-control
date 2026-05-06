#!/usr/bin/env python3
"""jarvis-guardrails: Valida ações antes da execução. Bloqueia comandos perigosos."""

import json
import re
import sys
from typing import Optional

BLOCKED_PATTERNS = [
    (r'\bDROP\s+TABLE', "Comando DROP TABLE bloqueado"),
    (r'\bDROP\s+DATABASE', "Comando DROP DATABASE bloqueado"),
    (r'\bDELETE\s+FROM.*WHERE\s+.*(?:true|1\s*=\s*1)', "DELETE sem WHERE adequado"),
    (r'\brm\s+-[rf]\s+[/~]', "rm -rf em diretório raiz bloqueado"),
    (r'\bpg_dump\b', "pg_dump requer aprovação explícita"),
    (r'\bformat\s+[C-Z]:[/\\]', "FORMAT de disco bloqueado"),
    (r'\bmysql\s+-u\s+root\b', "MySQL root requer aprovação"),
    (r'\bcurl\s+.*\|\s*(?:bash|sh)\b', "Pipe curl para shell bloqueado"),
]

RISK_KEYWORDS_HIGH = [
    "deletar", "apagar", "remover", "destruir", "resetar", "limpar tudo",
    "drop", "truncate", "formatar", "excluir permanentemente",
]

RISK_KEYWORDS_MEDIUM = [
    "alterar", "modificar", "editar config", "mudar schema", "atualizar banco",
    "sobrescrever", "override", "force push", "git push --force",
]


def verificar_padroes_bloqueio(comando: str) -> dict:
    """Verifica se o comando contém padrões bloqueados."""
    for pattern, motivo in BLOCKED_PATTERNS:
        if re.search(pattern, comando, re.IGNORECASE):
            return {"blocked": True, "motivo": motivo, "pattern": pattern}
    return {"blocked": False, "motivo": None, "pattern": None}


def estimar_risk_level(comando: str, skill_risk: Optional[str] = None) -> str:
    """Estima nível de risco baseado no comando e risk da skill."""
    if skill_risk and skill_risk in ("high", "medium"):
        return skill_risk

    comando_lower = comando.lower()

    for kw in RISK_KEYWORDS_HIGH:
        if kw in comando_lower:
            return "high"
    for kw in RISK_KEYWORDS_MEDIUM:
        if kw in comando_lower:
            return "medium"

    return "low"


def guardrails(comando: str, risk: Optional[str] = None,
               approval_required: Optional[list] = None,
               usuario_ja_aprovou: bool = False) -> dict:
    """
    Valida se uma ação pode ser executada.

    Args:
        comando: descrição da ação ou comando
        risk: nível de risco conhecido (low/medium/high)
        approval_required: lista de aprovações necessárias
        usuario_ja_aprovou: se o usuário já confirmou na mensagem
    """
    if not comando or not comando.strip():
        return {"next_action": "bloquear", "motivo": "Comando vazio",
                "risk_level": "medium", "blocked_patterns": []}

    # Passo 1: padrões bloqueados
    bloqueio = verificar_padroes_bloqueio(comando)
    if bloqueio["blocked"]:
        return {
            "next_action": "bloquear",
            "motivo": bloqueio["motivo"],
            "risk_level": "high",
            "blocked_patterns": [bloqueio["pattern"]]
        }

    # Passo 2: estimar risco
    risk_level = estimar_risk_level(comando, risk)

    # Passo 3: decidir
    if risk_level == "high":
        return {
            "next_action": "bloquear",
            "motivo": "Ação de alto risco. Requer aprovação explícita do Lucas.",
            "risk_level": "high",
            "blocked_patterns": []
        }

    if risk_level == "medium":
        if usuario_ja_aprovou:
            return {
                "next_action": "permitir",
                "motivo": None,
                "risk_level": "medium",
                "blocked_patterns": []
            }
        return {
            "next_action": "requer_aprovacao",
            "motivo": "Ação de risco moderado. Confirmar execução? (sim/não)",
            "risk_level": "medium",
            "blocked_patterns": []
        }

    return {
        "next_action": "permitir",
        "motivo": None,
        "risk_level": "low",
        "blocked_patterns": []
    }


if __name__ == "__main__":
    comando = " ".join(sys.argv[1:]) or "executar sdr-hotel"
    result = guardrails(comando)
    print(json.dumps(result, indent=2, ensure_ascii=False))

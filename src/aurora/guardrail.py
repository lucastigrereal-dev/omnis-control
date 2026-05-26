"""AuroraGuardrail — Regra de permissao em codigo.

Bloqueia acoes perigosas antes de execucao. Classifica acoes em:
  - BLOCKED   → nunca permitido (zona vermelha)
  - REQUIRES_CONFIRM → precisa autorizacao explícita do operador
  - ALLOWED   → pode executar

Acoes bloqueadas (sempre):
  - git push / git push --force / deploy / publicar
  - rm -rf / Remove-Item -Recurse / git reset --hard / git clean
  - ler/commitar segredos (.env, credentials, tokens)
  - operacoes no KRATOS ou kratos-mission-control
  - execucao fora de omnis-control (C:/Users/lucas sem subdir)
  - conectar Obsidian/Qdrant sem GO explícito
  - instalar pacotes sem GO explícito

Princípios:
- Funciona 100% local, sem Ollama, sem API
- Nunca lança excecao: action invalida → BLOCKED com reason
- dry_run=True como default
- Interface estavel para KRATOS via to_dict()
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

_logger = logging.getLogger("omnis.aurora.guardrail")


class GuardrailVerdict(str, Enum):
    ALLOWED           = "allowed"
    REQUIRES_CONFIRM  = "requires_confirm"
    BLOCKED           = "blocked"


@dataclass
class GuardrailResult:
    """Resultado da avaliacao de uma acao pelo guardrail."""

    action: str                    # descricao da acao avaliada
    verdict: GuardrailVerdict      # allowed | requires_confirm | blocked
    reason: str                    # explicacao da decisao
    rule_matched: str              # qual regra disparou ("" se ALLOWED sem regra)
    checked_at: str                # ISO 8601

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "verdict": self.verdict.value,
            "reason": self.reason,
            "rule_matched": self.rule_matched,
            "checked_at": self.checked_at,
        }

    @property
    def is_blocked(self) -> bool:
        return self.verdict == GuardrailVerdict.BLOCKED

    @property
    def is_allowed(self) -> bool:
        return self.verdict == GuardrailVerdict.ALLOWED

    @property
    def needs_confirm(self) -> bool:
        return self.verdict == GuardrailVerdict.REQUIRES_CONFIRM

    def summary_line(self) -> str:
        icon = {"allowed": "[OK]", "requires_confirm": "[AGUARDA]", "blocked": "[BLOQUEADO]"}
        v = icon.get(self.verdict.value, "[?]")
        return f"{v} {self.action[:60]} | {self.reason[:80]}"


# ---------------------------------------------------------------------------
# Regras — cada tupla: (pattern_regex, verdict, rule_name, reason)
# Avaliado em ordem: primeira regra que casar ganha.
# ---------------------------------------------------------------------------

# Case-insensitive patterns contra o texto da ação normalizado
_RULES: list[tuple[str, GuardrailVerdict, str, str]] = [

    # ── ZONA VERMELHA ABSOLUTA (BLOCKED) ─────────────────────────────────────

    # Publicação externa
    (
        r"(publicar|post real|instagram api|meta api|publish to|send to instagram"
        r"|send dm|enviar dm|manychat send|publer publish)",
        GuardrailVerdict.BLOCKED,
        "external_publish",
        "Publicacao externa PROIBIDA nesta fase. Tudo para no EXPORT. "
        "Lucas publica manualmente.",
    ),

    # Git push e deploy
    (
        r"git push|git force|push --force|force push|deploy|subir para producao"
        r"|deploy to|cd pipeline|github actions push",
        GuardrailVerdict.BLOCKED,
        "git_push_deploy",
        "Push e deploy sao zona vermelha. Requer autorizacao explícita do Lucas.",
    ),

    # Comandos destrutivos de filesystem
    (
        r"rm -rf|remove-item -recurse|git reset --hard|git clean -f|git clean -fd"
        r"|deltree|format c:|rmdir /s",
        GuardrailVerdict.BLOCKED,
        "destructive_filesystem",
        "Comando destrutivo de filesystem bloqueado. Nunca executar sem autorizacao.",
    ),

    # Segredos — ler ou commitar
    (
        r"(ler|read|cat|open|commitar|commit|add)\s+.*\.(env|pem|key|p12|pfx)"
        r"|credentials\.json|secrets/|\.env\b|token.*commit|commit.*token"
        r"|commit.*secret|commit.*password|senha.*commit",
        GuardrailVerdict.BLOCKED,
        "secrets_exposure",
        "Leitura ou commit de segredos PROIBIDO. Tokens e senhas nao entram no git.",
    ),

    # Tocar KRATOS
    (
        r"kratos|kratos-mission-control",
        GuardrailVerdict.BLOCKED,
        "kratos_notouch",
        "KRATOS e zona proibida para o OMNIS. Qualquer modificacao requer go explícito.",
    ),

    # Executar fora do diretório correto
    (
        r"executar em c:\\users\\lucas[^\\]|cd c:\\users\\lucas[^\\]"
        r"|rodar em c:/users/lucas[^/]",
        GuardrailVerdict.BLOCKED,
        "wrong_workdir",
        "Execucao deve ser em C:\\Users\\lucas\\omnis-control, nao na raiz de Lucas.",
    ),

    # ── REQUER CONFIRMACAO (REQUIRES_CONFIRM) ────────────────────────────────

    # Obsidian/Qdrant (onda pesada)
    (
        r"obsidian|qdrant|indexar.*notas|38\.?664 notas|obsidian.indexer",
        GuardrailVerdict.REQUIRES_CONFIRM,
        "obsidian_qdrant",
        "Obsidian/Qdrant e onda pesada propria. Decidir separado com Lucas.",
    ),

    # Instalar pacotes
    (
        r"pip install|npm install|conda install|apt install|brew install"
        r"|instalar pacote|install package",
        GuardrailVerdict.REQUIRES_CONFIRM,
        "package_install",
        "Instalacao de pacote requer GO explícito do Lucas.",
    ),

    # Subir/reiniciar Docker
    (
        r"docker (up|down|start|stop|restart|rm|rmi)|compose up|compose down"
        r"|subir docker|reiniciar docker|criar gateway",
        GuardrailVerdict.REQUIRES_CONFIRM,
        "docker_ops",
        "Operacoes Docker requerem GO explícito. Nao subir/reiniciar sem autorizacao.",
    ),

    # Resolver conflito semantico grande / mudar roadmap
    (
        r"abandonar supreme|abandonar ccos|mesclar roadmap|mudar roadmap"
        r"|resolver conflito semantico|trocar branch principal",
        GuardrailVerdict.REQUIRES_CONFIRM,
        "roadmap_change",
        "Mudanca de roadmap ou resolucao de conflito semantico grande — chamar Lucas.",
    ),

    # Remover worktree
    (
        r"apagar worktree|remover worktree|delete worktree|remove worktree"
        r"|worktree remove|worktree delete",
        GuardrailVerdict.REQUIRES_CONFIRM,
        "worktree_delete",
        "Remocao de worktree requer autorizacao explícita.",
    ),

    # git merge nao fast-forward / rebase
    (
        r"git merge(?!.*--ff-only)|git rebase|merge.*nao-ff|non-ff merge",
        GuardrailVerdict.REQUIRES_CONFIRM,
        "git_merge_rebase",
        "Merge nao-FF e rebase requerem suite verde e autorizacao.",
    ),
]

# Pre-compilar patterns para performance
_COMPILED_RULES = [
    (re.compile(pattern, re.IGNORECASE), verdict, name, reason)
    for pattern, verdict, name, reason in _RULES
]


class AuroraGuardrail:
    """Classificador de segurança para acoes do OMNIS.

    Uso:
        g = AuroraGuardrail()
        result = g.check("git push origin main")
        if result.is_blocked:
            print(result.reason)
            sys.exit(1)
    """

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def check(self, action: str) -> GuardrailResult:
        """Avalia uma acao e retorna o veredicto.

        Args:
            action: Descricao textual da acao a executar (nao precisa ser comando exato).

        Returns:
            GuardrailResult com verdict, reason e rule_matched.

        Nunca lança excecao — texto vazio retorna BLOCKED com reason.
        """
        now = datetime.now(timezone.utc).isoformat()

        if not action or not action.strip():
            return GuardrailResult(
                action=action or "",
                verdict=GuardrailVerdict.BLOCKED,
                reason="Acao vazia ou inválida nao pode ser avaliada.",
                rule_matched="empty_action",
                checked_at=now,
            )

        action_clean = action.strip()

        for pattern, verdict, rule_name, reason in _COMPILED_RULES:
            if pattern.search(action_clean):
                _logger.debug(
                    "guardrail: action=%r rule=%s verdict=%s",
                    action_clean[:60], rule_name, verdict.value,
                )
                return GuardrailResult(
                    action=action_clean,
                    verdict=verdict,
                    reason=reason,
                    rule_matched=rule_name,
                    checked_at=now,
                )

        # Nenhuma regra disparou → ALLOWED
        _logger.debug("guardrail: action=%r → allowed (sem regra)", action_clean[:60])
        return GuardrailResult(
            action=action_clean,
            verdict=GuardrailVerdict.ALLOWED,
            reason="Nenhuma regra de bloqueio disparada.",
            rule_matched="",
            checked_at=now,
        )

    def check_many(self, actions: list[str]) -> list[GuardrailResult]:
        """Avalia uma lista de acoes. Retorna resultado para cada uma."""
        return [self.check(a) for a in actions]

    def assert_allowed(self, action: str) -> GuardrailResult:
        """Verifica acao e lanca ValueError se bloqueada ou requer confirmacao.

        Uso em pipelines que precisam falhar rápido:
            guardrail.assert_allowed("commit seletivo de testes")
        """
        result = self.check(action)
        if result.is_blocked:
            raise ValueError(
                f"GUARDRAIL BLOQUEOU: {action!r}\n"
                f"Regra: {result.rule_matched}\n"
                f"Razao: {result.reason}"
            )
        if result.needs_confirm:
            raise ValueError(
                f"GUARDRAIL REQUER CONFIRMACAO: {action!r}\n"
                f"Regra: {result.rule_matched}\n"
                f"Razao: {result.reason}"
            )
        return result

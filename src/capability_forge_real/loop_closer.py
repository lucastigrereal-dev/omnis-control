"""Passo 5 / FIO 2 — LoopCloser: repetition → auto-propose → build → activate.

Chains RepetitionDetector (FIO 1) → CapabilityProposal → CapabilityBuilder
(with sandbox rail from FIO 4) → SkillCatalog activation (FIO 3).

Governance (Passo 5): risk is inferred from the candidate text.
- low  → auto-activates (no external side-effects)
- medium/high → build + validate but HOLD activation; pending_approval=True
                until a human explicitly approves.

When in doubt, risk is classified UP (medium), never down.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.capability_forge_real.models import (
    BuildState,
    CapabilityProposal,
    PROPOSAL_STATUS_APPROVED,
    IMPL_TYPE_CLI_WRAPPER,
)
from src.capability_forge_real.builder import CapabilityBuilder
from src.capability_forge_real.repetition_detector import RepetitionCandidate, RepetitionDetector

_SECTOR_KEYWORDS: list[tuple[list[str], str]] = [
    (["post", "caption", "carrossel", "reel", "content", "conteudo", "conteúdo", "viagem", "foto"], "midia"),
    (["hotel", "lead", "collab", "venda", "crm", "prospect", "cliente"], "comercial"),
    (["relatorio", "relatório", "report", "metric", "financi", "receita"], "financeiro"),
    (["agenda", "reuniao", "reunião", "tarefa", "schedule", "calendar"], "operacoes"),
]

# External communication / real-world effects → HIGH
_HIGH_RISK_PATTERNS = [
    "whatsapp", "telegram", "email", "sms",
    "enviar mensagem", "enviar email", "enviar sms", "send message",
    "publicar", "publish", "postar", "post to",
    "webhook", "http request", "api call", "chamada api",
    "notificar", "notify", "broadcast", "disparar",
]

# File I/O / database writes / deletions → MEDIUM
_MEDIUM_RISK_PATTERNS = [
    "salvar arquivo", "gravar arquivo", "escrever arquivo", "write file",
    "upload", "deletar", "delete", "remover arquivo", "remove file",
    "banco de dados", "database", "atualizar banco", "inserir banco",
    "criar conta", "create account", "modificar sistema",
]

# Pure local computation / read-only → LOW (explicit allowlist)
_LOW_RISK_PATTERNS = [
    "listar", "list", "buscar", "search",
    "calcular", "calculate", "transformar", "transform",
    "analisar", "analyze", "analisa", "ler", "read",
    "consultar", "query", "contar", "count",
    "criar post", "criar caption", "criar carrossel", "criar reel",
    "criar relatorio", "criar conteudo", "gerar conteudo",
    "gerar post", "gerar caption", "formatar", "classificar",
    "extrair", "resumir", "pontuar", "score", "qualificar lead",
    "criar resumo", "criar script",
]


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.lower()).strip("_")


def _infer_sector(text: str) -> str:
    """Keyword-based sector inference from normalized request_text."""
    lower = text.lower()
    for keywords, sector in _SECTOR_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return sector
    return "automacao"


def _infer_risk(text: str) -> str:
    """Infer risk level from request_text.

    Conservative: when no explicit low-risk match, classify as MEDIUM.
    Order: HIGH check first, then MEDIUM, then explicit LOW allowlist, else MEDIUM.
    """
    lower = text.lower()
    if any(p in lower for p in _HIGH_RISK_PATTERNS):
        return "high"
    if any(p in lower for p in _MEDIUM_RISK_PATTERNS):
        return "medium"
    if any(p in lower for p in _LOW_RISK_PATTERNS):
        return "low"
    return "medium"  # conservative default — never assume low


@dataclass
class LoopResult:
    """Outcome of processing one RepetitionCandidate through the full loop."""

    candidate_text: str
    candidate_count: int
    cap_id: str | None = None
    proposal_id: str | None = None
    build_state: str | None = None
    activated_skill_id: str | None = None
    pending_approval: bool = False
    skipped: bool = False
    skip_reason: str = ""
    error: str = ""

    @property
    def succeeded(self) -> bool:
        return (
            self.build_state == "done"
            and not self.skipped
            and not self.error
            and not self.pending_approval
        )

    def to_dict(self) -> dict:
        return {
            "candidate_text": self.candidate_text,
            "candidate_count": self.candidate_count,
            "cap_id": self.cap_id,
            "proposal_id": self.proposal_id,
            "build_state": self.build_state,
            "activated_skill_id": self.activated_skill_id,
            "pending_approval": self.pending_approval,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "error": self.error,
            "succeeded": self.succeeded,
        }


class LoopCloser:
    """End-to-end automation: detect repeated tasks → build new skill.

    Usage:
        closer = LoopCloser(runs_log=..., threshold=3, dry_run=True)
        results = closer.run()
        # one LoopResult per candidate
    """

    def __init__(
        self,
        runs_log: Optional[Path] = None,
        threshold: int = 3,
        dry_run: bool = True,
        caps_path: Optional[Path] = None,
        proposals_log: Optional[Path] = None,
    ):
        from src.skill_matcher.loader import DEFAULT_CONFIG_PATH

        self.runs_log = runs_log
        self.threshold = threshold
        self.dry_run = dry_run
        self.caps_path = caps_path or DEFAULT_CONFIG_PATH
        self.proposals_log = proposals_log

    def run(self) -> list[LoopResult]:
        """Detect repetitions and attempt to build a skill for each candidate."""
        detector = RepetitionDetector(runs_log=self.runs_log, threshold=self.threshold)
        candidates = detector.detect()
        return [self._process(c) for c in candidates]

    def _process(self, candidate: RepetitionCandidate) -> LoopResult:
        cap_id = _slug(candidate.normalized_text)
        result = LoopResult(
            candidate_text=candidate.original_text,
            candidate_count=candidate.count,
            cap_id=cap_id,
        )

        if not cap_id or len(cap_id) < 3:
            result.skipped = True
            result.skip_reason = "cap_id_too_short"
            return result

        if self._already_registered(cap_id):
            result.skipped = True
            result.skip_reason = "already_registered"
            return result

        try:
            proposal = CapabilityProposal.from_gap(
                gap_id=f"rep_{cap_id[:8]}",
                capability_name=cap_id,
                sector=_infer_sector(candidate.normalized_text),
                desired_output=f"Automate: {candidate.original_text}",
                risk_level=_infer_risk(candidate.normalized_text),
                implementation_type=IMPL_TYPE_CLI_WRAPPER,
            )
            proposal.status = PROPOSAL_STATUS_APPROVED
            result.proposal_id = proposal.proposal_id

            if not self.dry_run:
                from src.capability_forge_real.store import ProposalStore
                ProposalStore(self.proposals_log).save(proposal)
        except Exception as exc:
            result.error = f"proposal: {exc}"
            return result

        try:
            build_result = CapabilityBuilder(dry_run=self.dry_run).build(proposal)
            result.build_state = build_result.state
            result.activated_skill_id = build_result.activated_skill_id
            if proposal.approval_required and build_result.state == BuildState.DONE.value:
                result.pending_approval = True
        except Exception as exc:
            result.error = f"build: {exc}"
            return result

        return result

    def _already_registered(self, cap_id: str) -> bool:
        """True if cap_id already exists in capabilities.yaml."""
        if not self.caps_path.exists():
            return False
        try:
            import yaml
            raw = yaml.safe_load(self.caps_path.read_text(encoding="utf-8")) or {}
            return cap_id in raw.get("capabilities", {})
        except Exception:
            return False

"""P15 Computer Ops service — planner, audit plans, classification, cleanup plans."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.computer_ops.models import (
    AuditTarget,
    DiskFinding,
    ProjectFinding,
    DockerFinding,
    CleanupCandidate,
    ComputerOpsReport,
    TARGET_DISK,
    TARGET_PROJECT,
    TARGET_DOCKER,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
    SEVERITY_CRITICAL,
    ACTION_QUARANTINE,
    ACTION_ARCHIVE,
    ACTION_KEEP,
    ACTION_REVIEW,
    ACTION_DELETE,
    SAFE_ACTIONS,
    DESTRUCTIVE_ACTIONS,
    STATUS_CLASSIFIED,
    STATUS_QUARANTINED,
    VALID_TARGETS,
    VALID_ACTIONS,
)
from src.computer_ops.errors import (
    AuditPlanError,
    EmptyTargetListError,
    InvalidTargetTypeError,
    ClassificationError,
    DestructiveActionBlockedError,
    SafetyViolationError,
    QuarantineRequiredError,
    CleanupPlanError,
    AlreadyCleanedError,
)


@dataclass
class AuditPlan:
    """Plano de auditoria read-only — descreve O QUE auditar, sem executar."""
    plan_id: str
    targets: list[AuditTarget] = field(default_factory=list)
    estimated_steps: int = 0
    safety_rules: list[str] = field(default_factory=list)
    dry_run: bool = True

    @property
    def is_empty(self) -> bool:
        return len(self.targets) == 0


@dataclass
class ClassificationResult:
    """Resultado da classificacao de um candidato a limpeza."""
    candidate: CleanupCandidate
    is_safe: bool
    requires_review: bool
    blocked_actions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class SafeCleanupPlan:
    """Plano de limpeza segura — quarentena, revisao, sem acoes destrutivas."""
    plan_id: str
    candidates: list[CleanupCandidate] = field(default_factory=list)
    total_size_bytes: int = 0
    phases: list[dict] = field(default_factory=list)
    requires_approval: bool = True
    notes: list[str] = field(default_factory=list)

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)


# ── Computer Ops Planner ──────────────────────────────────────────────────

class ComputerOpsPlanner:
    """Planejador deterministico de operacoes de computador — read-only."""

    def build_plan(self, targets: list[AuditTarget]) -> AuditPlan:
        """Constroi plano de auditoria a partir de alvos."""
        if not targets:
            raise EmptyTargetListError("Lista de alvos nao pode ser vazia")

        for t in targets:
            if t.target_type not in VALID_TARGETS:
                raise InvalidTargetTypeError(
                    f"Tipo invalido: {t.target_type!r} no alvo {t.target_id}"
                )

        enabled = [t for t in targets if t.enabled]

        return AuditPlan(
            plan_id=f"audit_{len(targets)}_targets",
            targets=enabled,
            estimated_steps=len(enabled) * 3,  # scan + analyze + report
            safety_rules=[
                "read_only_scan",
                "no_modifications",
                "dry_run_default",
                "quarantine_first",
            ],
            dry_run=True,
        )

    def build_report(self, title: str, description: str) -> ComputerOpsReport:
        """Cria relatorio vazio pronto para agregacao."""
        return ComputerOpsReport.new(title, description)


def build_readonly_audit_plan(targets: list[AuditTarget]) -> AuditPlan:
    """Funcao de conveniencia: constroi plano de auditoria read-only."""
    planner = ComputerOpsPlanner()
    return planner.build_plan(targets)


# ── Classification ────────────────────────────────────────────────────────

def classify_cleanup_candidate(candidate: CleanupCandidate) -> ClassificationResult:
    """Classifica candidato a limpeza aplicando regras de seguranca.

    Regras:
    1. DELETE nunca permitido sem quarentena previa
    2. Candidatos > 1GB requerem revisao humana
    3. Candidatos sem days_since_accessed requerem revisao
    """
    blocked: list[str] = []
    warnings: list[str] = []
    is_safe = True
    requires_review = False  # comeca limpo, so sobe se houver motivo

    # Regra 1: DELETE bloqueado sem quarentena
    if candidate.recommended_action == ACTION_DELETE:
        if candidate.status != STATUS_QUARANTINED:
            blocked.append(ACTION_DELETE)
            warnings.append("DELETE requer status QUARANTINED primeiro. Sugerindo QUARANTINE.")
            candidate.recommended_action = ACTION_QUARANTINE
            is_safe = False

    # Regra 2: Candidatos grandes requerem revisao
    if candidate.size_bytes > 1_073_741_824:  # 1 GB
        requires_review = True
        warnings.append("Candidato > 1GB requer revisao humana obrigatoria")

    # Regra 3: Sem dados de acesso = requer revisao
    if candidate.days_since_accessed is None:
        requires_review = True
        warnings.append("Sem dados de ultimo acesso — requer revisao manual")

    # Regra 4: Acao destrutiva detectada
    if candidate.recommended_action in DESTRUCTIVE_ACTIONS:
        blocked.append(candidate.recommended_action)
        is_safe = False
        warnings.append(
            f"Acao {candidate.recommended_action!r} bloqueada. "
            f"Use {ACTION_QUARANTINE!r} ou {ACTION_ARCHIVE!r} primeiro."
        )

    candidate.mark_classified(is_safe, requires_review)

    return ClassificationResult(
        candidate=candidate,
        is_safe=is_safe,
        requires_review=requires_review,
        blocked_actions=blocked,
        warnings=warnings,
    )


# ── Safe Cleanup Plan ─────────────────────────────────────────────────────

def generate_safe_cleanup_plan(
    candidates: list[CleanupCandidate],
    report: Optional[ComputerOpsReport] = None,
) -> SafeCleanupPlan:
    """Gera plano de limpeza segura em 3 fases.

    Fase 1 — CLASSIFICAR: classificar cada candidato
    Fase 2 — QUARENTENAR: mover para quarentena (sem delete)
    Fase 3 — REVISAR: aguardar aprovacao humana

    NUNCA executa delete. NUNCA modifica arquivos reais.
    """
    if not candidates:
        raise CleanupPlanError("Lista de candidatos vazia")

    notes: list[str] = []
    processed: list[CleanupCandidate] = []
    total_size = 0

    # Fase 1: Classificar
    for c in candidates:
        if c.status == STATUS_CLASSIFIED:
            notes.append(f"{c.candidate_id}: ja classificado, pulando")
            processed.append(c)
            total_size += c.size_bytes
            continue

        result = classify_cleanup_candidate(c)
        processed.append(result.candidate)
        total_size += c.size_bytes
        if result.warnings:
            for w in result.warnings:
                notes.append(f"{c.candidate_id}: {w}")

    # Fase 2: Sugerir quarentena (sem executar)
    quarantine_phase = {
        "phase": "quarantine",
        "action": "Mover candidatos para diretorio de quarentena",
        "dry_run": True,
        "note": "NENHUM ARQUIVO SERA MOVIDO — apenas planejamento",
        "candidate_count": len(processed),
        "total_size_bytes": total_size,
    }

    # Fase 3: Revisao humana
    review_phase = {
        "phase": "review",
        "action": "Aguardar aprovacao humana para cada candidato",
        "requires": "Aprovacao explicita do operador",
        "candidates_requiring_review": [
            c.candidate_id for c in processed if c.requires_review
        ],
    }

    plan = SafeCleanupPlan(
        plan_id=f"cleanup_{len(processed)}_candidates",
        candidates=processed,
        total_size_bytes=total_size,
        phases=[quarantine_phase, review_phase],
        requires_approval=True,
        notes=notes,
    )

    return plan

"""ApprovalGate runtime — avalia risco, mostra pacote, aguarda input humano."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.governance.models import (
    ACTION_WRITE,
    ACTION_SEND,
    ACTION_DEPLOY,
    RISK_HIGH,
    RISK_CRITICAL,
    VERDICT_APPROVED,
    VERDICT_DENIED,
    VERDICT_REQUIRES_APPROVAL,
    VALID_VERDICTS,
)
from src.governance.service import (
    RiskClassifier,
    ApprovalPolicyEngine,
    AuditLogPlanner,
    PolicyEvalResult,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


# ── auto-approval thresholds ───────────────────────────────────────────

AUTO_APPROVE_RISK = {"low", "medium"}
AUTO_DENY_RISK = {"critical"}

APPROVAL_GATE_VERSION = "1.0.0"


# ── models ─────────────────────────────────────────────────────────────

@dataclass
class ApprovalRequest:
    request_id: str = field(default_factory=lambda: f"APR-{_short_id()}")
    mission_id: str = ""
    summary: str = ""
    risk_level: str = "low"
    action_count: int = 0
    dry_run: bool = True
    requires_input: bool = False
    auto_verdict: str = ""
    reason: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "mission_id": self.mission_id,
            "summary": self.summary,
            "risk_level": self.risk_level,
            "action_count": self.action_count,
            "dry_run": self.dry_run,
            "requires_input": self.requires_input,
            "auto_verdict": self.auto_verdict,
            "reason": self.reason,
            "created_at": self.created_at,
        }

    def to_markdown(self) -> str:
        lines = [
            f"# Approval Request — {self.request_id}",
            f"**Missão:** {self.mission_id}",
            f"**Gerado em:** {self.created_at}",
            f"**Risco:** {self.risk_level}",
            f"**Ações:** {self.action_count}",
            f"**Modo:** {'dry-run' if self.dry_run else 'live'}",
            "",
            f"**Resumo:** {self.summary}",
            "",
        ]
        if self.auto_verdict:
            lines.append(f"**Veredito automático:** {self.auto_verdict}")
            lines.append(f"**Motivo:** {self.reason}")
        else:
            lines.append("**Status:** Aguardando aprovação do operador")
        return "\n".join(lines)


@dataclass
class ApprovalStatus:
    mission_id: str
    request_id: str
    verdict: str  # approved | denied | requires_approval
    approved_by: str = ""
    approved_at: str = ""
    reason: str = ""
    gate_version: str = APPROVAL_GATE_VERSION

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "request_id": self.request_id,
            "verdict": self.verdict,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "reason": self.reason,
            "gate_version": self.gate_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ApprovalStatus":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Approval gate ──────────────────────────────────────────────────────

class ApprovalGate:
    """Gate de aprovação runtime — avalia ações e decide se precisam de input humano."""

    def __init__(
        self,
        dry_run: bool = True,
        risk_classifier: Optional[RiskClassifier] = None,
        policy_engine: Optional[ApprovalPolicyEngine] = None,
        audit_planner: Optional[AuditLogPlanner] = None,
    ) -> None:
        self.dry_run = dry_run
        self.risk_classifier = risk_classifier or RiskClassifier()
        self.policy_engine = policy_engine or ApprovalPolicyEngine()
        self.audit = audit_planner or AuditLogPlanner()

    def evaluate(
        self,
        mission_id: str,
        summary: str,
        action_types: list[str],
        actor: str = "OMNIS",
    ) -> ApprovalRequest:
        """Avalia ações da missão e determina se precisa de aprovação."""
        if not action_types:
            return ApprovalRequest(
                mission_id=mission_id,
                summary=summary,
                risk_level="low",
                action_count=0,
                dry_run=self.dry_run,
                auto_verdict=VERDICT_APPROVED,
                reason="Nenhuma ação para avaliar",
            )

        # Classify each action
        action_count = len(action_types)
        worst_risk = "low"
        for at in action_types:
            level = self.risk_classifier.classify(at)
            if _risk_rank(level) > _risk_rank(worst_risk):
                worst_risk = level

        req = ApprovalRequest(
            mission_id=mission_id,
            summary=summary,
            risk_level=worst_risk,
            action_count=action_count,
            dry_run=self.dry_run,
        )

        # Dry-run always safe — auto approve
        if self.dry_run:
            req.auto_verdict = VERDICT_APPROVED
            req.reason = "Dry-run ativo — nenhuma ação real será executada"
            req.requires_input = False
            return req

        # Critical → auto deny
        if worst_risk == RISK_CRITICAL:
            req.auto_verdict = VERDICT_DENIED
            req.reason = "Ação de risco crítico — execução bloqueada automaticamente"
            req.requires_input = False
            return req

        # High risk → requires human input
        if worst_risk == RISK_HIGH:
            req.requires_input = True
            req.auto_verdict = VERDICT_REQUIRES_APPROVAL
            req.reason = "Ação de alto risco requer aprovação do operador"
            return req

        # Low/medium → evaluate against policies
        for at in action_types:
            level = self.risk_classifier.classify(at)
            result: PolicyEvalResult = self.policy_engine.evaluate(
                at, level, mission_id, actor
            )
            if result.verdict == VERDICT_DENIED:
                req.auto_verdict = VERDICT_DENIED
                req.reason = result.reason
                return req
            if result.requires_approval:
                req.requires_input = True
                req.auto_verdict = VERDICT_REQUIRES_APPROVAL
                req.reason = result.reason
                return req

        req.auto_verdict = VERDICT_APPROVED
        req.reason = "Todas as ações passaram pelos gates de segurança"
        return req

    def approve(self, request: ApprovalRequest, approved_by: str = "lucas") -> ApprovalStatus:
        """Aprova uma request e registra no audit log."""
        verdict = VERDICT_APPROVED
        if request.auto_verdict == VERDICT_DENIED:
            verdict = VERDICT_DENIED
        elif request.requires_input:
            verdict = VERDICT_APPROVED

        status = ApprovalStatus(
            mission_id=request.mission_id,
            request_id=request.request_id,
            verdict=verdict,
            approved_by=approved_by,
            approved_at=_now_iso(),
            reason=request.reason,
        )

        self.audit.record_event(
            action_type=ACTION_WRITE,
            risk_level=request.risk_level,
            target=request.mission_id,
            actor="approval_gate",
            verdict=verdict,
            approved_by=approved_by,
            details={"request": request.to_dict()},
        )

        self.audit.record_decision(
            action_type=ACTION_WRITE,
            risk_level=request.risk_level,
            target=request.mission_id,
            verdict=verdict,
            reason=request.reason,
            policy_id=None,
            audit_event_id=None,
        )

        return status

    def deny(self, request: ApprovalRequest, reason: str = "") -> ApprovalStatus:
        """Nega uma request e registra no audit log."""
        status = ApprovalStatus(
            mission_id=request.mission_id,
            request_id=request.request_id,
            verdict=VERDICT_DENIED,
            approved_by="",
            approved_at=_now_iso(),
            reason=reason or request.reason,
        )

        self.audit.record_event(
            action_type=ACTION_WRITE,
            risk_level=request.risk_level,
            target=request.mission_id,
            actor="approval_gate",
            verdict=VERDICT_DENIED,
            details={"request": request.to_dict()},
        )

        return status

    def write_approval_files(
        self,
        approval_path: Path,
        request: ApprovalRequest,
        status: ApprovalStatus,
    ) -> None:
        """Escreve approval_request.md e approval_status.json em 07_approval/."""
        approval_path.mkdir(parents=True, exist_ok=True)

        req_md = approval_path / "approval_request.md"
        req_md.write_text(request.to_markdown(), encoding="utf-8")

        status_json = approval_path / "approval_status.json"
        status_json.write_text(
            json.dumps(status.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# ── helpers ────────────────────────────────────────────────────────────

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _risk_rank(level: str) -> int:
    return _RISK_ORDER.get(level, 0)

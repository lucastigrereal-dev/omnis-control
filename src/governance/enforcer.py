"""GuardrailsEnforcer — intercepta ações no dispatcher baseado em score de risco."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.governance.models import (
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_CRITICAL,
    VERDICT_APPROVED,
    VERDICT_DENIED,
    VERDICT_REQUIRES_APPROVAL,
)
from src.governance.service import RiskClassifier


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── risk score mapping ─────────────────────────────────────────────────

RISK_SCORE: dict[str, int] = {
    RISK_LOW: 1,
    RISK_MEDIUM: 3,
    RISK_HIGH: 7,
    RISK_CRITICAL: 10,
}

# Score thresholds for enforcement
SCORE_AUTO_APPROVE = 3   # score ≤ 3 → auto approve
SCORE_NEEDS_APPROVAL = 7  # score ≥ 7 → needs approval
SCORE_AUTO_DENY = 10      # score = 10 → auto deny


# ── models ─────────────────────────────────────────────────────────────

@dataclass
class EnforcerVerdict:
    action_type: str
    risk_level: str
    score: int
    verdict: str  # approved | denied | requires_approval
    reason: str
    timestamp: str = field(default_factory=_now_iso)

    @property
    def blocked(self) -> bool:
        return self.verdict == VERDICT_DENIED

    @property
    def needs_approval(self) -> bool:
        return self.verdict == VERDICT_REQUIRES_APPROVAL

    @property
    def allowed(self) -> bool:
        return self.verdict == VERDICT_APPROVED

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "risk_level": self.risk_level,
            "score": self.score,
            "verdict": self.verdict,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


# ── enforcer ───────────────────────────────────────────────────────────

class GuardrailsEnforcer:
    """Intercepta ações no dispatcher com base no score de risco."""

    def __init__(self, classifier: RiskClassifier | None = None) -> None:
        self.classifier = classifier or RiskClassifier()
        self.log: list[EnforcerVerdict] = []

    def evaluate(self, action_type: str) -> EnforcerVerdict:
        """Avalia uma ação e retorna veredito."""
        risk_level = self.classifier.classify(action_type)
        score = RISK_SCORE.get(risk_level, 3)

        if score >= SCORE_AUTO_DENY:
            verdict = EnforcerVerdict(
                action_type=action_type,
                risk_level=risk_level,
                score=score,
                verdict=VERDICT_DENIED,
                reason=f"Ação '{action_type}' tem risco '{risk_level}' (score={score}) — bloqueada automaticamente",
            )
        elif score >= SCORE_NEEDS_APPROVAL:
            verdict = EnforcerVerdict(
                action_type=action_type,
                risk_level=risk_level,
                score=score,
                verdict=VERDICT_REQUIRES_APPROVAL,
                reason=f"Ação '{action_type}' tem risco '{risk_level}' (score={score}) — requer aprovação",
            )
        else:
            verdict = EnforcerVerdict(
                action_type=action_type,
                risk_level=risk_level,
                score=score,
                verdict=VERDICT_APPROVED,
                reason=f"Ação '{action_type}' tem risco '{risk_level}' (score={score}) — permitida",
            )

        self.log.append(verdict)
        return verdict

    def evaluate_batch(self, action_types: list[str]) -> list[EnforcerVerdict]:
        """Avalia múltiplas ações — pior score dita o bloqueio mais restritivo."""
        return [self.evaluate(at) for at in action_types]

    def worst_verdict(self, action_types: list[str]) -> EnforcerVerdict:
        """Retorna o veredito mais restritivo para uma lista de ações."""
        if not action_types:
            return EnforcerVerdict(
                action_type="none",
                risk_level=RISK_LOW,
                score=0,
                verdict=VERDICT_APPROVED,
                reason="Nenhuma ação para avaliar",
            )

        verdicts = self.evaluate_batch(action_types)
        worst = verdicts[0]
        for v in verdicts[1:]:
            if v.score > worst.score:
                worst = v
        return worst

    def clear_log(self) -> None:
        self.log.clear()

    @property
    def log_count(self) -> int:
        return len(self.log)

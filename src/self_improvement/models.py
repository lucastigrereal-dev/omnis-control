"""P28 Self-Improvement Loop — core models."""
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


# ── Feedback source types ─────────────────────────────────────────
SOURCE_MISSION = "mission"
SOURCE_BUILD = "build"
SOURCE_ACTION = "action"
SOURCE_SYSTEM = "system"
SOURCE_TYPES = [SOURCE_MISSION, SOURCE_BUILD, SOURCE_ACTION, SOURCE_SYSTEM]

# ── Proposal categories ───────────────────────────────────────────
CATEGORY_CAPABILITY_GAP = "capability_gap"
CATEGORY_PERFORMANCE = "performance"
CATEGORY_RELIABILITY = "reliability"
CATEGORY_COST = "cost"
CATEGORY_SECURITY = "security"
PROPOSAL_CATEGORIES = [CATEGORY_CAPABILITY_GAP, CATEGORY_PERFORMANCE, CATEGORY_RELIABILITY, CATEGORY_COST, CATEGORY_SECURITY]

# ── Severities ────────────────────────────────────────────────────
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"

# ── Implementation types ──────────────────────────────────────────
IMPL_CODE_CHANGE = "code_change"
IMPL_CONFIG_CHANGE = "config_change"
IMPL_NEW_CAPABILITY = "new_capability"
IMPL_PROCESS_CHANGE = "process_change"

# ── Proposal statuses ─────────────────────────────────────────────
PROPOSAL_DRAFT = "draft"
PROPOSAL_PROPOSED = "proposed"
PROPOSAL_APPROVED = "approved"
PROPOSAL_REJECTED = "rejected"
PROPOSAL_IMPLEMENTED = "implemented"
PROPOSAL_MEASURED = "measured"
PROPOSAL_ROLLED_BACK = "rolled_back"

# ── Measurement verdicts ──────────────────────────────────────────
VERDICT_IMPROVED = "improved"
VERDICT_DEGRADED = "degraded"
VERDICT_NEUTRAL = "neutral"
VERDICT_INSUFFICIENT_DATA = "insufficient_data"


# ── ExecutionFeedback ─────────────────────────────────────────────

@dataclass
class ExecutionFeedback:
    feedback_id: str
    source_type: str
    source_id: str
    status: str = "success"
    step_results: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    latency_ms: int = 0
    model_used: str = ""
    collected_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, source_type: str, source_id: str, status: str = "success",
            errors: Optional[list[str]] = None, warnings: Optional[list[str]] = None,
            latency_ms: int = 0, model_used: str = "",
            step_results: Optional[list[dict]] = None) -> "ExecutionFeedback":
        return cls(
            feedback_id=_short_id("sif"), source_type=source_type, source_id=source_id,
            status=status, step_results=step_results or [],
            errors=errors or [], warnings=warnings or [],
            latency_ms=latency_ms, model_used=model_used,
        )

    @classmethod
    def from_mission_report(cls, report: dict) -> "ExecutionFeedback":
        return cls.new(SOURCE_MISSION, report.get("mission_id", ""),
                       status=report.get("status", "success"),
                       errors=report.get("errors", []),
                       latency_ms=report.get("latency_ms", 0))

    @classmethod
    def from_build_result(cls, build: dict) -> "ExecutionFeedback":
        return cls.new(SOURCE_BUILD, build.get("build_id", ""),
                       status="success" if build.get("is_complete") else "failure",
                       errors=build.get("errors", []))

    @classmethod
    def from_action_result(cls, result: dict) -> "ExecutionFeedback":
        return cls.new(SOURCE_ACTION, result.get("result_id", ""),
                       status=result.get("status", "failure"),
                       errors=[result.get("error")] if result.get("error") else [],
                       latency_ms=result.get("latency_ms", 0))

    def to_dict(self) -> dict:
        return {
            "feedback_id": self.feedback_id, "source_type": self.source_type,
            "source_id": self.source_id, "status": self.status,
            "step_results": self.step_results, "errors": self.errors,
            "warnings": self.warnings, "latency_ms": self.latency_ms,
            "model_used": self.model_used, "collected_at": self.collected_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ExecutionFeedback":
        return cls(
            feedback_id=d.get("feedback_id", ""), source_type=d.get("source_type", ""),
            source_id=d.get("source_id", ""), status=d.get("status", "success"),
            step_results=d.get("step_results", []), errors=d.get("errors", []),
            warnings=d.get("warnings", []), latency_ms=d.get("latency_ms", 0),
            model_used=d.get("model_used", ""), collected_at=d.get("collected_at", ""),
        )

    @property
    def is_failure(self) -> bool:
        return self.status in ("failure", "partial_success")

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


# ── ImprovementProposal ───────────────────────────────────────────

@dataclass
class ImprovementProposal:
    proposal_id: str
    title: str
    category: str = CATEGORY_CAPABILITY_GAP
    severity: str = SEVERITY_MEDIUM
    evidence: list[str] = field(default_factory=list)
    current_state: str = ""
    proposed_change: str = ""
    expected_impact: str = ""
    implementation_type: str = IMPL_CODE_CHANGE
    auto_implementable: bool = False
    status: str = PROPOSAL_DRAFT
    approved_by: str = ""
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, title: str, category: str = CATEGORY_CAPABILITY_GAP,
            severity: str = SEVERITY_MEDIUM, current_state: str = "",
            proposed_change: str = "", expected_impact: str = "",
            implementation_type: str = IMPL_CODE_CHANGE,
            auto_implementable: bool = False,
            evidence: Optional[list[str]] = None) -> "ImprovementProposal":
        return cls(
            proposal_id=_short_id("sip"), title=title, category=category,
            severity=severity, evidence=evidence or [],
            current_state=current_state, proposed_change=proposed_change,
            expected_impact=expected_impact, implementation_type=implementation_type,
            auto_implementable=auto_implementable,
        )

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id, "title": self.title,
            "category": self.category, "severity": self.severity,
            "evidence": self.evidence, "current_state": self.current_state,
            "proposed_change": self.proposed_change,
            "expected_impact": self.expected_impact,
            "implementation_type": self.implementation_type,
            "auto_implementable": self.auto_implementable,
            "status": self.status, "approved_by": self.approved_by,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ImprovementProposal":
        return cls(
            proposal_id=d.get("proposal_id", ""), title=d.get("title", ""),
            category=d.get("category", CATEGORY_CAPABILITY_GAP),
            severity=d.get("severity", SEVERITY_MEDIUM),
            evidence=d.get("evidence", []), current_state=d.get("current_state", ""),
            proposed_change=d.get("proposed_change", ""),
            expected_impact=d.get("expected_impact", ""),
            implementation_type=d.get("implementation_type", IMPL_CODE_CHANGE),
            auto_implementable=d.get("auto_implementable", False),
            status=d.get("status", PROPOSAL_DRAFT),
            approved_by=d.get("approved_by", ""),
            created_at=d.get("created_at", ""),
        )

    @property
    def is_actionable(self) -> bool:
        return bool(self.proposed_change and self.implementation_type)


# ── ImpactMeasurement ─────────────────────────────────────────────

@dataclass
class ImpactMeasurement:
    measurement_id: str
    proposal_id: str
    metric: str = ""
    value_before: float = 0.0
    value_after: float = 0.0
    delta: float = 0.0
    verdict: str = VERDICT_INSUFFICIENT_DATA
    sample_size: int = 0
    measured_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, proposal_id: str, metric: str = "",
            value_before: float = 0.0, value_after: float = 0.0,
            verdict: str = VERDICT_INSUFFICIENT_DATA,
            sample_size: int = 0) -> "ImpactMeasurement":
        return cls(
            measurement_id=_short_id("sim"), proposal_id=proposal_id,
            metric=metric, value_before=value_before, value_after=value_after,
            delta=value_after - value_before, verdict=verdict,
            sample_size=sample_size,
        )

    def to_dict(self) -> dict:
        return {
            "measurement_id": self.measurement_id, "proposal_id": self.proposal_id,
            "metric": self.metric, "value_before": self.value_before,
            "value_after": self.value_after, "delta": self.delta,
            "verdict": self.verdict, "sample_size": self.sample_size,
            "measured_at": self.measured_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ImprovementProposal":
        return cls(
            measurement_id=d.get("measurement_id", ""), proposal_id=d.get("proposal_id", ""),
            metric=d.get("metric", ""), value_before=d.get("value_before", 0.0),
            value_after=d.get("value_after", 0.0), delta=d.get("delta", 0.0),
            verdict=d.get("verdict", VERDICT_INSUFFICIENT_DATA),
            sample_size=d.get("sample_size", 0), measured_at=d.get("measured_at", ""),
        )

    @property
    def is_improvement(self) -> bool:
        return self.verdict == VERDICT_IMPROVED

    @property
    def is_degradation(self) -> bool:
        return self.verdict == VERDICT_DEGRADED


# ── Pattern ───────────────────────────────────────────────────────

@dataclass
class Pattern:
    pattern_id: str
    name: str
    category: str = ""
    description: str = ""
    occurrences: int = 0
    related_feedback_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    detected_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, name: str, category: str = "", description: str = "",
            occurrences: int = 1, related_feedback_ids: Optional[list[str]] = None,
            confidence: float = 0.5) -> "Pattern":
        return cls(
            pattern_id=_short_id("sipn"), name=name, category=category,
            description=description, occurrences=occurrences,
            related_feedback_ids=related_feedback_ids or [], confidence=confidence,
        )

    def to_dict(self) -> dict:
        return {
            "pattern_id": self.pattern_id, "name": self.name,
            "category": self.category, "description": self.description,
            "occurrences": self.occurrences,
            "related_feedback_ids": self.related_feedback_ids,
            "confidence": self.confidence, "detected_at": self.detected_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Pattern":
        return cls(
            pattern_id=d.get("pattern_id", ""), name=d.get("name", ""),
            category=d.get("category", ""), description=d.get("description", ""),
            occurrences=d.get("occurrences", 0),
            related_feedback_ids=d.get("related_feedback_ids", []),
            confidence=d.get("confidence", 0.0), detected_at=d.get("detected_at", ""),
        )


# ── PrioritizedGap ────────────────────────────────────────────────

@dataclass
class PrioritizedGap:
    gap_id: str
    pattern: Pattern
    score: float = 0.0
    impact_estimate: str = ""
    urgency: str = SEVERITY_MEDIUM
    rank: int = 0

    @classmethod
    def new(cls, pattern: Pattern, score: float = 0.0,
            impact_estimate: str = "", urgency: str = SEVERITY_MEDIUM) -> "PrioritizedGap":
        return cls(
            gap_id=_short_id("sig"), pattern=pattern, score=score,
            impact_estimate=impact_estimate, urgency=urgency,
        )

    def to_dict(self) -> dict:
        return {
            "gap_id": self.gap_id, "pattern": self.pattern.to_dict(),
            "score": self.score, "impact_estimate": self.impact_estimate,
            "urgency": self.urgency, "rank": self.rank,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PrioritizedGap":
        pattern_data = d.get("pattern", {})
        pattern = Pattern.from_dict(pattern_data) if isinstance(pattern_data, dict) else Pattern.new("unknown")
        return cls(
            gap_id=d.get("gap_id", ""), pattern=pattern,
            score=d.get("score", 0.0), impact_estimate=d.get("impact_estimate", ""),
            urgency=d.get("urgency", SEVERITY_MEDIUM), rank=d.get("rank", 0),
        )

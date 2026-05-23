"""SkillRunnerBridge — conecta TaskDispatcher entries ao SkillSelector + execução."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.agentic.task_dispatcher import DispatchEntry, DispatchPlan
from src.skills_bridge.adapter import MockSkillAdapter, RealSkillAdapter, SkillAdapter
from src.skills_bridge.models import SkillCall, SkillIntent
from src.skills_bridge.selection import SkillSelector


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── deliverable filename → search tags ─────────────────────────────────

_DELIVERABLE_TAG_HINTS: dict[str, list[str]] = {
    "legenda": ["seo", "caption", "instagram", "content", "social"],
    "caption": ["caption", "instagram", "content"],
    "carrossel": ["instagram", "carousel", "design", "content"],
    "calendario": ["calendar", "content", "planning", "instagram"],
    "hashtag": ["hashtag", "instagram", "seo"],
    "campaign": ["campaign", "marketing", "content"],
    "lead": ["crm", "sales", "leads", "pipeline"],
    "dm_sequence": ["sales", "dm", "outreach", "crm"],
    "proposta": ["sales", "proposal", "crm"],
    "pipeline": ["crm", "sales", "pipeline"],
    "outreach": ["sales", "outreach", "leads"],
    "follow_up": ["sales", "crm", "followup"],
    "prd": ["app", "factory", "development", "planning"],
    "schema": ["app", "factory", "database", "development"],
    "api_contract": ["app", "factory", "api", "development"],
    "test_plan": ["app", "factory", "testing", "development"],
    "package": ["app", "factory", "export", "development"],
    "audit": ["computer", "ops", "audit", "health"],
    "health": ["computer", "ops", "health", "monitoring"],
    "quarantine": ["computer", "ops", "quarantine", "cleanup"],
    "disk": ["computer", "ops", "disk", "audit"],
    "pricing": ["finance", "pricing", "revenue", "metrics"],
    "revenue": ["revenue", "finance", "tracking", "metrics"],
    "cost": ["finance", "cost", "metrics"],
    "roi": ["finance", "roi", "analytics", "metrics"],
}


def _resolve_tags(deliverable_name: str) -> list[str]:
    """Extrai tags de busca do nome do deliverable."""
    lower = deliverable_name.lower().replace("_", " ").replace("-", " ")
    for key, tags in _DELIVERABLE_TAG_HINTS.items():
        if key in lower:
            return tags
    return ["general", "ops"]


def _resolve_intent(deliverable_name: str) -> SkillIntent:
    """Infere intent a partir do deliverable."""
    lower = deliverable_name.lower()
    if any(w in lower for w in ["legenda", "caption", "carrossel", "calendario", "campaign", "dm_sequence", "proposta", "prd", "schema", "api_contract"]):
        return SkillIntent.CREATE
    if any(w in lower for w in ["lead", "pipeline", "audit", "health", "disk", "revenue", "cost", "roi", "package"]):
        return SkillIntent.READ
    if any(w in lower for w in ["hashtag", "test_plan", "quarantine"]):
        return SkillIntent.ANALYZE
    return SkillIntent.GENERATE


# ── result model ───────────────────────────────────────────────────────

@dataclass
class ExecutionResult:
    entry_id: str
    skill_id: str
    status: str  # success | failed | needs_review | dry_run
    output: str
    duration_ms: int = 0
    error: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "entry_id": self.entry_id,
            "skill_id": self.skill_id,
            "status": self.status,
            "output": self.output,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


# ── bridge ─────────────────────────────────────────────────────────────

class SkillRunnerBridge:
    """Conecta DispatchPlan entries ao SkillSelector e executa skills."""

    def __init__(self, dry_run: bool = True, adapter: SkillAdapter | None = None) -> None:
        self.dry_run = dry_run
        self.selector = SkillSelector(dry_run=dry_run)
        if adapter is not None:
            self.adapter = adapter
        elif dry_run:
            self.adapter = MockSkillAdapter(dry_run=True)
        else:
            self.adapter = RealSkillAdapter(dry_run=False)

    def execute_plan(self, plan: DispatchPlan) -> list[ExecutionResult]:
        """Executa todas as entries de um plano, atualizando status."""
        results: list[ExecutionResult] = []
        for entry in plan.entries:
            result = self.execute_entry(entry)
            results.append(result)
            entry.status = "done" if result.status in ("success", "dry_run") else "failed"
            entry.finished_at = _now_iso()
            entry.result_hint = result.output[:200]
        return results

    def execute_entry(self, entry: DispatchEntry) -> ExecutionResult:
        """Executa uma DispatchEntry: resolve skill, chama adapter, retorna resultado."""
        tags = _resolve_tags(entry.deliverable)
        intent = _resolve_intent(entry.deliverable)

        call = SkillCall(
            skill_id="",
            intent=intent,
            tags=tags,
            dry_run=self.dry_run or entry.dry_run,
        )

        selection = self.selector.select(call)
        call.skill_id = selection.skill_id

        if selection.requires_manual_review:
            return ExecutionResult(
                entry_id=entry.task_id,
                skill_id=selection.skill_id,
                status="needs_review",
                output=selection.reason,
            )

        response = self.adapter.call_skill(call)

        if call.dry_run or self.dry_run:
            return ExecutionResult(
                entry_id=entry.task_id,
                skill_id=selection.skill_id,
                status="dry_run",
                output=response.get("output", ""),
            )

        return ExecutionResult(
            entry_id=entry.task_id,
            skill_id=selection.skill_id,
            status=response.get("status", "failed"),
            output=response.get("output", ""),
        )

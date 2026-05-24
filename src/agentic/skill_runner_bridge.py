"""SkillRunnerBridge — conecta TaskDispatcher entries ao SkillSelector + execução.

Onda 8: com lego_registry opcional, roteia StepNodes diretamente para Legos reais
(via LegoCog.run) antes de cair no caminho skill/model tradicional.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from src.agentic.task_dispatcher import DispatchEntry, DispatchPlan
from src.skills_bridge.adapter import MockSkillAdapter, RealSkillAdapter, SkillAdapter
from src.skills_bridge.models import SkillCall, SkillIntent
from src.skills_bridge.selection import SkillSelector

if TYPE_CHECKING:
    from src.legos.registry import LegoRegistry

_logger = logging.getLogger("omnis.skill_runner_bridge")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Mapeamento de role_id → nome canônico no LegoRegistry
_ROLE_TO_LEGO: dict[str, str] = {
    "research_lead": "research_conductor",
    "research_conductor": "research_conductor",
    "code_executor": "code_executor",
    "developer": "code_executor",
    "channel_messenger": "channel_messenger",
    "messenger": "channel_messenger",
    "publisher": "channel_messenger",
    "video_processor": "video_processor",
    "video_editor": "video_processor",
    "browser_executor": "browser_executor",
    "browser": "browser_executor",
    "web_researcher": "browser_executor",
}


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
    """Conecta DispatchPlan entries ao SkillSelector e executa skills.

    Onda 8: quando lego_registry é fornecido, tenta rotear o entry para o Lego
    correto via LegoCog.run() antes de cair no caminho skill/model tradicional.
    """

    def __init__(
        self,
        dry_run: bool = True,
        adapter: SkillAdapter | None = None,
        lego_registry: "LegoRegistry | None" = None,
        run_context=None,
    ) -> None:
        self.dry_run = dry_run
        self.selector = SkillSelector(dry_run=dry_run)
        self.lego_registry = lego_registry
        self.run_context = run_context
        if adapter is not None:
            self.adapter = adapter
        elif dry_run:
            self.adapter = MockSkillAdapter(dry_run=True)
        else:
            self.adapter = RealSkillAdapter(dry_run=False)

    def _try_lego(self, entry: DispatchEntry) -> "ExecutionResult | None":
        """Tenta rotear o entry para um Lego via LegoCog.run().

        Retorna ExecutionResult se o executor mapeia para um lego registrado,
        None caso contrário (fall-through para o caminho skill/model).
        """
        if self.lego_registry is None:
            return None

        executor = entry.executor or ""
        lego_name = _ROLE_TO_LEGO.get(executor) or (
            executor if executor in self.lego_registry else None
        )
        if lego_name is None:
            return None

        lego = self.lego_registry.get(lego_name)
        if lego is None:
            return None

        from src.legos.protocol import LegoCogSpec

        run_id = self.run_context.run_id if self.run_context is not None else ""
        is_dry = self.dry_run or bool(entry.dry_run)

        spec = LegoCogSpec(
            goal=entry.deliverable,
            dry_run=is_dry,
            run_id=run_id,
            payload={"executor": executor, "task_id": entry.task_id},
        )

        try:
            result = lego.run(spec)
            status = "dry_run" if is_dry else ("success" if result.success else "failed")
            _logger.info(
                "[bridge] lego:%s entry=%s status=%s run_id=%s",
                lego_name, entry.task_id, status, run_id or "none",
            )
            return ExecutionResult(
                entry_id=entry.task_id,
                skill_id=f"lego:{lego_name}",
                status=status,
                output=result.output,
                error=result.error,
            )
        except Exception as exc:
            _logger.error("[bridge] lego:%s failed: %s", lego_name, exc)
            return ExecutionResult(
                entry_id=entry.task_id,
                skill_id=f"lego:{lego_name}",
                status="failed",
                output="",
                error=str(exc)[:200],
            )

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
        """Executa uma DispatchEntry: tenta Lego primeiro, depois skill/model."""
        # Onda 8: Lego path — prioridade sobre skill catalog quando registry disponível
        lego_result = self._try_lego(entry)
        if lego_result is not None:
            return lego_result

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

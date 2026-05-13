"""P20 OMNIS Supreme Activation — Service layer."""
from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from src.omnis_supreme.models import (
    SupremeMission,
    SupremePlan,
    SupremeStatus,
    SupremeStep,
    _now_iso,
)
from src.omnis_supreme.errors import (
    UnknownIntentError,
    ExecutionError,
    StepAdapterError,
)
from src.omnis_supreme.adapters import ADAPTER_REGISTRY
from src.omnis_supreme.tracer import ObservabilityTracer


INTENT_PATTERNS: dict[str, list[str]] = {
    "create_campaign": [r"campanha", r"campaign", r"criar\s*campanha", r"briefing", r"marketing"],
    "publish_content": [r"publicar", r"postar", r"conteudo", r"conteúdo", r"publish", r"post"],
    "deliver_to_client": [r"entregar", r"cliente", r"delivery", r"entrega", r"enviar\s*ao\s*cliente"],
    "analyze_performance": [r"analisar", r"metricas", r"métricas", r"relatorio", r"relatório", r"performance", r"analytics", r"dashboard"],
    "commercial_outreach": [r"comercial", r"prospeccao", r"prospecção", r"vender", r"prospect", r"lead", r"sdr", r"venda"],
}

INTENT_TO_PIPELINE: dict[str, list[tuple[str, str]]] = {
    "create_campaign": [
        ("P5", "build_campaign_brief"),
        ("P19", "orchestrate_campaign"),
        ("P19", "allocate_budget"),
        ("P19", "build_publish_queue_plan"),
        ("P8", "validate_publish_readiness"),
        ("P17", "build_delivery_package"),
        ("P19", "generate_manifest"),
    ],
    "publish_content": [
        ("P8", "validate_publish_readiness"),
    ],
    "deliver_to_client": [
        ("P17", "build_delivery_package"),
    ],
    "analyze_performance": [
        ("P19", "calculate_roi"),
    ],
    "commercial_outreach": [
        ("P5", "build_campaign_brief"),
        ("P19", "orchestrate_campaign"),
    ],
}


class SupremeIntake:
    """Parses natural-language requests into classified SupremeMissions."""

    def parse(self, request: str) -> SupremeMission:
        intent = self._classify_intent(request)
        sector = self._classify_sector(intent)
        return SupremeMission.new(request_text=request, intent=intent, sector=sector)

    def _classify_intent(self, request: str) -> str:
        text = request.lower()
        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return intent
        raise UnknownIntentError(f"Cannot classify intent from: {request!r}")

    def _classify_sector(self, intent: str) -> str:
        return {
            "create_campaign": "comercial",
            "publish_content": "midia",
            "deliver_to_client": "vendas",
            "analyze_performance": "inteligencia",
            "commercial_outreach": "comercial",
        }.get(intent, "operacoes")


class SupremeContextBuilder:
    """Gathers multi-source context; degrades gracefully on source failures."""

    def build(self, intent: str) -> dict:
        ctx: dict = {"intent": intent, "sources": {}}
        ctx["sources"]["memory"] = self._fetch_memory(intent)
        ctx["sources"]["analytics"] = self._fetch_analytics(intent)
        ctx["sources"]["briefings"] = self._fetch_briefings(intent)
        ctx["warnings"] = []
        return ctx

    def _fetch_memory(self, intent: str) -> dict:
        try:
            from src.memory_pack.models import ContextPack
            return {"status": "ok", "hits": 0, "note": f"memory stub for {intent}"}
        except Exception as e:
            return {"status": "degraded", "error": str(e)}

    def _fetch_analytics(self, intent: str) -> dict:
        try:
            return {"status": "ok", "metrics": [], "note": f"analytics stub for {intent}"}
        except Exception as e:
            return {"status": "degraded", "error": str(e)}

    def _fetch_briefings(self, intent: str) -> dict:
        try:
            return {"status": "ok", "briefings": [], "note": f"briefings stub for {intent}"}
        except Exception as e:
            return {"status": "degraded", "error": str(e)}


class SupremePlanner:
    """Decomposes a mission into ordered steps with dependency edges."""

    def plan(self, mission: SupremeMission) -> SupremePlan:
        pipeline = INTENT_TO_PIPELINE.get(mission.intent, [])
        steps = self._build_steps(pipeline)
        edges = self._build_edges(steps)
        sorted_steps = self._topological_sort(steps, edges)
        modules = list({s.module_ref for s in sorted_steps})
        return SupremePlan.new(
            mission_id=mission.mission_id,
            steps=sorted_steps,
            edges=edges,
            selected_modules=modules,
            dry_run=mission.dry_run,
        )

    def _build_steps(self, pipeline: list[tuple[str, str]]) -> list[SupremeStep]:
        return [SupremeStep.new(module_ref=ref, operation=op) for ref, op in pipeline]

    def _build_edges(self, steps: list[SupremeStep]) -> list[tuple[str, str]]:
        edges: list[tuple[str, str]] = []
        for i in range(len(steps) - 1):
            edges.append((steps[i].step_id, steps[i + 1].step_id))
        return edges

    def _topological_sort(
        self, steps: list[SupremeStep], edges: list[tuple[str, str]]
    ) -> list[SupremeStep]:
        step_map = {s.step_id: s for s in steps}
        in_degree: dict[str, int] = {s.step_id: 0 for s in steps}
        adj: dict[str, list[str]] = {s.step_id: [] for s in steps}
        for src, dst in edges:
            if src in adj and dst in in_degree:
                adj[src].append(dst)
                in_degree[dst] += 1
        queue: deque[str] = deque(sid for sid, deg in in_degree.items() if deg == 0)
        result: list[SupremeStep] = []
        while queue:
            sid = queue.popleft()
            result.append(step_map[sid])
            for neighbor in adj.get(sid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(result) != len(steps):
            cycle_ids = set(step_map) - {s.step_id for s in result}
            from src.omnis_supreme.errors import PlanError
            raise PlanError(f"Cycle detected in step graph involving: {cycle_ids}")
        return result


class SupremeOrchestrator:
    """Top-level conductor — wires intake → context → plan → execute → report."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.intake = SupremeIntake()
        self.context_builder = SupremeContextBuilder()
        self.planner = SupremePlanner()
        self.executor = SupremeExecutor(dry_run=dry_run)

    def run(self, request: str) -> SupremeMission:
        mission = self.intake.parse(request)
        mission.transition_to(SupremeStatus.CONTEXT_BUILDING)
        mission.context = self.context_builder.build(mission.intent)
        mission.transition_to(SupremeStatus.PLANNING)
        plan = self.planner.plan(mission)
        mission.plan = plan
        mission.transition_to(SupremeStatus.DRY_RUN)
        dry_result = self.executor.dry_run(plan)
        mission.execution = dry_result
        if not self.dry_run:
            mission.transition_to(SupremeStatus.EXECUTING)
            result = self.executor.execute(plan)
            mission.execution = result.to_dict()
            mission.transition_to(SupremeStatus.COMPLETED)
            mission.completed_at = _now_iso()
        return mission


@dataclass
class ExecutionResult:
    mission_id: str
    steps: list[dict] = field(default_factory=list)
    status: str = "pending"
    trace: dict = field(default_factory=dict)
    started_at: str = ""
    completed_at: str = ""
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "steps": self.steps,
            "status": self.status,
            "trace": self.trace,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def new(cls, mission_id: str, dry_run: bool = True) -> "ExecutionResult":
        return cls(mission_id=mission_id, dry_run=dry_run, started_at=_now_iso())


class SupremeExecutor:
    """Coordinates step execution via ADAPTER_REGISTRY. No business logic."""

    MAX_RETRIES = 3

    def __init__(self, dry_run: bool = True):
        self._dry = dry_run

    def dry_run(self, plan: SupremePlan) -> dict:
        result = ExecutionResult.new(mission_id=plan.mission_id, dry_run=True)
        tracer = ObservabilityTracer(mission_id=plan.mission_id)
        context: dict = {}
        for step in plan.steps:
            span = tracer.start_span(step.step_id, step.operation)
            try:
                adapter_key = (step.module_ref, step.operation)
                if adapter_key not in ADAPTER_REGISTRY:
                    raise StepAdapterError(f"No adapter for {adapter_key}")
                step_result = {"simulated": True, "step_id": step.step_id, "module_ref": step.module_ref, "operation": step.operation}
                span.ok(step_result)
                result.steps.append({"step_id": step.step_id, "status": "dry_ok", "output": step_result})
                context[step.step_id] = step_result
            except Exception as e:
                span.fail(e)
                result.steps.append({"step_id": step.step_id, "status": "dry_blocked", "error": str(e)})
        result.trace = tracer.flush()
        result.status = "dry_complete"
        result.completed_at = _now_iso()
        return result.to_dict()

    def execute(self, plan: SupremePlan) -> ExecutionResult:
        result = ExecutionResult.new(mission_id=plan.mission_id, dry_run=False)
        tracer = ObservabilityTracer(mission_id=plan.mission_id)
        context: dict = {}
        for step in plan.steps:
            span = tracer.start_span(step.step_id, step.operation)
            step_result = self._execute_with_retry(step, context, span)
            if step_result is None:
                result.status = "failed"
                result.trace = tracer.flush()
                result.completed_at = _now_iso()
                return result
            result.steps.append(step_result)
            context[step.step_id] = step_result.get("output", {})
        result.trace = tracer.flush()
        result.status = "complete"
        result.completed_at = _now_iso()
        return result

    def execute_step(self, step: SupremeStep, context: dict) -> dict:
        adapter_key = (step.module_ref, step.operation)
        fn = ADAPTER_REGISTRY.get(adapter_key)
        if fn is None:
            raise StepAdapterError(f"No adapter registered for {adapter_key}")
        config = {**step.config, "dry_run": self._dry}
        output = fn(config, context)
        return {"step_id": step.step_id, "module_ref": step.module_ref, "operation": step.operation, "status": "ok", "output": output}

    def build_delivery(self, result: ExecutionResult) -> dict:
        last = result.steps[-1] if result.steps else {}
        return {"delivery_ref": last.get("step_id", ""), "status": result.status, "mission_id": result.mission_id}

    def _execute_with_retry(self, step: SupremeStep, context: dict, span) -> Optional[dict]:
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                step_result = self.execute_step(step, context)
                span.ok(step_result.get("output", {}))
                return step_result
            except Exception as e:
                step.retry_attempt = attempt
                if attempt == self.MAX_RETRIES:
                    span.fail(e)
                    return None
        return None

"""WorkflowRegistry — catálogo e health-check de todos os workflows OMNIS.

Onda 34 — 19 capacidades distintas:
  - DeepResearchWorkflow    (WF1)
  - VideoEditWorkflow       (WF2)
  - AppFactoryWorkflow      (WF3)
  - CodeRunWorkflow         (WF4)
  - SystemHealthWorkflow    (Onda 15)
  - LeadScoringWorkflow     (Onda 16)
  - ContentCalendarWorkflow   (Onda 17 + batch de O21)
  - SDRPipelineWorkflow       (consolida O18+O19+O22)
  - DailyBriefingWorkflow        (Onda 20)
  - ContentQualityWorkflow       (Onda 23)
  - MetricsSnapshotWorkflow      (Onda 24)
  - SquadAssignmentWorkflow      (Onda 25)
  - DeliverableMappingWorkflow   (Onda 26)
  - TaskDispatchWorkflow         (Onda 27)
  - CapabilityForgeWorkflow      (Onda 28)
  - SkillExecutionWorkflow       (Onda 29)
  - ContentBriefWorkflow         (Onda 34 — brief editorial via Ollama)
  - HotelPitchWorkflow           (Onda 33 — pitch collab PT-BR via Ollama)
  - CaptionGeneratorWorkflow     (Onda 32 — LLM real Ollama)

Removidos do registry (módulos permanecem como utilitários):
  - OutreachSequenceWorkflow  → subsumo por SDRPipelineWorkflow
  - SDRBatchWorkflow          → subsumo por SDRPipelineWorkflow
  - MultiAccountCalendarWorkflow → run_batch() em ContentCalendarWorkflow
  - SDRPlanWorkflow           → subsumo por SDRPipelineWorkflow
  - TaskClassificationWorkflow → utilitário (TaskClassifier)
  - CostTrackingWorkflow       → utilitário (CostTracker)

Papel: análogo ao LegoRegistry (Onda 5) — registra, descreve e verifica workflows.

API:
  registry.get("deep_research")   → WorkflowEntry
  registry.list_all()             → list[WorkflowEntry]
  registry.health_check_all()     → WorkflowHealthReport
  registry.run(name, **kwargs)    → resultado do workflow

Cada WorkflowEntry tem:
  name, version, description, cost_local_pct, dry_run_safe, tags
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

_logger = logging.getLogger("omnis.workflows.registry")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── WorkflowEntry ─────────────────────────────────────────────────────────────

@dataclass
class WorkflowEntry:
    """Descritor de um workflow registrado."""
    name: str
    version: str
    description: str
    cost_local_pct: int
    dry_run_safe: bool
    tags: list[str] = field(default_factory=list)
    factory: Callable[..., Any] | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "cost_local_pct": self.cost_local_pct,
            "dry_run_safe": self.dry_run_safe,
            "tags": self.tags,
        }


# ── WorkflowHealthReport ──────────────────────────────────────────────────────

@dataclass
class WorkflowHealthReport:
    """Relatório de saúde de todos os workflows registrados."""
    total: int
    importable: int
    failed: int
    entries: list[dict[str, Any]] = field(default_factory=list)
    checked_at: str = field(default_factory=_now_iso)

    @property
    def all_ok(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "importable": self.importable,
            "failed": self.failed,
            "all_ok": self.all_ok,
            "entries": self.entries,
            "checked_at": self.checked_at,
        }


# ── WorkflowRegistry ─────────────────────────────────────────────────────────

class WorkflowRegistry:
    """Catálogo e health-check de todos os workflows OMNIS.

    Usage:
        registry = WorkflowRegistry.default()
        entry = registry.get("deep_research")
        wf = entry.factory()
        result = wf.run(topic="IA em saúde", dry_run=True)
    """

    def __init__(self) -> None:
        self._entries: dict[str, WorkflowEntry] = {}

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, entry: WorkflowEntry) -> None:
        self._entries[entry.name] = entry

    def get(self, name: str) -> WorkflowEntry | None:
        return self._entries.get(name)

    def list_all(self) -> list[WorkflowEntry]:
        return list(self._entries.values())

    @property
    def names(self) -> list[str]:
        return list(self._entries.keys())

    @property
    def count(self) -> int:
        return len(self._entries)

    # ── Health check ─────────────────────────────────────────────────────────

    def health_check_all(self) -> WorkflowHealthReport:
        """Verifica se todos os workflows são importáveis e têm factory."""
        results: list[dict[str, Any]] = []
        importable = 0
        failed = 0

        for name, entry in self._entries.items():
            ok = entry.factory is not None
            status = "ok" if ok else "no_factory"
            if ok:
                importable += 1
            else:
                failed += 1
                _logger.warning("WorkflowRegistry: %s has no factory", name)
            results.append({"name": name, "status": status, **entry.to_dict()})

        return WorkflowHealthReport(
            total=len(self._entries),
            importable=importable,
            failed=failed,
            entries=results,
        )

    # ── Run ──────────────────────────────────────────────────────────────────

    def run(self, name: str, **kwargs: Any) -> Any:
        """Instancia e executa um workflow pelo nome."""
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Workflow '{name}' not registered")
        if entry.factory is None:
            raise RuntimeError(f"Workflow '{name}' has no factory")
        wf = entry.factory()
        return wf.run(**kwargs)

    # ── Default registry (todos os workflows Onda 10-12) ─────────────────────

    @classmethod
    def default(cls) -> "WorkflowRegistry":
        """Cria registry com os 12 workflows OMNIS padrão (Ondas 10-22)."""
        registry = cls()
        registry._register_defaults()
        return registry

    def _register_defaults(self) -> None:
        try:
            from src.workflows.deep_research_workflow import DeepResearchWorkflow
            self.register(WorkflowEntry(
                name="deep_research",
                version="1.0",
                description="Pesquisa profunda: tópico → STORM → citações → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["research", "storm", "ollama", "local"],
                factory=DeepResearchWorkflow,
            ))
        except ImportError as e:
            _logger.error("deep_research import failed: %s", e)
            self.register(WorkflowEntry(
                name="deep_research", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.video_edit_workflow import VideoEditWorkflow
            self.register(WorkflowEntry(
                name="video_edit",
                version="1.0",
                description="Edição de vídeo: MP4 → Whisper → SRT → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["video", "whisper", "ffmpeg", "local"],
                factory=VideoEditWorkflow,
            ))
        except ImportError as e:
            _logger.error("video_edit import failed: %s", e)
            self.register(WorkflowEntry(
                name="video_edit", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.app_factory_workflow import AppFactoryWorkflow
            self.register(WorkflowEntry(
                name="app_factory",
                version="1.0",
                description="App Factory: ideia → PRD + blueprint → artefato → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["app_factory", "prd", "deterministic", "local"],
                factory=AppFactoryWorkflow,
            ))
        except ImportError as e:
            _logger.error("app_factory import failed: %s", e)
            self.register(WorkflowEntry(
                name="app_factory", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.code_run_workflow import CodeRunWorkflow
            self.register(WorkflowEntry(
                name="code_run",
                version="1.0",
                description="Code run: goal → sandbox Python → output → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["code", "sandbox", "python", "local"],
                factory=CodeRunWorkflow,
            ))
        except ImportError as e:
            _logger.error("code_run import failed: %s", e)
            self.register(WorkflowEntry(
                name="code_run", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.system_health_workflow import SystemHealthWorkflow
            self.register(WorkflowEntry(
                name="system_health",
                version="1.0",
                description="Health snapshot: workflows + agências → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["health", "monitoring", "local"],
                factory=SystemHealthWorkflow,
            ))
        except ImportError as e:
            _logger.error("system_health import failed: %s", e)
            self.register(WorkflowEntry(
                name="system_health", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.lead_scoring_workflow import LeadScoringWorkflow
            self.register(WorkflowEntry(
                name="lead_scoring",
                version="1.0",
                description="Lead scoring: prospects → score deterministico → ranking → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["sdr", "scoring", "deterministic", "local"],
                factory=LeadScoringWorkflow,
            ))
        except ImportError as e:
            _logger.error("lead_scoring import failed: %s", e)
            self.register(WorkflowEntry(
                name="lead_scoring", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.content_calendar_workflow import ContentCalendarWorkflow
            self.register(WorkflowEntry(
                name="content_calendar",
                version="1.0",
                description="Calendário editorial: brief → QueueItems → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["content", "calendar", "queue", "local"],
                factory=ContentCalendarWorkflow,
            ))
        except ImportError as e:
            _logger.error("content_calendar import failed: %s", e)
            self.register(WorkflowEntry(
                name="content_calendar", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.sdr_pipeline_workflow import SDRPipelineWorkflow
            self.register(WorkflowEntry(
                name="sdr_pipeline",
                version="1.0",
                description="Pipeline SDR unificado: mode=execute (score+outreach) ou mode=plan (SDRPlan)",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["sdr", "pipeline", "outreach", "plan", "deterministic", "local"],
                factory=SDRPipelineWorkflow,
            ))
        except ImportError as e:
            _logger.error("sdr_pipeline import failed: %s", e)
            self.register(WorkflowEntry(
                name="sdr_pipeline", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.daily_briefing_workflow import DailyBriefingWorkflow
            self.register(WorkflowEntry(
                name="daily_briefing",
                version="1.0",
                description="Briefing matinal: health + leads + calendario → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["briefing", "composite", "morning", "local"],
                factory=DailyBriefingWorkflow,
            ))
        except ImportError as e:
            _logger.error("daily_briefing import failed: %s", e)
            self.register(WorkflowEntry(
                name="daily_briefing", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.content_quality_workflow import ContentQualityWorkflow
            self.register(WorkflowEntry(
                name="content_quality",
                version="1.0",
                description="Qualidade de conteúdo: N itens → QualityReport lote → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["quality", "scoring", "content", "local"],
                factory=ContentQualityWorkflow,
            ))
        except ImportError as e:
            _logger.error("content_quality import failed: %s", e)
            self.register(WorkflowEntry(
                name="content_quality", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.metrics_snapshot_workflow import MetricsSnapshotWorkflow
            self.register(WorkflowEntry(
                name="metrics_snapshot",
                version="1.0",
                description="Snapshot de métricas: MetricEvents + RunSummaries → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["metrics", "aggregation", "snapshot", "local"],
                factory=MetricsSnapshotWorkflow,
            ))
        except ImportError as e:
            _logger.error("metrics_snapshot import failed: %s", e)
            self.register(WorkflowEntry(
                name="metrics_snapshot", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.squad_assignment_workflow import SquadAssignmentWorkflow
            self.register(WorkflowEntry(
                name="squad_assignment",
                version="1.0",
                description="Atribuição de squads: N missões → SquadAssignment → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["squad", "assignment", "agentic", "local"],
                factory=SquadAssignmentWorkflow,
            ))
        except ImportError as e:
            _logger.error("squad_assignment import failed: %s", e)
            self.register(WorkflowEntry(
                name="squad_assignment", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.deliverable_mapping_workflow import DeliverableMappingWorkflow
            self.register(WorkflowEntry(
                name="deliverable_mapping",
                version="1.0",
                description="Mapping de deliverables: textos → intake → manifesto → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["deliverables", "intake", "mapping", "local"],
                factory=DeliverableMappingWorkflow,
            ))
        except ImportError as e:
            _logger.error("deliverable_mapping import failed: %s", e)
            self.register(WorkflowEntry(
                name="deliverable_mapping", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.task_dispatch_workflow import TaskDispatchWorkflow
            self.register(WorkflowEntry(
                name="task_dispatch",
                version="1.0",
                description="Despacho de tarefas: manifests → DispatchPlan lote → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["dispatch", "tasks", "executor", "local"],
                factory=TaskDispatchWorkflow,
            ))
        except ImportError as e:
            _logger.error("task_dispatch import failed: %s", e)
            self.register(WorkflowEntry(
                name="task_dispatch", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.capability_forge_workflow import CapabilityForgeWorkflow
            self.register(WorkflowEntry(
                name="capability_forge",
                version="1.0",
                description="Forge de capabilities: gaps → ForgeResult lote → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["forge", "gaps", "capability", "local"],
                factory=CapabilityForgeWorkflow,
            ))
        except ImportError as e:
            _logger.error("capability_forge import failed: %s", e)
            self.register(WorkflowEntry(
                name="capability_forge", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.skill_execution_workflow import SkillExecutionWorkflow
            self.register(WorkflowEntry(
                name="skill_execution",
                version="1.0",
                description="Execução de skills: DispatchPlan lote → SkillRunnerBridge → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["skills", "execution", "bridge", "local"],
                factory=SkillExecutionWorkflow,
            ))
        except ImportError as e:
            _logger.error("skill_execution import failed: %s", e)
            self.register(WorkflowEntry(
                name="skill_execution", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        # task_classification e cost_tracking removidos do registry (utilitários — ver módulos direto)

        try:
            from src.workflows.content_brief_workflow import ContentBriefWorkflow
            self.register(WorkflowEntry(
                name="content_brief",
                version="1.0",
                description="Brief editorial para pré-produção de conteúdo via Ollama (ângulo, pontos, dicas, hooks)",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["llm", "editorial", "brief", "ollama", "local", "instagram"],
                factory=ContentBriefWorkflow,
            ))
        except ImportError as e:
            _logger.error("content_brief import failed: %s", e)
            self.register(WorkflowEntry(
                name="content_brief", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.hotel_pitch_workflow import HotelPitchWorkflow
            self.register(WorkflowEntry(
                name="hotel_pitch",
                version="1.0",
                description="Pitch de collab para hotel via Ollama local (PT-BR personalizado por tier)",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["llm", "sdr", "hotel", "pitch", "ollama", "local"],
                factory=HotelPitchWorkflow,
            ))
        except ImportError as e:
            _logger.error("hotel_pitch import failed: %s", e)
            self.register(WorkflowEntry(
                name="hotel_pitch", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.caption_generator_workflow import CaptionGeneratorWorkflow
            self.register(WorkflowEntry(
                name="caption_generator",
                version="1.0",
                description="Geração de legenda Instagram via Ollama local (LLM real, custo zero)",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["llm", "instagram", "caption", "ollama", "local"],
                factory=CaptionGeneratorWorkflow,
            ))
        except ImportError as e:
            _logger.error("caption_generator import failed: %s", e)
            self.register(WorkflowEntry(
                name="caption_generator", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

"""WorkflowRegistry — catálogo e health-check de todos os workflows OMNIS.

Onda 13 (base) + Ondas 15-21 — cataloga 11 workflows:
  - DeepResearchWorkflow    (WF1)
  - VideoEditWorkflow       (WF2)
  - AppFactoryWorkflow      (WF3)
  - CodeRunWorkflow         (WF4)
  - SystemHealthWorkflow    (Onda 15)
  - LeadScoringWorkflow     (Onda 16)
  - ContentCalendarWorkflow   (Onda 17)
  - OutreachSequenceWorkflow  (Onda 18)
  - SDRBatchWorkflow          (Onda 19)
  - DailyBriefingWorkflow        (Onda 20)
  - MultiAccountCalendarWorkflow (Onda 21)

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
        """Cria registry com os 11 workflows OMNIS padrão (Ondas 10-21)."""
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
            from src.workflows.outreach_sequence_workflow import OutreachSequenceWorkflow
            self.register(WorkflowEntry(
                name="outreach_sequence",
                version="1.0",
                description="Outreach SDR: prospects → sequências 7-passos → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["sdr", "outreach", "sequence", "deterministic", "local"],
                factory=OutreachSequenceWorkflow,
            ))
        except ImportError as e:
            _logger.error("outreach_sequence import failed: %s", e)
            self.register(WorkflowEntry(
                name="outreach_sequence", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

        try:
            from src.workflows.sdr_batch_workflow import SDRBatchWorkflow
            self.register(WorkflowEntry(
                name="sdr_batch",
                version="1.0",
                description="Pipeline SDR: prospects → score → outreach HOT+WARM → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["sdr", "batch", "pipeline", "deterministic", "local"],
                factory=SDRBatchWorkflow,
            ))
        except ImportError as e:
            _logger.error("sdr_batch import failed: %s", e)
            self.register(WorkflowEntry(
                name="sdr_batch", version="1.0",
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
            from src.workflows.multi_account_calendar_workflow import MultiAccountCalendarWorkflow
            self.register(WorkflowEntry(
                name="multi_account_calendar",
                version="1.0",
                description="Batch de calendários: N contas → QueueItems → akasha",
                cost_local_pct=100,
                dry_run_safe=True,
                tags=["content", "calendar", "batch", "multi-account", "local"],
                factory=MultiAccountCalendarWorkflow,
            ))
        except ImportError as e:
            _logger.error("multi_account_calendar import failed: %s", e)
            self.register(WorkflowEntry(
                name="multi_account_calendar", version="1.0",
                description="import failed",
                cost_local_pct=0, dry_run_safe=False,
            ))

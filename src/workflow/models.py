"""Modelos do Workflow Engine."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


class WorkflowStage:
    """Estágios do pipeline de conteúdo."""
    IDEA = "idea"
    PLAN = "plan"
    BRIEF = "brief"
    PRODUCE = "produce"
    DRAFT = "draft"
    APPROVE = "approve"
    QUEUE = "queue"
    PUBLISH = "publish"


class WorkflowStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class WorkflowResult:
    """Resultado de uma execução do workflow."""
    workflow_id: str
    topic: str
    pagina: str
    formato: str
    stages: dict[str, str]  # stage -> status
    queue_id: Optional[str] = None
    draft_id: Optional[str] = None
    job_id: Optional[str] = None
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda:
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    def is_complete(self) -> bool:
        return all(s == WorkflowStatus.SUCCESS for s in self.stages.values())

    def summary(self) -> str:
        lines = [f"Workflow: {self.workflow_id[:8]} ({self.topic})"]
        for stage, status in self.stages.items():
            icon = {"success": "✅", "failed": "❌", "running": "⏳",
                    "pending": "⬜", "skipped": "⏭️", "blocked": "🚫"}
            lines.append(f"  {icon.get(status, '❓')} {stage}: {status}")
        if self.errors:
            lines.append(f"  Erros: {len(self.errors)}")
        return "\n".join(lines)

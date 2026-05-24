"""TaskClassificationWorkflow — Onda 30.

Wraps TaskClassifier.classify_batch() for batch intent classification:
  intent list → TaskClassifier → TaskClass list → Akasha
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass

from src.multi_model_orchestration.classifier import TaskClassifier
from src.multi_model_orchestration.models import TaskClass
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkEvent


def _run_id() -> str:
    return secrets.token_hex(6)


@dataclass
class ClassifiedTask:
    intent: str
    risk_level: str
    task_class: TaskClass

    @property
    def complexity(self) -> str:
        return self.task_class.complexity

    @property
    def capabilities(self) -> list[str]:
        return list(self.task_class.min_capabilities)


@dataclass
class TaskClassificationResult:
    run_id: str
    success: bool
    tasks_count: int
    classifications: list[ClassifiedTask]
    akasha_event_id: str
    dry_run: bool
    cost_local_pct: int = 100
    error: str | None = None

    @property
    def complexity_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {}
        for c in self.classifications:
            dist[c.complexity] = dist.get(c.complexity, 0) + 1
        return dist

    @property
    def unique_capabilities(self) -> list[str]:
        seen: set[str] = set()
        for c in self.classifications:
            seen.update(c.capabilities)
        return sorted(seen)

    @property
    def high_risk_count(self) -> int:
        return sum(1 for c in self.classifications if c.risk_level in ("high", "critical"))

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "tasks_count": self.tasks_count,
            "complexity_distribution": self.complexity_distribution,
            "unique_capabilities": self.unique_capabilities,
            "high_risk_count": self.high_risk_count,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
        }


class TaskClassificationWorkflow:
    """Classifica lotes de intents OMNIS via TaskClassifier."""

    def __init__(self, akasha_sink=None) -> None:
        self._sink = akasha_sink or MockAkashaSink()

    def run(
        self,
        tasks: list[dict],
        dry_run: bool = True,
    ) -> TaskClassificationResult:
        run_id = _run_id()

        if not tasks:
            event = SinkEvent(
                event_type="task_classification_completed",
                source=run_id,
                payload={"error": "empty_tasks", "tasks_count": 0},
            )
            self._sink.write_event(event)
            return TaskClassificationResult(
                run_id=run_id,
                success=False,
                tasks_count=0,
                classifications=[],
                akasha_event_id=event.event_id,
                dry_run=dry_run,
                error="empty_tasks",
            )

        classifier = TaskClassifier(dry_run=dry_run)
        classifications: list[ClassifiedTask] = []

        for item in tasks:
            intent = item.get("intent", "")
            risk_level = item.get("risk_level", "low")
            task_class = classifier.classify(intent, risk_level)
            classifications.append(ClassifiedTask(
                intent=intent,
                risk_level=risk_level,
                task_class=task_class,
            ))

        event = SinkEvent(
            event_type="task_classification_completed",
            source=run_id,
            payload={
                "tasks_count": len(tasks),
                "complexity_distribution": {
                    c.complexity: sum(1 for x in classifications if x.complexity == c.complexity)
                    for c in classifications
                },
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return TaskClassificationResult(
            run_id=run_id,
            success=True,
            tasks_count=len(tasks),
            classifications=classifications,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
        )

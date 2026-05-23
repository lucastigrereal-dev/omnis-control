"""Learning Writeback Service — bridges Mission LearningJournal to MemoryIntelligence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class WritebackResult:
    """Result of a writeback operation — what was written, blocked, or pending."""

    writeback_id: str
    mission_id: str
    total_learnings: int = 0
    written: int = 0
    blocked: int = 0
    approval_required: int = 0
    records: list[dict[str, object]] = field(default_factory=list)
    details: list[str] = field(default_factory=list)
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    @property
    def success(self) -> bool:
        return self.written > 0 or (
            self.total_learnings == 0 and self.blocked == 0
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "writeback_id": self.writeback_id,
            "mission_id": self.mission_id,
            "total_learnings": self.total_learnings,
            "written": self.written,
            "blocked": self.blocked,
            "approval_required": self.approval_required,
            "records": self.records,
            "details": self.details,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }


class LearningWritebackService:
    """Bridges Mission LearningJournal → Memory Intelligence writeback.

    Reads learnings from a mission's journal, applies write policies,
    and persists validated entries to the file-backed memory adapter.
    """

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    def writeback_from_journal(
        self,
        mission_id: str,
        journal_dir: str,
        sector: str = "produto",
        tags: list[str] | None = None,
    ) -> WritebackResult:
        import uuid

        result = WritebackResult(
            writeback_id=f"wb_{uuid.uuid4().hex[:8]}",
            mission_id=mission_id,
            dry_run=self.dry_run,
        )

        # Read from LearningJournal
        from src.missions.learning import LearningJournal

        journal = LearningJournal(journal_dir)
        entries = journal.read_all()

        if not entries:
            result.details.append("Nenhum aprendizado encontrado no journal")
            return result

        result.total_learnings = len(entries)

        # Convert to MissionMemoryRecord format
        from src.memory_pack.models import MissionMemoryRecord, SOURCE_SESSION

        records: list[MissionMemoryRecord] = []
        for entry in entries:
            try:
                record = MissionMemoryRecord.new(
                    mission_id=mission_id,
                    sector=sector,
                    title=f"Aprendizado: {entry.insight[:60]}",
                    summary=entry.insight,
                    key_insights=[entry.insight],
                    decisions=[],
                    outcomes=[],
                    source_type=SOURCE_SESSION,
                    tags=entry.tags + (tags or []),
                    metadata={
                        "source": entry.source,
                        "confidence": entry.confidence.value,
                        "learning_id": entry.id,
                        "step_id": entry.step_id,
                        "evidence": entry.evidence,
                    },
                )
                records.append(record)
            except Exception:
                result.blocked += 1
                result.details.append(f"Falha ao converter entrada {entry.id}")

        if not records:
            return result

        # Write through MemoryIntelligence
        from src.memory_intel.service import MemoryIntelligence

        mi = MemoryIntelligence(dry_run=self.dry_run)

        for record in records:
            try:
                plan = mi.planner.plan_memory_writeback(
                    records=[record],
                    target_source="akasha",
                    action="upsert",
                    notes=f"Writeback de {mission_id}",
                )

                if plan.record_count > 0:
                    result.written += 1
                    result.records.append(record.to_dict())
                else:
                    result.blocked += 1
                    result.details.append(f"Policy bloqueou: {record.title}")

                if plan.requires_approval:
                    result.approval_required += 1

            except Exception as e:
                result.blocked += 1
                result.details.append(f"Erro: {e}")

        return result

    def writeback_single(
        self,
        mission_id: str,
        insight: str,
        sector: str = "produto",
        tags: list[str] | None = None,
        confidence: str = "medium",
    ) -> WritebackResult:
        import uuid

        result = WritebackResult(
            writeback_id=f"wb_{uuid.uuid4().hex[:8]}",
            mission_id=mission_id,
            total_learnings=1,
            dry_run=self.dry_run,
        )

        from src.memory_pack.models import MissionMemoryRecord, SOURCE_SESSION

        try:
            record = MissionMemoryRecord.new(
                mission_id=mission_id,
                sector=sector,
                title=f"Aprendizado: {insight[:60]}",
                summary=insight,
                key_insights=[insight],
                source_type=SOURCE_SESSION,
                tags=tags or [],
                metadata={"confidence": confidence},
            )
        except Exception as e:
            result.blocked = 1
            result.details.append(str(e))
            return result

        from src.memory_intel.service import MemoryIntelligence

        mi = MemoryIntelligence(dry_run=self.dry_run)

        try:
            plan = mi.planner.plan_memory_writeback(
                records=[record],
                target_source="akasha",
                action="upsert",
                notes=f"Writeback single de {mission_id}",
            )
            if plan.record_count > 0:
                result.written = 1
                result.records.append(record.to_dict())
            else:
                result.blocked = 1
                result.details.append("Policy bloqueou registro")
        except Exception as e:
            result.blocked = 1
            result.details.append(str(e))

        return result

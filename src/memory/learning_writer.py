"""LearningWriter — gera 10_learnings.md e faz writeback para Akasha."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


# ── models ─────────────────────────────────────────────────────────────

@dataclass
class LearningEntry:
    id: str = field(default_factory=lambda: f"LRN-{_short_id()}")
    topic: str = ""
    insight: str = ""
    evidence: str = ""
    confidence: str = "medium"  # high | medium | low
    action_item: str = ""
    tags: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            f"### {self.topic}",
            f"**Insight:** {self.insight}",
            f"**Evidência:** {self.evidence}",
            f"**Confiança:** {self.confidence}",
        ]
        if self.action_item:
            lines.append(f"**Ação:** {self.action_item}")
        if self.tags:
            lines.append(f"**Tags:** {', '.join(self.tags)}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "topic": self.topic,
            "insight": self.insight,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "action_item": self.action_item,
            "tags": self.tags,
        }


@dataclass
class LearningReport:
    mission_id: str
    entries: list[LearningEntry] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)
    sector: str = ""
    total: int = 0
    writeback_status: str = "pending"

    def to_dict(self) -> dict[str, object]:
        return {
            "mission_id": self.mission_id,
            "entries": [e.to_dict() for e in self.entries],
            "generated_at": self.generated_at,
            "sector": self.sector,
            "total": self.total,
            "writeback_status": self.writeback_status,
        }


# ── LearningWriter ─────────────────────────────────────────────────────

class LearningWriter:
    """Gera learnings a partir de resultados de execução e faz writeback."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    def generate(
        self,
        mission_id: str,
        sector: str,
        objectives: list[str],
        execution_summary: dict[str, object],
        mission_path: Path | None = None,
    ) -> LearningReport:
        """Gera aprendizado com base no que foi observado durante a execução."""
        entries = self._derive_learnings(mission_id, sector, objectives, execution_summary)
        report = LearningReport(
            mission_id=mission_id,
            entries=entries,
            sector=sector,
            total=len(entries),
        )

        if mission_path:
            self._write_learnings_md(mission_path, report)

        self._writeback_to_akasha(report)

        return report

    def _derive_learnings(
        self,
        mission_id: str,
        sector: str,
        objectives: list[str],
        summary: dict[str, object],
    ) -> list[LearningEntry]:
        entries: list[LearningEntry] = []

        # 1. Routing observation
        executor = summary.get("executor", "skill_runner")
        entries.append(LearningEntry(
            topic="Roteamento de Missão",
            insight=f"Missão do setor '{sector}' foi roteada para executor '{executor}'.",
            evidence=f"TaskDispatcher resolveu setor '{sector}' → executor '{executor}'.",
            confidence="high",
            tags=[sector, "routing", executor],
        ))

        # 2. Deliverable count
        total_deliverables = summary.get("total_deliverables", 0)
        if total_deliverables > 0:
            entries.append(LearningEntry(
                topic="Mapeamento de Deliverables",
                insight=f"Foram identificados {total_deliverables} deliverables para esta missão.",
                evidence=f"DeliverableMapper gerou {total_deliverables} specs.",
                confidence="high",
                action_item="Validar se todos os deliverables são realmente necessários.",
                tags=[sector, "deliverables", "mapping"],
            ))

        # 3. Dry-run observation
        if self.dry_run or summary.get("dry_run"):
            entries.append(LearningEntry(
                topic="Execução em Modo Seguro",
                insight="Missão executada em dry-run — ações reais não foram disparadas.",
                evidence="dry_run=True em TaskDispatcher e SkillRunnerBridge.",
                confidence="high",
                action_item="Revisar plano e aprovar para execução real.",
                tags=["dry_run", "safety", "governance"],
            ))

        # 4. Skill matching
        skill_matches = summary.get("skills_matched", [])
        skill_fallbacks = summary.get("skills_fallback", 0)
        if skill_matches:
            entries.append(LearningEntry(
                topic="Skills Encontradas",
                insight=f"Skills correspondidas: {', '.join(skill_matches)}.",
                evidence=f"SkillSelector encontrou {len(skill_matches)} skills por tags/intent.",
                confidence="medium",
                tags=["skills", "selection"] + skill_matches,
            ))
        if skill_fallbacks > 0:
            entries.append(LearningEntry(
                topic="Gaps de Skill Detectados",
                insight=f"{skill_fallbacks} deliverable(s) não encontraram skill correspondente.",
                evidence="SkillSelector retornou manual-review como fallback.",
                confidence="medium",
                action_item="Avaliar criação de novas skills via Capability Forge.",
                tags=["skills", "gap", "forge"],
            ))

        # 5. Objective coverage
        if objectives:
            entries.append(LearningEntry(
                topic="Cobertura de Objetivos",
                insight=f"Objetivos da missão: {', '.join(objectives[:3])}.",
                evidence=f"MissionIntake extraiu {len(objectives)} objetivos do texto livre.",
                confidence="medium",
                tags=["objectives", "intake", "planning"],
            ))

        # 6. Risk awareness
        risk = summary.get("risk", "baixo")
        if risk != "baixo":
            entries.append(LearningEntry(
                topic="Consciência de Risco",
                insight=f"Missão classificada com risco '{risk}' — requer atenção especial.",
                evidence=f"RiskClassifier detectou palavras-chave de risco no texto.",
                confidence="high",
                action_item="Revisar approval gate antes de executar ações.",
                tags=["risk", "governance", risk],
            ))

        # 7. Execution mode
        mode = "dry-run" if (self.dry_run or summary.get("dry_run")) else "live"
        entries.append(LearningEntry(
            topic="Modo de Execução",
            insight=f"Pipeline executado em modo '{mode}'.",
            evidence=f"Configuração: dry_run={self.dry_run}, summary.dry_run={summary.get('dry_run')}.",
            confidence="high",
            tags=[mode, "execution", "pipeline"],
        ))

        return entries

    def _write_learnings_md(self, mission_path: Path, report: LearningReport) -> None:
        mission_path.mkdir(parents=True, exist_ok=True)
        md_path = mission_path / "10_learnings.md"

        lines = [
            f"# Aprendizados — {report.mission_id}",
            f"**Gerado em:** {report.generated_at}",
            f"**Setor:** {report.sector}",
            f"**Total de aprendizados:** {report.total}",
            f"**Writeback:** {report.writeback_status}",
            "",
            "---",
            "",
        ]

        for i, entry in enumerate(report.entries, 1):
            lines.append(f"## {i}. {entry.topic}")
            lines.append(entry.to_markdown())
            lines.append("")

        md_path.write_text("\n".join(lines), encoding="utf-8")

    def _writeback_to_akasha(self, report: LearningReport) -> None:
        try:
            from src.memory.writeback import LearningWritebackService

            wb = LearningWritebackService(dry_run=self.dry_run)
            for entry in report.entries:
                wb.writeback_single(
                    mission_id=report.mission_id,
                    insight=entry.insight,
                    sector=report.sector,
                    tags=entry.tags,
                    confidence=entry.confidence,
                )
            report.writeback_status = "dry_run_ok" if self.dry_run else "written"
        except ImportError:
            report.writeback_status = "skipped — writeback service unavailable"
        except Exception as exc:
            report.writeback_status = f"error: {exc}"

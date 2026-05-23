"""ForgeOrchestrator — gap detection → forge trigger → skill registration."""
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
class GapReport:
    gap_id: str = field(default_factory=lambda: f"GAP-{_short_id()}")
    mission_id: str = ""
    missing_capability: str = ""
    sector: str = ""
    detected_at: str = field(default_factory=_now_iso)
    severity: str = "medium"  # low | medium | high
    suggested_skill_name: str = ""
    suggested_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "gap_id": self.gap_id,
            "mission_id": self.mission_id,
            "missing_capability": self.missing_capability,
            "sector": self.sector,
            "detected_at": self.detected_at,
            "severity": self.severity,
            "suggested_skill_name": self.suggested_skill_name,
            "suggested_tags": self.suggested_tags,
        }


@dataclass
class ForgeResult:
    forge_id: str = field(default_factory=lambda: f"FRG-{_short_id()}")
    gap_id: str = ""
    mission_id: str = ""
    skill_name: str = ""
    status: str = "dry_run"  # dry_run | scaffolded | tested | registered | failed
    version: str = "0.1.0"
    output_path: str = ""
    test_count: int = 0
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    @property
    def success(self) -> bool:
        return self.status in ("dry_run", "scaffolded", "tested", "registered")

    def to_dict(self) -> dict[str, object]:
        return {
            "forge_id": self.forge_id,
            "gap_id": self.gap_id,
            "mission_id": self.mission_id,
            "skill_name": self.skill_name,
            "status": self.status,
            "version": self.version,
            "output_path": self.output_path,
            "test_count": self.test_count,
            "errors": self.errors,
            "created_at": self.created_at,
        }


@dataclass
class SkillVersion:
    skill_name: str
    version: str
    status: str = "active"  # active | superseded | broken
    registered_at: str = field(default_factory=_now_iso)
    rollback_from: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "skill_name": self.skill_name,
            "version": self.version,
            "status": self.status,
            "registered_at": self.registered_at,
            "rollback_from": self.rollback_from,
        }


# ── orchestrator ───────────────────────────────────────────────────────

class ForgeOrchestrator:
    """Orquestra detecção de gaps → criação de skills via Capability Forge."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self._versions: dict[str, list[SkillVersion]] = {}
        self.gaps: list[GapReport] = []
        self.results: list[ForgeResult] = []

    def detect_gaps(
        self,
        mission_id: str,
        sector: str,
        missing_skills: list[str],
        deliverables: list[str],
    ) -> list[GapReport]:
        """Detecta gaps de capability a partir de skills não encontradas."""
        reports: list[GapReport] = []
        for skill in missing_skills:
            gap = GapReport(
                mission_id=mission_id,
                missing_capability=f"Skill '{skill}' não encontrada para deliverable",
                sector=sector,
                severity="high" if sector in ("sales", "finance") else "medium",
                suggested_skill_name=self._suggest_skill_name(skill, sector),
                suggested_tags=[sector, skill, "forge"],
            )
            reports.append(gap)
            self.gaps.append(gap)
        return reports

    def forge(
        self,
        gap: GapReport,
        output_dir: Path | None = None,
    ) -> ForgeResult:
        """Aciona a forja para criar uma skill a partir de um gap."""
        result = ForgeResult(
            gap_id=gap.gap_id,
            mission_id=gap.mission_id,
            skill_name=gap.suggested_skill_name,
            status="dry_run" if self.dry_run else "scaffolded",
            output_path=str(output_dir / gap.suggested_skill_name) if output_dir else "",
        )

        if not self.dry_run:
            try:
                result.status = "scaffolded"
                if output_dir:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    (output_dir / gap.suggested_skill_name / "SKILL.md").mkdir(
                        parents=True, exist_ok=True
                    )
            except Exception as exc:
                result.status = "failed"
                result.errors.append(str(exc))

        self.results.append(result)
        return result

    def register_skill(
        self, forge_result: ForgeResult, version: str = "0.1.0"
    ) -> SkillVersion:
        """Registra a skill criada no controle de versão."""
        sv = SkillVersion(
            skill_name=forge_result.skill_name,
            version=version,
            status="active",
        )

        if forge_result.skill_name not in self._versions:
            self._versions[forge_result.skill_name] = []
        self._versions[forge_result.skill_name].append(sv)
        return sv

    def rollback(self, skill_name: str) -> SkillVersion:
        """Rollback para versão anterior de uma skill quebrada."""
        versions = self._versions.get(skill_name, [])
        if len(versions) < 2:
            return SkillVersion(
                skill_name=skill_name,
                version="none",
                status="broken",
                rollback_from="",
            )

        # Mark current as broken
        current = versions[-1]
        current.status = "broken"

        # Activate previous
        previous = versions[-2]
        rollback = SkillVersion(
            skill_name=skill_name,
            version=previous.version,
            status="active",
            rollback_from=current.version,
        )
        versions.append(rollback)
        return rollback

    def process_gaps(
        self,
        mission_id: str,
        sector: str,
        missing_skills: list[str],
        deliverables: list[str],
        output_dir: Path | None = None,
    ) -> list[ForgeResult]:
        """Pipeline completo: detecta gaps → forja skills → registra."""
        gaps = self.detect_gaps(mission_id, sector, missing_skills, deliverables)
        results: list[ForgeResult] = []
        for gap in gaps:
            forge_result = self.forge(gap, output_dir)
            if forge_result.success:
                self.register_skill(forge_result)
            results.append(forge_result)
        return results

    def _suggest_skill_name(self, missing: str, sector: str) -> str:
        """Sugere nome de skill baseado no gap e setor."""
        clean = missing.lower().replace(" ", "_").replace("-", "_")
        return f"{sector}_{clean}"

    @property
    def version_count(self) -> int:
        return sum(len(v) for v in self._versions.values())

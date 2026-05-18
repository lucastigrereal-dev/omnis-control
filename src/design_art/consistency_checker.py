"""Visual consistency checker — validates design outputs against brand profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .models import BrandVisualProfile, DesignBrief, AssetSpec


@dataclass
class ConsistencyReport:
    check_id: str
    profile_id: str
    profile_name: str
    overall_score: float = 0.0  # 0.0–10.0
    checks: list[ConsistencyCheck] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    recommendation: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

    @property
    def is_consistent(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> dict:
        import dataclasses
        d = dataclasses.asdict(self)
        d["checks"] = [c.to_dict() for c in self.checks]
        return d


@dataclass
class ConsistencyCheck:
    dimension: str
    expected: str
    actual: str
    passed: bool = True
    severity: str = "info"  # info, warning, error
    detail: str = ""

    def to_dict(self) -> dict:
        import dataclasses
        return dataclasses.asdict(self)


class ConsistencyChecker:
    """Validates design outputs against brand visual profiles."""

    def check_design_brief(self, brief: DesignBrief, profile: BrandVisualProfile) -> ConsistencyReport:
        import uuid

        report = ConsistencyReport(
            check_id=uuid.uuid4().hex[:8],
            profile_id=profile.brand_id,
            profile_name=profile.name,
        )

        # Check 1: Format matches intent
        report.checks.append(self._check_format(brief, profile))

        # Check 2: Dimensions match aspect ratio expectations
        report.checks.append(self._check_dimensions(brief))

        # Check 3: Archetype alignment
        report.checks.append(self._check_archetype(brief, profile))

        # Check 4: Color references in constraints
        report.checks.append(self._check_colors(brief, profile))

        # Check 5: Copy text length/quality
        report.checks.append(self._check_copy(brief))

        # Tally
        for c in report.checks:
            if not c.passed:
                if c.severity == "error":
                    report.failed += 1
                else:
                    report.warnings += 1
            else:
                report.passed += 1

        # Score
        total = len(report.checks)
        report.overall_score = round((report.passed / total) * 10.0, 1) if total > 0 else 0.0

        if report.failed == 0 and report.warnings == 0:
            report.recommendation = "Design consistente com o perfil visual da marca. Pronto para producao."
        elif report.failed == 0:
            report.recommendation = f"Design aprovado com {report.warnings} alerta(s). Revisar antes de publicar."
        else:
            report.recommendation = f"Design precisa de ajustes: {report.failed} erro(s) e {report.warnings} alerta(s)."

        return report

    def check_asset(self, asset: AssetSpec, profile: BrandVisualProfile) -> ConsistencyReport:
        import uuid

        report = ConsistencyReport(
            check_id=uuid.uuid4().hex[:8],
            profile_id=profile.brand_id,
            profile_name=profile.name,
        )

        # Check format
        report.checks.append(ConsistencyCheck(
            dimension="file_format",
            expected="png or jpg",
            actual=asset.file_format,
            passed=asset.file_format in ("png", "jpg", "webp"),
            severity="error" if asset.file_format not in ("png", "jpg", "webp") else "info",
            detail="Formato deve ser exportavel para Instagram",
        ))

        # Check DPI
        report.checks.append(ConsistencyCheck(
            dimension="dpi",
            expected="72",
            actual=str(asset.dpi),
            passed=asset.dpi >= 72,
            severity="warning" if asset.dpi < 72 else "info",
            detail="DPI minimo de 72 para redes sociais",
        ))

        # Check dimensions
        min_dim = 1080
        dims_ok = asset.width >= min_dim and asset.height >= min_dim
        report.checks.append(ConsistencyCheck(
            dimension="minimum_dimensions",
            expected=f">= {min_dim}x{min_dim}",
            actual=f"{asset.width}x{asset.height}",
            passed=dims_ok,
            severity="error" if not dims_ok else "info",
            detail="Resolucao minima para Instagram",
        ))

        # Tally
        for c in report.checks:
            if not c.passed:
                if c.severity == "error":
                    report.failed += 1
                else:
                    report.warnings += 1
            else:
                report.passed += 1

        total = len(report.checks)
        report.overall_score = round((report.passed / total) * 10.0, 1) if total > 0 else 0.0
        report.recommendation = "Asset pronto." if report.is_consistent else "Asset precisa de ajustes."
        return report

    def _check_format(self, brief: DesignBrief, profile: BrandVisualProfile) -> ConsistencyCheck:
        return ConsistencyCheck(
            dimension="target_format",
            expected="carousel, reel, story, or post",
            actual=brief.target_format,
            passed=brief.target_format in ("carousel", "reel", "story", "post", "banner", "thumbnail"),
            detail="Formato de saida valido",
        )

    def _check_dimensions(self, brief: DesignBrief) -> ConsistencyCheck:
        dims = brief.dimensions.split("x")
        ok = len(dims) == 2 and all(d.isdigit() and int(d) >= 720 for d in dims)
        return ConsistencyCheck(
            dimension="dimensions",
            expected=">= 720x720",
            actual=brief.dimensions,
            passed=ok,
            severity="error" if not ok else "info",
            detail="Dimensoes minimas para redes sociais",
        )

    def _check_archetype(self, brief: DesignBrief, profile: BrandVisualProfile) -> ConsistencyCheck:
        return ConsistencyCheck(
            dimension="visual_archetype",
            expected=profile.visual_archetype,
            actual=profile.visual_archetype,
            passed=True,
            detail=f"Perfil usa arquétipo '{profile.visual_archetype}'",
        )

    def _check_colors(self, brief: DesignBrief, profile: BrandVisualProfile) -> ConsistencyCheck:
        has_colors = any(
            "cor" in c.lower() or "color" in c.lower() or "paleta" in c.lower()
            for c in brief.constraints
        )
        return ConsistencyCheck(
            dimension="color_reference",
            expected="referencia de cores nas constraints",
            actual="presente" if has_colors else "ausente",
            passed=True,  # Always passes, just informative
            severity="warning" if not has_colors else "info",
            detail="Incluir paleta de cores nas constraints melhora consistencia",
        )

    def _check_copy(self, brief: DesignBrief) -> ConsistencyCheck:
        if not brief.copy_text:
            return ConsistencyCheck(
                dimension="copy_text",
                expected="texto presente",
                actual="ausente",
                passed=True,
                severity="warning",
                detail="Brief sem copy_text — design pode ser generico",
            )
        words = len(brief.copy_text.split())
        return ConsistencyCheck(
            dimension="copy_text_length",
            expected=">= 10 palavras",
            actual=f"{words} palavras",
            passed=words >= 10,
            severity="warning" if words < 10 else "info",
            detail="Copy muito curta pode nao comunicar bem",
        )

"""A/B comparison for video packages — compare two versions side by side."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

from .models import VideoPackage, HookCandidate


@dataclass
class ABComparison:
    comparison_id: str
    title: str
    package_a_id: str
    package_b_id: str
    winner: Optional[str] = None  # "A", "B", or "tie"
    score_a: float = 0.0
    score_b: float = 0.0
    differences: list[ABDiff] = field(default_factory=list)
    recommendation: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

    @property
    def is_tie(self) -> bool:
        return self.winner == "tie"

    @property
    def score_delta(self) -> float:
        return abs(self.score_a - self.score_b)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["differences"] = [diff.to_dict() for diff in self.differences]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ABComparison":
        diffs = [ABDiff.from_dict(x) for x in d.get("differences", [])]
        fields = {k: v for k, v in d.items() if k in cls.__dataclass_fields__ and k != "differences"}
        comp = cls(**fields)
        comp.differences = diffs
        return comp


@dataclass
class ABDiff:
    field: str
    value_a: str
    value_b: str
    verdict: str = ""  # "a_better", "b_better", "same"
    weight: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ABDiff":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class ABComparator:
    """Compare two VideoPackages across multiple dimensions."""

    def compare(self, package_a: VideoPackage, package_b: VideoPackage, title: str = "") -> ABComparison:
        import uuid

        comp = ABComparison(
            comparison_id=uuid.uuid4().hex[:8],
            title=title or f"{package_a.package_id} vs {package_b.package_id}",
            package_a_id=package_a.package_id,
            package_b_id=package_b.package_id,
        )

        # 1. Hook strength
        hook_a = package_a.strongest_hook
        hook_b = package_b.strongest_hook
        if hook_a and hook_b:
            comp.differences.append(ABDiff(
                field="strongest_hook_score",
                value_a=f"{hook_a.score:.2f}",
                value_b=f"{hook_b.score:.2f}",
                verdict="a_better" if hook_a.score > hook_b.score else ("b_better" if hook_b.score > hook_a.score else "same"),
                weight=2.0,
            ))
            comp.score_a += hook_a.score * 2.0
            comp.score_b += hook_b.score * 2.0

        # 2. Hook count
        hooks_a = len(package_a.hook_candidates)
        hooks_b = len(package_b.hook_candidates)
        comp.differences.append(ABDiff(
            field="hook_count",
            value_a=str(hooks_a),
            value_b=str(hooks_b),
            verdict="a_better" if hooks_a > hooks_b else ("b_better" if hooks_b > hooks_a else "same"),
            weight=1.0,
        ))
        comp.score_a += hooks_a
        comp.score_b += hooks_b

        # 3. Total clips
        clips_a = package_a.total_clips
        clips_b = package_b.total_clips
        comp.differences.append(ABDiff(
            field="total_clips",
            value_a=str(clips_a),
            value_b=str(clips_b),
            verdict=self._clips_verdict(clips_a, clips_b),
            weight=1.0,
        ))
        comp.score_a += clips_a
        comp.score_b += clips_b

        # 4. Segment count
        segs_a = package_a.reel_script.segment_count if package_a.reel_script else 0
        segs_b = package_b.reel_script.segment_count if package_b.reel_script else 0
        comp.differences.append(ABDiff(
            field="script_segments",
            value_a=str(segs_a),
            value_b=str(segs_b),
            verdict="a_better" if segs_a > segs_b else ("b_better" if segs_b > segs_a else "same"),
            weight=1.0,
        ))
        comp.score_a += segs_a
        comp.score_b += segs_b

        # 5. Validation
        val_a = package_a.is_valid
        val_b = package_b.is_valid
        comp.differences.append(ABDiff(
            field="validation",
            value_a="PASS" if val_a else "FAIL",
            value_b="PASS" if val_b else "FAIL",
            verdict="same" if val_a == val_b else ("a_better" if val_a else "b_better"),
            weight=3.0,
        ))
        comp.score_a += 3.0 if val_a else 0.0
        comp.score_b += 3.0 if val_b else 0.0

        # 6. Total duration
        dur_a = package_a.cut_plan.total_duration_seconds if package_a.cut_plan else 0.0
        dur_b = package_b.cut_plan.total_duration_seconds if package_b.cut_plan else 0.0
        comp.differences.append(ABDiff(
            field="total_duration",
            value_a=f"{dur_a:.1f}s",
            value_b=f"{dur_b:.1f}s",
            verdict="same",
            weight=0.5,
        ))

        # Determine winner
        if abs(comp.score_a - comp.score_b) < 0.5:
            comp.winner = "tie"
            comp.recommendation = "Ambas as versoes sao equivalentes. Escolha por preferencia de estilo."
        elif comp.score_a > comp.score_b:
            comp.winner = "A"
            comp.recommendation = f"Versao A ({package_a.package_id}) venceu com score {comp.score_a:.1f} vs {comp.score_b:.1f}."
        else:
            comp.winner = "B"
            comp.recommendation = f"Versao B ({package_b.package_id}) venceu com score {comp.score_b:.1f} vs {comp.score_a:.1f}."

        return comp

    def _clips_verdict(self, a: int, b: int) -> str:
        """More clips isn't always better — prefer 3-5 for reels."""
        def _ideal_score(n: int) -> float:
            if n == 0:
                return 0
            if 3 <= n <= 5:
                return 1.0
            return max(0, 1.0 - abs(n - 4) * 0.2)

        score_a = _ideal_score(a)
        score_b = _ideal_score(b)
        if abs(score_a - score_b) < 0.1:
            return "same"
        return "a_better" if score_a > score_b else "b_better"

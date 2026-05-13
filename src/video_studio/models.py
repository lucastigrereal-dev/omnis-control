"""Modelos do Video Studio — dataclasses deterministicas para especificacao de edicao."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VideoSourceKind(str, Enum):
    RAW = "raw"
    RECORDING = "recording"
    IMPORTED = "imported"
    GENERATED = "generated"


class HookStrength(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CutType(str, Enum):
    TRIM = "trim"
    SPLIT = "split"
    KEEP = "keep"
    REMOVE = "remove"


class ReelFormat(str, Enum):
    SHORT = "short"        # < 60s
    STANDARD = "standard"  # 60-90s
    EXTENDED = "extended"   # > 90s


class CaptionPosition(str, Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


class CaptionStyle(str, Enum):
    BOLD = "bold"
    ITALIC = "italic"
    REGULAR = "regular"
    HIGHLIGHT = "highlight"


class PackageStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    VALIDATED = "validated"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class VideoSource:
    """Metadados da fonte de video — nunca processa arquivo real."""
    source_id: str
    kind: VideoSourceKind
    uri_hint: str
    duration_seconds: float
    width: int
    height: int
    fps: float
    codec_hint: str
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        kind: VideoSourceKind,
        uri_hint: str,
        duration_seconds: float,
        width: int = 1920,
        height: int = 1080,
        fps: float = 30.0,
        codec_hint: str = "h264",
    ) -> "VideoSource":
        if duration_seconds <= 0:
            raise ValueError("duration_seconds deve ser > 0")
        if width <= 0 or height <= 0:
            raise ValueError("width e height devem ser > 0")
        if fps <= 0:
            raise ValueError("fps deve ser > 0")
        return cls(
            source_id=_new_id("vs"),
            kind=kind,
            uri_hint=uri_hint,
            duration_seconds=duration_seconds,
            width=width,
            height=height,
            fps=fps,
            codec_hint=codec_hint,
        )

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "kind": self.kind.value,
            "uri_hint": self.uri_hint,
            "duration_seconds": self.duration_seconds,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "codec_hint": self.codec_hint,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VideoSource":
        kind = data.get("kind", "raw")
        if isinstance(kind, str):
            kind = VideoSourceKind(kind)
        return cls(
            source_id=data.get("source_id", _new_id("vs")),
            kind=kind,
            uri_hint=data.get("uri_hint", ""),
            duration_seconds=data.get("duration_seconds", 0),
            width=data.get("width", 1920),
            height=data.get("height", 1080),
            fps=data.get("fps", 30.0),
            codec_hint=data.get("codec_hint", "h264"),
            created_at=data.get("created_at", _now_iso()),
        )

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height if self.height > 0 else 1.0

    @property
    def is_vertical(self) -> bool:
        return self.height > self.width


@dataclass
class TranscriptSegment:
    """Segmento de transcricao com timestamps — nunca transcreve audio real."""
    segment_id: str
    start_seconds: float
    end_seconds: float
    text: str
    confidence: float
    speaker_label: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        start_seconds: float,
        end_seconds: float,
        text: str,
        confidence: float = 1.0,
        speaker_label: Optional[str] = None,
    ) -> "TranscriptSegment":
        if start_seconds < 0 or end_seconds < 0:
            raise ValueError("timestamps nao podem ser negativos")
        if end_seconds <= start_seconds:
            raise ValueError("end_seconds deve ser > start_seconds")
        if not text.strip():
            raise ValueError("text nao pode ser vazio")
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("confidence deve estar entre 0.0 e 1.0")
        return cls(
            segment_id=_new_id("ts"),
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            text=text.strip(),
            confidence=confidence,
            speaker_label=speaker_label,
        )

    def to_dict(self) -> dict:
        return {
            "segment_id": self.segment_id,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "text": self.text,
            "confidence": self.confidence,
            "speaker_label": self.speaker_label,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TranscriptSegment":
        return cls(
            segment_id=data.get("segment_id", _new_id("ts")),
            start_seconds=data.get("start_seconds", 0),
            end_seconds=data.get("end_seconds", 0),
            text=data.get("text", ""),
            confidence=data.get("confidence", 1.0),
            speaker_label=data.get("speaker_label"),
            created_at=data.get("created_at", _now_iso()),
        )

    @property
    def duration(self) -> float:
        return self.end_seconds - self.start_seconds

    @property
    def word_count(self) -> int:
        return len(self.text.split())


@dataclass
class HookCandidate:
    """Candidato a hook detectado em segmento de transcricao."""
    hook_id: str
    segment_id: str
    start_seconds: float
    end_seconds: float
    hook_text: str
    strength: HookStrength
    score: float
    rationale: str
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        segment_id: str,
        start_seconds: float,
        end_seconds: float,
        hook_text: str,
        strength: HookStrength,
        score: float,
        rationale: str,
    ) -> "HookCandidate":
        if not hook_text.strip():
            raise ValueError("hook_text nao pode ser vazio")
        if not (0.0 <= score <= 1.0):
            raise ValueError("score deve estar entre 0.0 e 1.0")
        return cls(
            hook_id=_new_id("hk"),
            segment_id=segment_id,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            hook_text=hook_text.strip(),
            strength=strength,
            score=score,
            rationale=rationale,
        )

    def to_dict(self) -> dict:
        return {
            "hook_id": self.hook_id,
            "segment_id": self.segment_id,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "hook_text": self.hook_text,
            "strength": self.strength.value,
            "score": self.score,
            "rationale": self.rationale,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HookCandidate":
        strength = data.get("strength", "medium")
        if isinstance(strength, str):
            strength = HookStrength(strength)
        return cls(
            hook_id=data.get("hook_id", _new_id("hk")),
            segment_id=data.get("segment_id", ""),
            start_seconds=data.get("start_seconds", 0),
            end_seconds=data.get("end_seconds", 0),
            hook_text=data.get("hook_text", ""),
            strength=strength,
            score=data.get("score", 0.0),
            rationale=data.get("rationale", ""),
            created_at=data.get("created_at", _now_iso()),
        )


@dataclass
class CutPlan:
    """Plano de corte deterministico baseado em timestamps."""
    plan_id: str
    source_id: str
    cuts: list[CutInstruction] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, source_id: str) -> "CutPlan":
        if not source_id:
            raise ValueError("source_id nao pode ser vazio")
        return cls(
            plan_id=_new_id("cp"),
            source_id=source_id,
            cuts=[],
            total_duration_seconds=0.0,
        )

    def add_cut(self, instruction: "CutInstruction") -> None:
        self.cuts.append(instruction)
        self._recalc_duration()

    def remove_cut(self, cut_id: str) -> bool:
        before = len(self.cuts)
        self.cuts = [c for c in self.cuts if c.cut_id != cut_id]
        if len(self.cuts) != before:
            self._recalc_duration()
            return True
        return False

    def _recalc_duration(self) -> None:
        self.total_duration_seconds = sum(
            c.end_seconds - c.start_seconds
            for c in self.cuts
            if c.cut_type != CutType.REMOVE
        )

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "source_id": self.source_id,
            "cuts": [c.to_dict() for c in self.cuts],
            "total_duration_seconds": self.total_duration_seconds,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CutPlan":
        plan = cls(
            plan_id=data.get("plan_id", _new_id("cp")),
            source_id=data.get("source_id", ""),
            total_duration_seconds=data.get("total_duration_seconds", 0.0),
            created_at=data.get("created_at", _now_iso()),
        )
        for c in data.get("cuts", []):
            plan.cuts.append(CutInstruction.from_dict(c))
        return plan

    @property
    def keep_cuts(self) -> list["CutInstruction"]:
        return [c for c in self.cuts if c.cut_type != CutType.REMOVE]

    @property
    def removed_cuts(self) -> list["CutInstruction"]:
        return [c for c in self.cuts if c.cut_type == CutType.REMOVE]


@dataclass
class CutInstruction:
    """Instrucao individual de corte."""
    cut_id: str
    start_seconds: float
    end_seconds: float
    cut_type: CutType
    label: str
    segment_id: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        start_seconds: float,
        end_seconds: float,
        cut_type: CutType,
        label: str,
        segment_id: Optional[str] = None,
    ) -> "CutInstruction":
        if start_seconds < 0 or end_seconds < 0:
            raise ValueError("timestamps nao podem ser negativos")
        if end_seconds <= start_seconds and cut_type != CutType.REMOVE:
            raise ValueError("end_seconds deve ser > start_seconds para cortes nao-removidos")
        if not label.strip():
            raise ValueError("label nao pode ser vazio")
        return cls(
            cut_id=_new_id("ci"),
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            cut_type=cut_type,
            label=label.strip(),
            segment_id=segment_id,
        )

    def to_dict(self) -> dict:
        return {
            "cut_id": self.cut_id,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "cut_type": self.cut_type.value,
            "label": self.label,
            "segment_id": self.segment_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CutInstruction":
        cut_type = data.get("cut_type", "keep")
        if isinstance(cut_type, str):
            cut_type = CutType(cut_type)
        return cls(
            cut_id=data.get("cut_id", _new_id("ci")),
            start_seconds=data.get("start_seconds", 0),
            end_seconds=data.get("end_seconds", 0),
            cut_type=cut_type,
            label=data.get("label", ""),
            segment_id=data.get("segment_id"),
            created_at=data.get("created_at", _now_iso()),
        )

    @property
    def duration(self) -> float:
        return self.end_seconds - self.start_seconds


@dataclass
class ReelScript:
    """Roteiro de reel com timestamps e especificacoes de legenda."""
    script_id: str
    source_id: str
    plan_id: str
    format: ReelFormat
    title: str
    segments: list[ReelSegment] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        source_id: str,
        plan_id: str,
        format: ReelFormat,
        title: str,
    ) -> "ReelScript":
        if not source_id:
            raise ValueError("source_id nao pode ser vazio")
        if not plan_id:
            raise ValueError("plan_id nao pode ser vazio")
        if not title.strip():
            raise ValueError("title nao pode ser vazio")
        return cls(
            script_id=_new_id("rs"),
            source_id=source_id,
            plan_id=plan_id,
            format=format,
            title=title.strip(),
            segments=[],
            total_duration_seconds=0.0,
        )

    def add_segment(self, segment: "ReelSegment") -> None:
        self.segments.append(segment)
        self.total_duration_seconds = sum(s.duration for s in self.segments)

    def to_dict(self) -> dict:
        return {
            "script_id": self.script_id,
            "source_id": self.source_id,
            "plan_id": self.plan_id,
            "format": self.format.value,
            "title": self.title,
            "segments": [s.to_dict() for s in self.segments],
            "total_duration_seconds": self.total_duration_seconds,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReelScript":
        fmt = data.get("format", "standard")
        if isinstance(fmt, str):
            fmt = ReelFormat(fmt)
        script = cls(
            script_id=data.get("script_id", _new_id("rs")),
            source_id=data.get("source_id", ""),
            plan_id=data.get("plan_id", ""),
            format=fmt,
            title=data.get("title", ""),
            total_duration_seconds=data.get("total_duration_seconds", 0.0),
            created_at=data.get("created_at", _now_iso()),
        )
        for s in data.get("segments", []):
            script.segments.append(ReelSegment.from_dict(s))
        return script

    @property
    def segment_count(self) -> int:
        return len(self.segments)


@dataclass
class ReelSegment:
    """Segmento individual do roteiro de reel."""
    position: int
    start_seconds: float
    end_seconds: float
    narration: str
    on_screen_text: Optional[str] = None
    caption_spec: Optional["CaptionOverlaySpec"] = None
    transition_hint: str = "cut"

    def to_dict(self) -> dict:
        return {
            "position": self.position,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "narration": self.narration,
            "on_screen_text": self.on_screen_text,
            "caption_spec": self.caption_spec.to_dict() if self.caption_spec else None,
            "transition_hint": self.transition_hint,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReelSegment":
        cap = data.get("caption_spec")
        return cls(
            position=data.get("position", 0),
            start_seconds=data.get("start_seconds", 0),
            end_seconds=data.get("end_seconds", 0),
            narration=data.get("narration", ""),
            on_screen_text=data.get("on_screen_text"),
            caption_spec=CaptionOverlaySpec.from_dict(cap) if cap else None,
            transition_hint=data.get("transition_hint", "cut"),
        )

    @property
    def duration(self) -> float:
        return self.end_seconds - self.start_seconds


@dataclass
class CaptionOverlaySpec:
    """Especificacao de legenda na tela — nunca renderiza."""
    text: str
    position: CaptionPosition
    style: CaptionStyle
    font_size_hint: int
    color_hex: str
    start_seconds: float
    end_seconds: float
    animation_hint: str = "fade"

    @classmethod
    def new(
        cls,
        text: str,
        position: CaptionPosition = CaptionPosition.BOTTOM,
        style: CaptionStyle = CaptionStyle.BOLD,
        font_size_hint: int = 48,
        color_hex: str = "#FFFFFF",
        start_seconds: float = 0.0,
        end_seconds: float = 3.0,
        animation_hint: str = "fade",
    ) -> "CaptionOverlaySpec":
        if not text.strip():
            raise ValueError("text nao pode ser vazio")
        if font_size_hint <= 0:
            raise ValueError("font_size_hint deve ser > 0")
        if not color_hex.startswith("#") or len(color_hex) != 7:
            raise ValueError("color_hex deve ser formato #RRGGBB")
        if end_seconds <= start_seconds:
            raise ValueError("end_seconds deve ser > start_seconds")
        return cls(
            text=text.strip(),
            position=position,
            style=style,
            font_size_hint=font_size_hint,
            color_hex=color_hex,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            animation_hint=animation_hint,
        )

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "position": self.position.value,
            "style": self.style.value,
            "font_size_hint": self.font_size_hint,
            "color_hex": self.color_hex,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "animation_hint": self.animation_hint,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CaptionOverlaySpec":
        pos = data.get("position", "bottom")
        if isinstance(pos, str):
            pos = CaptionPosition(pos)
        sty = data.get("style", "bold")
        if isinstance(sty, str):
            sty = CaptionStyle(sty)
        return cls(
            text=data.get("text", ""),
            position=pos,
            style=sty,
            font_size_hint=data.get("font_size_hint", 48),
            color_hex=data.get("color_hex", "#FFFFFF"),
            start_seconds=data.get("start_seconds", 0),
            end_seconds=data.get("end_seconds", 0),
            animation_hint=data.get("animation_hint", "fade"),
        )

    @property
    def duration(self) -> float:
        return self.end_seconds - self.start_seconds


@dataclass
class VideoPackage:
    """Pacote completo de edicao — agrega source, corte, script e legendas."""
    package_id: str
    source: VideoSource
    cut_plan: CutPlan
    reel_script: ReelScript
    hook_candidates: list[HookCandidate] = field(default_factory=list)
    caption_specs: list[CaptionOverlaySpec] = field(default_factory=list)
    notes: str = ""
    status: PackageStatus = PackageStatus.DRAFT
    validation_errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        source: VideoSource,
        cut_plan: CutPlan,
        reel_script: ReelScript,
        notes: str = "",
    ) -> "VideoPackage":
        return cls(
            package_id=_new_id("vp"),
            source=source,
            cut_plan=cut_plan,
            reel_script=reel_script,
            hook_candidates=[],
            caption_specs=[],
            notes=notes,
            status=PackageStatus.DRAFT,
            validation_errors=[],
        )

    def add_hook(self, hook: HookCandidate) -> None:
        self.hook_candidates.append(hook)

    def add_caption_spec(self, spec: CaptionOverlaySpec) -> None:
        self.caption_specs.append(spec)

    def validate(self) -> bool:
        self.validation_errors = []
        if not self.source:
            self.validation_errors.append("source e obrigatorio")
        if not self.cut_plan:
            self.validation_errors.append("cut_plan e obrigatorio")
        elif not self.cut_plan.cuts:
            self.validation_errors.append("cut_plan deve conter pelo menos 1 corte")
        if not self.reel_script:
            self.validation_errors.append("reel_script e obrigatorio")
        elif not self.reel_script.segments:
            self.validation_errors.append("reel_script deve conter pelo menos 1 segmento")
        if self.cut_plan and self.source:
            if self.cut_plan.source_id != self.source.source_id:
                self.validation_errors.append("cut_plan.source_id nao coincide com source.source_id")
        if self.cut_plan and self.reel_script:
            if self.cut_plan.plan_id != self.reel_script.plan_id:
                self.validation_errors.append("reel_script.plan_id nao coincide com cut_plan.plan_id")
            if self.cut_plan.source_id != self.reel_script.source_id:
                self.validation_errors.append("reel_script.source_id nao coincide com cut_plan.source_id")
        self.status = PackageStatus.VALIDATED if not self.validation_errors else PackageStatus.REJECTED
        return len(self.validation_errors) == 0

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "source": self.source.to_dict(),
            "cut_plan": self.cut_plan.to_dict(),
            "reel_script": self.reel_script.to_dict(),
            "hook_candidates": [h.to_dict() for h in self.hook_candidates],
            "caption_specs": [c.to_dict() for c in self.caption_specs],
            "notes": self.notes,
            "status": self.status.value,
            "validation_errors": self.validation_errors,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VideoPackage":
        status = data.get("status", "draft")
        if isinstance(status, str):
            status = PackageStatus(status)
        pkg = cls(
            package_id=data.get("package_id", _new_id("vp")),
            source=VideoSource.from_dict(data.get("source", {})),
            cut_plan=CutPlan.from_dict(data.get("cut_plan", {})),
            reel_script=ReelScript.from_dict(data.get("reel_script", {})),
            notes=data.get("notes", ""),
            status=status,
            validation_errors=data.get("validation_errors", []),
            created_at=data.get("created_at", _now_iso()),
        )
        for h in data.get("hook_candidates", []):
            pkg.hook_candidates.append(HookCandidate.from_dict(h))
        for c in data.get("caption_specs", []):
            pkg.caption_specs.append(CaptionOverlaySpec.from_dict(c))
        return pkg

    @property
    def is_valid(self) -> bool:
        return self.status == PackageStatus.VALIDATED

    @property
    def total_clips(self) -> int:
        return len(self.cut_plan.keep_cuts) if self.cut_plan else 0

    @property
    def strongest_hook(self) -> Optional[HookCandidate]:
        if not self.hook_candidates:
            return None
        return max(self.hook_candidates, key=lambda h: h.score)

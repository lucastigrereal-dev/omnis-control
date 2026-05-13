"""Servico VideoStudioPlanner — operacoes deterministicas de planejamento de edicao."""
from __future__ import annotations

from typing import Optional

from src.video_studio.models import (
    CaptionOverlaySpec,
    CaptionPosition,
    CaptionStyle,
    CutInstruction,
    CutPlan,
    CutType,
    HookCandidate,
    HookStrength,
    ReelFormat,
    ReelScript,
    ReelSegment,
    TranscriptSegment,
    VideoPackage,
    VideoSource,
)
from src.video_studio.errors import (
    InvalidCutPlanError,
    InvalidReelScriptError,
    InvalidTranscriptError,
    InvalidVideoPackageError,
    ValidationError,
)


class VideoStudioPlanner:
    """Planejador deterministico de edicao de video — dry-run, sem processamento real."""

    def __init__(self) -> None:
        self._last_package: Optional[VideoPackage] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_transcript_segments(
        self,
        segments: list[TranscriptSegment],
    ) -> dict:
        """Analisa segmentos de transcricao e retorna metricas agregadas.

        Args:
            segments: Lista de TranscriptSegment para analise.

        Returns:
            Dicionario com: total_segments, total_duration_seconds,
            total_words, avg_confidence, speakers.

        Raises:
            InvalidTranscriptError: Se a lista de segmentos for vazia.
        """
        if not segments:
            raise InvalidTranscriptError("lista de segmentos nao pode ser vazia")

        total_duration = sum(s.duration for s in segments)
        total_words = sum(s.word_count for s in segments)
        avg_confidence = sum(s.confidence for s in segments) / len(segments)
        speakers = list({s.speaker_label for s in segments if s.speaker_label})

        return {
            "total_segments": len(segments),
            "total_duration_seconds": round(total_duration, 2),
            "total_words": total_words,
            "avg_confidence": round(avg_confidence, 4),
            "speakers": speakers,
        }

    def detect_hook_candidates(
        self,
        segments: list[TranscriptSegment],
    ) -> list[HookCandidate]:
        """Detecta candidatos a hook em segmentos de transcricao.

        Heuristica deterministica:
        - segmentos com >= 5 palavras e duracao <= 20s recebem score proporcional
          ao word_count / duration (densidade de informacao)
        - confidence do segmento afeta o score final

        Args:
            segments: Lista de TranscriptSegment.

        Returns:
            Lista de HookCandidate ordenada por score decrescente.
        """
        if not segments:
            return []

        candidates: list[HookCandidate] = []
        for seg in segments:
            if seg.word_count < 5:
                continue
            if seg.duration > 20.0:
                continue

            density = seg.word_count / max(seg.duration, 0.5)
            base_score = min(density / 3.5, 1.0)
            score = round(base_score * seg.confidence, 4)

            if score >= 0.5:
                strength = HookStrength.HIGH
                rationale = "alta densidade de informacao e confianca elevada"
            elif score >= 0.3:
                strength = HookStrength.MEDIUM
                rationale = "densidade moderada de informacao"
            else:
                strength = HookStrength.LOW
                rationale = "densidade baixa ou confianca reduzida"

            candidates.append(HookCandidate.new(
                segment_id=seg.segment_id,
                start_seconds=seg.start_seconds,
                end_seconds=seg.end_seconds,
                hook_text=seg.text,
                strength=strength,
                score=score,
                rationale=rationale,
            ))

        candidates.sort(key=lambda h: h.score, reverse=True)
        return candidates

    def build_cut_plan(
        self,
        source: VideoSource,
        segments: list[TranscriptSegment],
        hooks: list[HookCandidate],
        target_duration: Optional[float] = None,
    ) -> CutPlan:
        """Constroi plano de corte deterministico.

        Logica:
        - Hook HIGH sao KEEP
        - Hook MEDIUM sao TRIM (mantem mas reduz)
        - Segmentos sem hook sao REMOVE
        - Cortes respeitam target_duration se fornecido

        Args:
            source: VideoSource de origem.
            segments: Segmentos de transcricao.
            hooks: Candidatos a hook detectados.
            target_duration: Duracao alvo opcional do reel final.

        Returns:
            CutPlan com instrucoes de corte.

        Raises:
            InvalidCutPlanError: Se source ou segments forem invalidos.
        """
        if not source:
            raise InvalidCutPlanError("source nao pode ser nulo")
        if not segments:
            raise InvalidCutPlanError("segments nao pode ser vazio")

        plan = CutPlan.new(source_id=source.source_id)
        hook_ids = {h.segment_id for h in hooks}

        for seg in segments:
            seg_hooks = [h for h in hooks if h.segment_id == seg.segment_id]
            if not seg_hooks:
                plan.add_cut(CutInstruction.new(
                    start_seconds=seg.start_seconds,
                    end_seconds=seg.end_seconds,
                    cut_type=CutType.REMOVE,
                    label=f"remove: {seg.text[:40]}",
                    segment_id=seg.segment_id,
                ))
                continue

            best = max(seg_hooks, key=lambda h: h.score)
            if best.strength == HookStrength.HIGH:
                plan.add_cut(CutInstruction.new(
                    start_seconds=seg.start_seconds,
                    end_seconds=seg.end_seconds,
                    cut_type=CutType.KEEP,
                    label=f"keep: {best.hook_text[:40]}",
                    segment_id=seg.segment_id,
                ))
            elif best.strength == HookStrength.MEDIUM:
                mid = (seg.start_seconds + seg.end_seconds) / 2
                half_dur = (seg.end_seconds - seg.start_seconds) / 4
                plan.add_cut(CutInstruction.new(
                    start_seconds=mid - half_dur,
                    end_seconds=mid + half_dur,
                    cut_type=CutType.TRIM,
                    label=f"trim: {best.hook_text[:40]}",
                    segment_id=seg.segment_id,
                ))
            else:
                plan.add_cut(CutInstruction.new(
                    start_seconds=seg.start_seconds,
                    end_seconds=seg.end_seconds,
                    cut_type=CutType.REMOVE,
                    label=f"remove_low: {best.hook_text[:40]}",
                    segment_id=seg.segment_id,
                ))

        if target_duration is not None and target_duration > 0:
            plan = self._trim_to_target(plan, target_duration)

        self._last_cut_plan = plan
        return plan

    def build_reel_script(
        self,
        source: VideoSource,
        cut_plan: CutPlan,
        format: ReelFormat = ReelFormat.STANDARD,
        title: str = "",
    ) -> ReelScript:
        """Constroi roteiro de reel a partir do plano de corte.

        Args:
            source: VideoSource de origem.
            cut_plan: CutPlan com instrucoes de corte.
            format: Formato do reel.
            title: Titulo do reel.

        Returns:
            ReelScript com segmentos numerados.

        Raises:
            InvalidReelScriptError: Se source ou cut_plan forem invalidos.
        """
        if not source:
            raise InvalidReelScriptError("source nao pode ser nulo")
        if not cut_plan:
            raise InvalidReelScriptError("cut_plan nao pode ser nulo")

        title = title or f"Reel — {source.source_id}"
        script = ReelScript.new(
            source_id=source.source_id,
            plan_id=cut_plan.plan_id,
            format=format,
            title=title,
        )

        for i, cut in enumerate(cut_plan.keep_cuts, start=1):
            seg = ReelSegment(
                position=i,
                start_seconds=cut.start_seconds,
                end_seconds=cut.end_seconds,
                narration=cut.label,
                on_screen_text=cut.label,
                transition_hint="dissolve" if i > 1 else "cut",
            )
            script.add_segment(seg)

        self._last_reel_script = script
        return script

    def build_video_package(
        self,
        source: VideoSource,
        segments: list[TranscriptSegment],
        format: ReelFormat = ReelFormat.STANDARD,
        title: str = "",
        target_duration: Optional[float] = None,
        notes: str = "",
    ) -> VideoPackage:
        """Constroi pacote completo de video — orquestra todo o pipeline.

        Pipeline:
        1. analyze_transcript_segments()
        2. detect_hook_candidates()
        3. build_cut_plan()
        4. build_reel_script()
        5. build_caption_specs()
        6. validate_video_package()

        Args:
            source: VideoSource de origem.
            segments: Segmentos de transcricao.
            format: Formato do reel.
            title: Titulo do reel.
            target_duration: Duracao alvo opcional.
            notes: Notas do pacote.

        Returns:
            VideoPackage completo.

        Raises:
            InvalidVideoPackageError: Se source ou segments forem invalidos.
        """
        if not source:
            raise InvalidVideoPackageError("source nao pode ser nulo")
        if not segments:
            raise InvalidVideoPackageError("segments nao pode ser vazio")

        hooks = self.detect_hook_candidates(segments)
        cut_plan = self.build_cut_plan(source, segments, hooks, target_duration)
        reel_script = self.build_reel_script(source, cut_plan, format, title)

        pkg = VideoPackage.new(
            source=source,
            cut_plan=cut_plan,
            reel_script=reel_script,
            notes=notes,
        )

        for hook in hooks:
            pkg.add_hook(hook)

        captions = self._build_caption_specs(reel_script)
        for cap in captions:
            pkg.add_caption_spec(cap)

        self._last_package = pkg
        return pkg

    def validate_video_package(self, package: VideoPackage) -> dict:
        """Valida um VideoPackage e retorna relatorio.

        Args:
            package: VideoPackage a validar.

        Returns:
            Dicionario com: valid, status, validation_errors, warnings, summary.

        Raises:
            ValidationError: Se package for nulo.
        """
        if not package:
            raise ValidationError("package nao pode ser nulo")

        is_valid = package.validate()
        warnings: list[str] = []

        if package.source and package.source.duration_seconds > 600:
            warnings.append("fonte com mais de 10 minutos — verificar relevancia")
        if package.cut_plan and len(package.cut_plan.keep_cuts) < 2:
            warnings.append("menos de 2 cortes mantidos — reel pode ficar curto")
        if not package.hook_candidates:
            warnings.append("nenhum hook detectado — engajamento pode ser baixo")
        if package.reel_script and package.reel_script.total_duration_seconds > 90:
            warnings.append("reel acima de 90s — considerar dividir")

        return {
            "valid": is_valid,
            "status": package.status.value,
            "validation_errors": package.validation_errors,
            "warnings": warnings,
            "summary": {
                "package_id": package.package_id,
                "hooks_detected": len(package.hook_candidates),
                "cuts_total": len(package.cut_plan.cuts) if package.cut_plan else 0,
                "cuts_kept": package.total_clips,
                "reel_segments": package.reel_script.segment_count if package.reel_script else 0,
                "total_duration": package.reel_script.total_duration_seconds if package.reel_script else 0,
                "caption_specs": len(package.caption_specs),
                "strongest_hook_score": package.strongest_hook.score if package.strongest_hook else 0,
            },
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _trim_to_target(plan: CutPlan, target_seconds: float) -> CutPlan:
        """Remove cortes de menor prioridade ate caber no target."""
        keep_cuts = plan.keep_cuts
        if not keep_cuts:
            return plan

        current = sum(c.duration for c in keep_cuts)
        if current <= target_seconds:
            return plan

        sorted_cuts = sorted(keep_cuts, key=lambda c: c.duration)
        removed_ids: set[str] = set()

        for cut in sorted_cuts:
            if current <= target_seconds:
                break
            removed_ids.add(cut.cut_id)
            current -= cut.duration

        plan.cuts = [
            c for c in plan.cuts
            if c.cut_id not in removed_ids or c.cut_type == CutType.REMOVE
        ]
        plan.total_duration_seconds = sum(
            c.duration for c in plan.cuts if c.cut_type != CutType.REMOVE
        )
        return plan

    @staticmethod
    def _build_caption_specs(script: ReelScript) -> list[CaptionOverlaySpec]:
        """Gera CaptionOverlaySpec para cada segmento do script."""
        specs: list[CaptionOverlaySpec] = []
        for seg in script.segments:
            if seg.on_screen_text:
                specs.append(CaptionOverlaySpec.new(
                    text=seg.on_screen_text,
                    position=CaptionPosition.BOTTOM,
                    style=CaptionStyle.BOLD,
                    font_size_hint=48,
                    color_hex="#FFFFFF",
                    start_seconds=seg.start_seconds,
                    end_seconds=seg.end_seconds,
                    animation_hint="fade",
                ))
        return specs


# ------------------------------------------------------------------
# Module-level convenience functions
# ------------------------------------------------------------------

_planner = VideoStudioPlanner()


def analyze_transcript_segments(
    segments: list[TranscriptSegment],
) -> dict:
    """Module-level wrapper for VideoStudioPlanner.analyze_transcript_segments."""
    return _planner.analyze_transcript_segments(segments)


def detect_hook_candidates(
    segments: list[TranscriptSegment],
) -> list[HookCandidate]:
    """Module-level wrapper for VideoStudioPlanner.detect_hook_candidates."""
    return _planner.detect_hook_candidates(segments)


def build_cut_plan(
    source: VideoSource,
    segments: list[TranscriptSegment],
    hooks: list[HookCandidate],
    target_duration: Optional[float] = None,
) -> CutPlan:
    """Module-level wrapper for VideoStudioPlanner.build_cut_plan."""
    return _planner.build_cut_plan(source, segments, hooks, target_duration)


def build_reel_script(
    source: VideoSource,
    cut_plan: CutPlan,
    format: ReelFormat = ReelFormat.STANDARD,
    title: str = "",
) -> ReelScript:
    """Module-level wrapper for VideoStudioPlanner.build_reel_script."""
    return _planner.build_reel_script(source, cut_plan, format, title)


def build_video_package(
    source: VideoSource,
    segments: list[TranscriptSegment],
    format: ReelFormat = ReelFormat.STANDARD,
    title: str = "",
    target_duration: Optional[float] = None,
    notes: str = "",
) -> VideoPackage:
    """Module-level wrapper for VideoStudioPlanner.build_video_package."""
    return _planner.build_video_package(
        source, segments, format, title, target_duration, notes
    )


def validate_video_package(package: VideoPackage) -> dict:
    """Module-level wrapper for VideoStudioPlanner.validate_video_package."""
    return _planner.validate_video_package(package)

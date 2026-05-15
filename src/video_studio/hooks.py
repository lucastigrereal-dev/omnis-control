"""W104 — Hook Detector extending VideoStudioPlanner with criteria-based detection."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.video_studio.models import HookCandidate, HookStrength, TranscriptSegment


@dataclass
class HookCriteria:
    """Criteria-based hook detection result for a single segment."""

    segment_id: str
    text: str
    has_question: bool = False
    has_shock: bool = False
    has_number: bool = False
    has_promise: bool = False
    has_conflict: bool = False
    has_location: bool = False
    score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "segment_id": self.segment_id,
            "text": self.text,
            "has_question": self.has_question,
            "has_shock": self.has_shock,
            "has_number": self.has_number,
            "has_promise": self.has_promise,
            "has_conflict": self.has_conflict,
            "has_location": self.has_location,
            "score": self.score,
        }


class HookDetector:
    """Deterministic hook detector using criteria patterns. No LLM, no API."""

    QUESTION_PATTERNS = [
        r"\?$", r"voce\s+ja\s+imaginou", r"voce\s+sabia",
        r"ja\s+pensou", r"quer\s+saber", r"como\s+seria",
        r"quem\s+aí", r"o\s+que\s+voce",
    ]

    SHOCK_PATTERNS = [
        r"ninguem\s+te\s+conta", r"ninguem\s+sabe", r"escondido",
        r"secreto", r"chocante", r"surpreendente",
        r"inacreditavel", r"nao\s+acreditei",
    ]

    NUMBER_PATTERNS = [
        r"\d+\s*mil", r"\d+\s*milhao|milhões", r"\d+\s*%",
        r"top\s*\d+", r"numero\s*\d+", r"\d+\s*em\s*cada",
        r"\d+\s*vezes", r"\d+\s*anos",
    ]

    PROMISE_PATTERNS = [
        r"garanto", r"prometo", r"resultado",
        r"em\s+\d+\s*dias", r"transform", r"muda",
        r"nunca\s+mais", r"melhor\s+que",
    ]

    CONFLICT_PATTERNS = [
        r"mas\s+nao", r"errado", r"mentira",
        r"diferente\s+do\s+que", r"ao\s+contrario",
        r"engan", r"nao\s+e\s+bem\s+assim",
    ]

    LOCATION_PATTERNS = [
        r"natal", r"praia", r"nordeste", r"brasil",
        r"r[nñ]o?\s+grande\s+do\s+norte", r"rn\b",
        r"pipa", r"maracajau", r"genipabu",
        r"pontanegra", r"ponta\s+negra",
    ]

    def __init__(self, max_hooks: int = 10):
        self.max_hooks = max_hooks

    def detect(self, segments: list[TranscriptSegment]) -> list[HookCandidate]:
        criteria_results = self._analyze_criteria(segments)
        return self._rank_and_convert(criteria_results)

    def _analyze_criteria(self, segments: list[TranscriptSegment]) -> list[HookCriteria]:
        results: list[HookCriteria] = []
        for seg in segments:
            if seg.word_count < 3:
                continue
            text_lower = seg.text.lower()
            cr = HookCriteria(
                segment_id=seg.segment_id,
                text=seg.text,
                has_question=self._match_any(self.QUESTION_PATTERNS, text_lower),
                has_shock=self._match_any(self.SHOCK_PATTERNS, text_lower),
                has_number=self._match_any(self.NUMBER_PATTERNS, text_lower),
                has_promise=self._match_any(self.PROMISE_PATTERNS, text_lower),
                has_conflict=self._match_any(self.CONFLICT_PATTERNS, text_lower),
                has_location=self._match_any(self.LOCATION_PATTERNS, text_lower),
            )
            cr.score = self._compute_criteria_score(cr)
            results.append(cr)
        return results

    def _rank_and_convert(self, criteria_results: list[HookCriteria]) -> list[HookCandidate]:
        ranked = sorted(criteria_results, key=lambda c: c.score, reverse=True)
        limited = ranked[:self.max_hooks]

        candidates: list[HookCandidate] = []
        for cr in limited:
            strength = (
                HookStrength.HIGH if cr.score >= 0.6
                else HookStrength.MEDIUM if cr.score >= 0.3
                else HookStrength.LOW
            )
            reasons = []
            if cr.has_question: reasons.append("pergunta")
            if cr.has_shock: reasons.append("choque")
            if cr.has_number: reasons.append("numero")
            if cr.has_promise: reasons.append("promessa")
            if cr.has_conflict: reasons.append("conflito")
            if cr.has_location: reasons.append("localidade")

            candidates.append(HookCandidate.new(
                segment_id=cr.segment_id,
                start_seconds=0.0,
                end_seconds=5.0,
                hook_text=cr.text,
                strength=strength,
                score=cr.score,
                rationale=" + ".join(reasons) if reasons else "densidade",
            ))
        return candidates

    @staticmethod
    def _compute_criteria_score(cr: HookCriteria) -> float:
        weight = 0.0
        if cr.has_question: weight += 0.25
        if cr.has_shock: weight += 0.25
        if cr.has_number: weight += 0.15
        if cr.has_promise: weight += 0.15
        if cr.has_conflict: weight += 0.10
        if cr.has_location: weight += 0.10
        return round(min(weight, 1.0), 2)

    @staticmethod
    def _match_any(patterns: list[str], text: str) -> bool:
        return any(re.search(p, text) for p in patterns)

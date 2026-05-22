"""CaptionFactory — batch Instagram caption generation with parallel LLM calls."""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.skills.caption_skill import (
    CaptionRequest,
    CaptionResult,
    CAPTION_SYSTEM_PROMPT,
    build_caption_prompt,
)
from src.skills_bridge.models import SkillCall, SkillIntent


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class BatchCaptionRequest:
    topic: str
    page: str = "@lucastigrereal"
    count: int = 3
    tones: list[str] = field(default_factory=lambda: [
        "autêntico e caloroso",
        "informativo e educativo",
        "urgente e persuasivo",
    ])
    formats: list[str] = field(default_factory=lambda: [
        "carrossel", "reel", "feed",
    ])
    target_audience: str = "viajantes e famílias"
    max_words: int = 150
    include_hashtags: bool = True
    include_cta: bool = True

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "page": self.page,
            "count": self.count,
            "tones": self.tones,
            "formats": self.formats,
            "target_audience": self.target_audience,
            "max_words": self.max_words,
            "include_hashtags": self.include_hashtags,
            "include_cta": self.include_cta,
        }

    def individual_requests(self) -> list[CaptionRequest]:
        """Expand into N individual CaptionRequest objects with rotating tones/formats."""
        requests = []
        for i in range(self.count):
            tone = self.tones[i % len(self.tones)]
            fmt = self.formats[i % len(self.formats)]
            requests.append(CaptionRequest(
                topic=self.topic,
                page=self.page,
                tone=f"{tone} para formato {fmt}",
                target_audience=self.target_audience,
                max_words=self.max_words,
                include_hashtags=self.include_hashtags,
                include_cta=self.include_cta,
            ))
        return requests


@dataclass
class BatchCaptionResult:
    request: BatchCaptionRequest
    captions: list[CaptionResult] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)
    total_time_ms: int = 0
    errors: list[dict] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return len(self.captions)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def to_dict(self) -> dict:
        return {
            "request": self.request.to_dict(),
            "captions": [c.to_dict() for c in self.captions],
            "generated_at": self.generated_at,
            "total_time_ms": self.total_time_ms,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "errors": self.errors,
        }

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


def _build_combined_prompt(request: CaptionRequest) -> str:
    """Combine system + user prompt into a single string for the adapter.

    The adapter passes 'system' as a kwarg to OllamaAdapter, which now
    constructs proper [system, user] messages. The prompt field is the
    user message.
    """
    return build_caption_prompt(request)


class CaptionFactory:
    """Generates multiple Instagram captions in parallel via ThreadPoolExecutor."""

    def __init__(self, adapter=None, dry_run: bool = True, max_workers: int = 4):
        self.dry_run = dry_run
        self.max_workers = max_workers
        self._adapter = adapter

    @property
    def adapter(self):
        if self._adapter is None:
            from src.skills_bridge.adapter import RealSkillAdapter
            self._adapter = RealSkillAdapter(dry_run=self.dry_run)
        return self._adapter

    def _generate_one(self, req: CaptionRequest, idx: int) -> CaptionResult:
        """Generate a single caption (called by worker threads)."""
        prompt = build_caption_prompt(req)

        # If research hint is attached, append it to the prompt for richer output
        hint = getattr(req, '_research_hint', '')
        if hint:
            prompt = f"{prompt}\n\n{hint}"

        call = SkillCall(
            skill_id="generate_caption",
            intent=SkillIntent.GENERATE,
            input_payload={
                "prompt": prompt,
                "system": CAPTION_SYSTEM_PROMPT,
                "topic": req.topic,
                "page": req.page,
            },
            dry_run=self.dry_run,
        )

        result = self.adapter.call_skill(call)

        if result["status"] in ("ok", "dry_run"):
            return CaptionResult.from_llm_response(
                result["output"],
                req,
                model_used=result.get("model_used", "unknown"),
            )
        else:
            raise RuntimeError(
                f"Caption {idx} failed: {result.get('error', result.get('status', 'unknown'))}"
            )

    def produce_batch(self, request: BatchCaptionRequest) -> BatchCaptionResult:
        """Generate N captions in parallel using ThreadPoolExecutor."""
        t0 = time.perf_counter()
        individual = request.individual_requests()
        batch_result = BatchCaptionResult(request=request)

        with ThreadPoolExecutor(max_workers=min(self.max_workers, request.count)) as executor:
            futures = {
                executor.submit(self._generate_one, req, i): i
                for i, req in enumerate(individual)
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    caption = future.result()
                    batch_result.captions.append(caption)
                except Exception as exc:
                    batch_result.errors.append({
                        "index": idx,
                        "error": str(exc),
                    })

        batch_result.total_time_ms = int((time.perf_counter() - t0) * 1000)
        return batch_result

    def produce_batch_with_research(
        self,
        request: BatchCaptionRequest,
        research_context=None,
    ) -> BatchCaptionResult:
        """Generate N captions enriched with memory research context.

        The research context adds top hooks, saturated themes, viral patterns,
        and book/obsidian insights to the LLM prompt for higher-quality output.
        Returns the same BatchCaptionResult as produce_batch.
        """
        if research_context is not None and not research_context.is_empty:
            hint = research_context.to_prompt_hint()
            individual = request.individual_requests()
            for req in individual:
                req._research_hint = hint
        return self.produce_batch(request)

    def produce_and_save(
        self,
        request: BatchCaptionRequest,
        output_dir: str | Path,
    ) -> BatchCaptionResult:
        """Generate batch and save all results to files."""
        result = self.produce_batch(request)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save manifest
        result.save(str(output_dir / "batch_manifest.json"))

        # Save individual captions
        for i, caption in enumerate(result.captions):
            caption.save(str(output_dir / f"caption_{i+1:02d}.json"))
            txt_path = output_dir / f"caption_{i+1:02d}.txt"
            txt_path.write_text(caption.caption, encoding="utf-8")

        return result

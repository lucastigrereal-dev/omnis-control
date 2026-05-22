"""PublishOrchestrator — end-to-end: generate → QA → approve → publish."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class PublishManifest:
    """Record of a single post through the full pipeline."""
    post_id: str = ""
    caption: str = ""
    hook: str = ""
    hashtags: list[str] = field(default_factory=list)
    page: str = ""
    topic: str = ""
    model_used: str = ""
    score: int = 0
    approved: bool = False
    scheduled_at: str = ""
    status: str = ""  # generated | approved | scheduled | published | failed
    error: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "post_id": self.post_id,
            "caption": self.caption,
            "hook": self.hook,
            "hashtags": self.hashtags,
            "page": self.page,
            "topic": self.topic,
            "model_used": self.model_used,
            "score": self.score,
            "approved": self.approved,
            "scheduled_at": self.scheduled_at,
            "status": self.status,
            "error": self.error,
            "created_at": self.created_at,
        }


@dataclass
class BatchPublishResult:
    """Result of a batch publishing operation."""
    request_topic: str = ""
    generated_count: int = 0
    approved_count: int = 0
    scheduled_count: int = 0
    failed_count: int = 0
    manifests: list[PublishManifest] = field(default_factory=list)
    total_time_ms: int = 0
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "request_topic": self.request_topic,
            "generated_count": self.generated_count,
            "approved_count": self.approved_count,
            "scheduled_count": self.scheduled_count,
            "failed_count": self.failed_count,
            "manifests": [m.to_dict() for m in self.manifests],
            "total_time_ms": self.total_time_ms,
            "generated_at": self.generated_at,
        }

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


class PublishOrchestrator:
    """Orchestrates the complete publishing pipeline: generate → approve → schedule."""

    def __init__(
        self,
        factory=None,   # CaptionFactory
        gate=None,      # ApprovalGate
        publer=None,    # PublerClient
        dry_run: bool = True,
    ):
        self.dry_run = dry_run
        self._factory = factory
        self._gate = gate
        self._publer = publer

    @property
    def factory(self):
        if self._factory is None:
            from src.skills.caption_factory import CaptionFactory
            self._factory = CaptionFactory(dry_run=self.dry_run)
        return self._factory

    @property
    def gate(self):
        if self._gate is None:
            from src.publishing.approval_gate import ApprovalGate
            self._gate = ApprovalGate(mode="auto", auto_approve_threshold=85)
        return self._gate

    @property
    def publer(self):
        if self._publer is None:
            from src.publishing.publer_client import PublerClient
            self._publer = PublerClient()
        return self._publer

    def publish_single(
        self,
        topic: str,
        page: str,
        tone: str = "autêntico e caloroso",
        scheduled_at: str | None = None,
        score_threshold: int = 60,
    ) -> PublishManifest:
        """Generate ONE caption → QA → approve → schedule. Returns manifest."""
        from src.skills.caption_factory import BatchCaptionRequest

        req = BatchCaptionRequest(
            topic=topic,
            page=page,
            count=1,
            tones=[tone],
            formats=["feed"],
        )
        batch = self.factory.produce_batch(req)

        if batch.success_count == 0:
            return PublishManifest(
                topic=topic, page=page, status="failed",
                error=batch.errors[0]["error"] if batch.errors else "no captions generated",
            )

        caption = batch.captions[0]
        manifest = PublishManifest(
            caption=caption.caption,
            hook=caption.hook,
            hashtags=caption.hashtags,
            page=page,
            topic=topic,
            model_used=caption.model_used,
            status="generated",
        )

        # Score — use hashtag count and caption length as basic quality proxy
        score = self._score_caption(caption)
        manifest.score = score

        if score < score_threshold:
            manifest.status = "failed"
            manifest.error = f"score {score} < threshold {score_threshold}"
            return manifest

        # Approval
        decision = self.gate.request_approval(
            content=caption.caption,
            content_type="caption",
            page=page,
            score=score,
            scheduled_at=scheduled_at,
        )
        manifest.approved = decision.approved

        if not decision.approved:
            manifest.status = "rejected"
            manifest.error = decision.reason
            return manifest

        manifest.status = "approved"

        # Publish (or mock schedule)
        account = self.publer.get_account_by_handle(page)
        account_id = account.account_id if account else "acc_mock"

        if self.dry_run:
            manifest.status = "scheduled"
            manifest.scheduled_at = scheduled_at or _now_iso()
            manifest.post_id = f"dry_{manifest.hook[:20]}"
        else:
            result = self.publer.schedule_post(
                caption=caption.caption,
                account_id=account_id,
                scheduled_at=scheduled_at or _now_iso(),
            )
            manifest.post_id = result.post_id
            manifest.status = result.status
            manifest.scheduled_at = result.scheduled_at
            if result.error:
                manifest.error = result.error

        return manifest

    def publish_batch(
        self,
        topic: str,
        page: str,
        count: int = 3,
        tones: list[str] | None = None,
        scheduled_at: str | None = None,
        score_threshold: int = 60,
    ) -> BatchPublishResult:
        """Generate N captions → QA → approve → schedule. Returns batch result."""
        import time
        from src.skills.caption_factory import BatchCaptionRequest

        t0 = time.perf_counter()

        if tones is None:
            tones = ["autêntico e caloroso", "informativo e educativo", "urgente e persuasivo"]

        req = BatchCaptionRequest(
            topic=topic, page=page, count=count, tones=tones,
            formats=["feed"] * count,
        )
        batch = self.factory.produce_batch(req)

        result = BatchPublishResult(
            request_topic=topic,
            generated_count=batch.success_count,
        )

        for caption in batch.captions:
            score = self._score_caption(caption)
            decision = self.gate.request_approval(
                content=caption.caption,
                content_type="caption",
                page=page,
                score=score,
                scheduled_at=scheduled_at,
            )

            manifest = PublishManifest(
                caption=caption.caption,
                hook=caption.hook,
                hashtags=caption.hashtags,
                page=page,
                topic=topic,
                model_used=caption.model_used,
                score=score,
                approved=decision.approved,
                scheduled_at=scheduled_at or "",
                status="approved" if decision.approved else "rejected",
                error="" if decision.approved else decision.reason,
            )

            if decision.approved:
                result.approved_count += 1

                if self.dry_run:
                    manifest.status = "scheduled"
                    manifest.scheduled_at = scheduled_at or _now_iso()
                    manifest.post_id = f"dry_{topic[:15].replace(' ', '_')}_{result.scheduled_count}"
                    result.scheduled_count += 1
                else:
                    account = self.publer.get_account_by_handle(page)
                    pub_result = self.publer.schedule_post(
                        caption=caption.caption,
                        account_id=account.account_id if account else "acc_mock",
                        scheduled_at=scheduled_at or _now_iso(),
                    )
                    manifest.post_id = pub_result.post_id
                    manifest.status = pub_result.status
                    manifest.scheduled_at = pub_result.scheduled_at
                    if pub_result.error:
                        manifest.error = pub_result.error
                        manifest.status = "failed"
                        result.failed_count += 1
                    else:
                        result.scheduled_count += 1
            else:
                result.failed_count += 1

            result.manifests.append(manifest)

        result.total_time_ms = int((time.perf_counter() - t0) * 1000)
        return result

    def _score_caption(self, caption) -> int:
        """Simple quality score based on structure. Replace with evaluate_content MCP later."""
        score = 50
        # Hook has content
        if caption.hook and len(caption.hook) > 5:
            score += 10
        # Has hashtags
        if caption.hashtags:
            score += min(15, len(caption.hashtags) * 5)
        # Has CTA (salva, compartilha, comenta, pergunta)
        lower = caption.caption.lower()
        cta_words = ["salva", "compartilha", "comenta", "me conta", "qual", "você"]
        if any(w in lower for w in cta_words):
            score += 10
        # Good length (80-200 words)
        word_count = len(caption.caption.split())
        if 80 <= word_count <= 200:
            score += 15
        elif word_count > 50:
            score += 5
        # Has emojis
        if any(c in caption.caption for c in "🌊🌞🔥💛✨🌴📍"):
            score += 5
        return min(100, score)

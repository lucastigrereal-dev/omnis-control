"""Pipeline IDEA->PUBLISH — orquestrador com MetaAPIDryRun e JsonLStore."""
from __future__ import annotations
import uuid
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path

from .statemachine import ContentContext, ContentStatus, InvalidTransitionError

logger = logging.getLogger("omnis.publisher.pipeline")


class JsonLStore:
    """Armazenamento local JSONL (substitui SupabaseClient para dry-run)."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.dir = data_dir or Path(__file__).parent.parent.parent / "data" / "publisher_store"
        self.dir.mkdir(parents=True, exist_ok=True)
        self._items_path = self.dir / "content_items.jsonl"
        self._queue_path = self.dir / "publish_queue.jsonl"
        self._transitions_path = self.dir / "transitions.jsonl"

    # --- content_items CRUD ---
    def _read_items(self) -> List[Dict]:
        if not self._items_path.exists():
            return []
        with open(self._items_path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def _write_items(self, items: List[Dict]) -> None:
        with open(self._items_path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")

    def insert(self, table: str, data: Dict) -> str:
        if table == "content_items":
            items = self._read_items()
            data.setdefault("id", str(uuid.uuid4()))
            items.append(data)
            self._write_items(items)
            return data["id"]
        elif table == "content_transitions":
            with open(self._transitions_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False, default=str) + "\n")
            return data.get("id", "")
        raise ValueError(f"Tabela desconhecida: {table}")

    def get(self, table: str, content_id: str) -> Optional[Dict]:
        if table == "content_items":
            for item in self._read_items():
                if item.get("id") == content_id:
                    return item
        return None

    def update(self, table: str, content_id: str, data: Dict) -> None:
        if table == "content_items":
            items = self._read_items()
            for i, item in enumerate(items):
                if item.get("id") == content_id:
                    items[i] = {**item, **data}
                    self._write_items(items)
                    return

    def query(self, table: str, filters: Dict) -> List[Dict]:
        if table == "content_items":
            return [
                item for item in self._read_items()
                if all(item.get(k) == v for k, v in filters.items())
            ]
        return []

    def execute_raw(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """Mock de SQL raw — SKIP LOCKED simulado via log."""
        logger.debug("SQL raw (dry-run)", extra={"sql": sql[:80], "params": params})
        return []


class PublishPipeline:
    """Pipeline unico IDEA->PUBLISH com idempotencia e audit trail."""

    def __init__(self, meta_client=None, argos_bridge=None, db: Optional[JsonLStore] = None):
        from ..integrations.metaapi_dryrun import MetaAPIDryRun
        self.meta = meta_client or MetaAPIDryRun()
        self.argos = argos_bridge
        self.db = db or JsonLStore()

    async def stage_idea_to_brief(self, ctx: ContentContext, brief_prompt: str) -> ContentContext:
        try:
            brief = await self._call_jarvis_brief(ctx.title, brief_prompt)
            ctx.body = brief.get("body", "")
            ctx.format = brief.get("format", "post")
            ctx = ctx.transition_to(ContentStatus.BRIEF, actor="jarvis", reason="Brief gerado")
            self._persist(ctx)
            return ctx
        except Exception as e:
            ctx.record_error(str(e), "idea_to_brief")
            ctx = ctx.transition_to(ContentStatus.FAILED, actor="system", reason=str(e))
            self._persist(ctx)
            raise

    async def stage_brief_to_draft(self, ctx: ContentContext) -> ContentContext:
        try:
            draft = await self._call_jarvis_draft(ctx.body, ctx.format)
            ctx.caption = draft.get("caption", "")
            ctx.hashtags = draft.get("hashtags", [])
            ctx.media_urls = draft.get("media_urls", [])
            ctx = ctx.transition_to(ContentStatus.DRAFT, actor="jarvis", reason="Draft gerado")
            self._persist(ctx)
            return ctx
        except Exception as e:
            ctx.record_error(str(e), "brief_to_draft")
            ctx = ctx.transition_to(ContentStatus.FAILED, actor="system", reason=str(e))
            self._persist(ctx)
            raise

    async def stage_draft_to_review(self, ctx: ContentContext) -> ContentContext:
        ctx = ctx.transition_to(ContentStatus.REVIEW, actor="system", reason="Aguardando aprovacao")
        self._persist(ctx)
        return ctx

    async def approve(self, content_id: str, approver: str) -> ContentContext:
        ctx = self._load(content_id)
        ctx = ctx.transition_to(ContentStatus.APPROVED, actor=f"human:{approver}", reason="Aprovado")
        self._persist(ctx)
        return ctx

    async def reject(self, content_id: str, approver: str, reason: str) -> ContentContext:
        ctx = self._load(content_id)
        ctx = ctx.transition_to(ContentStatus.DRAFT, actor=f"human:{approver}", reason=f"Rejeitado: {reason}")
        self._persist(ctx)
        return ctx

    async def stage_approved_to_queued(self, ctx: ContentContext) -> ContentContext:
        self.db.insert("publish_queue", {
            "content_item_id": ctx.content_id,
            "priority": 5,
        })
        ctx = ctx.transition_to(ContentStatus.QUEUED, actor="system", reason="Enfileirado")
        self._persist(ctx)
        return ctx

    async def stage_publish(self, ctx: ContentContext) -> ContentContext:
        try:
            ctx = ctx.transition_to(ContentStatus.PUBLISHING, actor="worker")
            self._persist(ctx)

            existing = self.db.query("content_items", {
                "idempotency_key": ctx.idempotency_key, "status": "published"
            })
            if existing:
                logger.info("Ja publicado, pulando", extra={"content_id": ctx.content_id})
                ctx.status = ContentStatus.PUBLISHED
                return ctx

            result = await self.meta.publish(
                caption=ctx.caption or "",
                hashtags=ctx.hashtags,
                media_urls=ctx.media_urls,
                format=ctx.format,
                idempotency_key=ctx.idempotency_key,
            )

            ctx = ctx.transition_to(
                ContentStatus.PUBLISHED, actor="meta_api",
                payload={"external_post_id": result["id"]},
                reason="Publicado (dry-run)",
            )
            self._persist(ctx, extra={"external_post_id": result["id"]})
            return ctx

        except Exception as e:
            ctx.record_error(str(e), "publish")
            if ctx.can_retry:
                ctx = ctx.transition_to(ContentStatus.FAILED, actor="system", reason=str(e))
            else:
                ctx = ctx.transition_to(ContentStatus.FAILED, actor="system", reason=f"Max retries: {e}")
            self._persist(ctx)
            raise

    async def run_full_pipeline(self, content_id: str, brief_prompt: str = "") -> ContentContext:
        ctx = self._load(content_id)
        stages = [
            (ContentStatus.IDEA, self.stage_idea_to_brief, {"brief_prompt": brief_prompt}),
            (ContentStatus.BRIEF, self.stage_brief_to_draft, {}),
            (ContentStatus.DRAFT, self.stage_draft_to_review, {}),
            (ContentStatus.APPROVED, self.stage_approved_to_queued, {}),
            (ContentStatus.QUEUED, self.stage_publish, {}),
        ]
        for expected_status, stage_fn, kwargs in stages:
            if ctx.status == expected_status:
                ctx = await stage_fn(ctx, **kwargs)
                if ctx.status == ContentStatus.FAILED:
                    break
        return ctx

    def _persist(self, ctx: ContentContext, extra: Optional[Dict] = None) -> None:
        data = {
            "status": ctx.status.value,
            "caption": ctx.caption,
            "hashtags": ctx.hashtags,
            "media_urls": ctx.media_urls,
            "retry_count": ctx.retry_count,
            "error_log": ctx.error_log,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            data.update(extra)
        self.db.update("content_items", ctx.content_id, data)
        if ctx.transitions:
            last = ctx.transitions[-1]
            self.db.insert("content_transitions", {
                "content_item_id": ctx.content_id,
                "from_status": last["from"],
                "to_status": last["to"],
                "actor": last["actor"],
                "reason": last.get("reason", ""),
                "payload": last.get("payload", {}),
            })

    def _load(self, content_id: str) -> ContentContext:
        row = self.db.get("content_items", content_id)
        if not row:
            raise KeyError(f"Content {content_id} not found")
        return ContentContext(
            content_id=row["id"],
            title=row.get("title", ""),
            account_handle=row.get("account_handle", ""),
            status=ContentStatus(row.get("status", "idea")),
            body=row.get("body"),
            caption=row.get("caption"),
            hashtags=row.get("hashtags", []),
            media_urls=row.get("media_urls", []),
            format=row.get("format", "post"),
            idempotency_key=row.get("idempotency_key", str(uuid.uuid4())),
            retry_count=row.get("retry_count", 0),
            error_log=row.get("error_log", []),
        )

    async def _call_jarvis_brief(self, title: str, prompt: str) -> Dict[str, Any]:
        return {"body": f"Brief: {title}\n{prompt}", "format": "post"}

    async def _call_jarvis_draft(self, body: str, fmt: str) -> Dict[str, Any]:
        return {
            "caption": f"Caption gerada: {body[:200]}",
            "hashtags": ["#omnis", "#dryrun"],
            "media_urls": [],
        }

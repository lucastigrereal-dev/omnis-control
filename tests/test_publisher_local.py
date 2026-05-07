"""Tests for Publisher Local Dry-Run module."""
import pytest
from pathlib import Path
from src.publisher.statemachine import (
    ContentStatus, ContentContext, InvalidTransitionError, ALLOWED_TRANSITIONS
)
from src.publisher.pipeline import PublishPipeline, JsonLStore
from src.integrations.metaapi_dryrun import MetaAPIDryRun


class TestStateMachine:
    def test_valid_transition(self):
        ctx = ContentContext(content_id="test-1", title="Post 1")
        ctx.transition_to(ContentStatus.BRIEF)
        assert ctx.status == ContentStatus.BRIEF

    def test_invalid_transition_raises(self):
        ctx = ContentContext(content_id="test-1", title="Post 1")
        ctx.status = ContentStatus.IDEA
        with pytest.raises(InvalidTransitionError):
            ctx.transition_to(ContentStatus.PUBLISHED)

    def test_terminal_state_has_no_transitions(self):
        assert ALLOWED_TRANSITIONS[ContentStatus.PUBLISHED] == []

    def test_can_retry_under_max(self):
        ctx = ContentContext(content_id="test-1", title="Post 1", max_retries=3)
        assert ctx.can_retry is True
        ctx.retry_count = 3
        assert ctx.can_retry is False

    def test_record_error_appends(self):
        ctx = ContentContext(content_id="test-1", title="Post 1")
        ctx.record_error("erro de teste", "test_stage")
        assert len(ctx.error_log) == 1
        assert ctx.retry_count == 1


class TestPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_create_and_run(self, tmp_path):
        store = JsonLStore(data_dir=tmp_path)
        pipe = PublishPipeline(db=store)

        import uuid
        content_id = str(uuid.uuid4())
        store.insert("content_items", {
            "id": content_id,
            "title": "Teste",
            "status": "idea",
            "idempotency_key": str(uuid.uuid4()),
        })

        ctx = pipe._load(content_id)
        ctx = await pipe.stage_idea_to_brief(ctx, "test brief")
        assert ctx.status == ContentStatus.BRIEF

    @pytest.mark.asyncio
    async def test_pipeline_full_dry_run(self, tmp_path):
        store = JsonLStore(data_dir=tmp_path)
        pipe = PublishPipeline(db=store)

        import uuid
        content_id = str(uuid.uuid4())
        store.insert("content_items", {
            "id": content_id,
            "title": "Dry Run Test",
            "status": "idea",
            "idempotency_key": str(uuid.uuid4()),
        })

        ctx = await pipe.run_full_pipeline(content_id, "brief")
        assert ctx.status == ContentStatus.REVIEW  # para em REVIEW (espera aprovacao humana)

    def test_metaapi_dryrun_publish(self, tmp_path):
        import asyncio
        api = MetaAPIDryRun(dry_run_dir=tmp_path)
        result = asyncio.run(api.publish(
            caption="Test", hashtags=["#tag"], media_urls=[], format="post",
            idempotency_key="key-001"
        ))
        assert result["status"] == "published_dry_run"
        assert result["id"].startswith("dryrun_")

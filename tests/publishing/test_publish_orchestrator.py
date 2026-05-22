"""Tests for PublishOrchestrator — end-to-end publishing pipeline."""
from __future__ import annotations

import json

import pytest

from src.publishing.publish_orchestrator import (
    PublishOrchestrator,
    PublishManifest,
    BatchPublishResult,
)


class TestPublishManifest:
    def test_manifest_defaults(self):
        m = PublishManifest(caption="Test", hook="Hook", page="@test", topic="topic")
        assert m.status == ""
        assert m.approved is False

    def test_manifest_to_dict(self):
        m = PublishManifest(
            post_id="pub_001",
            caption="Full caption",
            hook="The hook",
            hashtags=["#test"],
            page="@test",
            topic="testing",
            model_used="mock",
            score=75,
            approved=True,
            scheduled_at="2026-05-25T09:00:00-03:00",
            status="scheduled",
        )
        d = m.to_dict()
        assert d["status"] == "scheduled"
        assert d["approved"] is True
        assert d["score"] == 75


class TestBatchPublishResult:
    def test_empty_result(self):
        r = BatchPublishResult(request_topic="test")
        assert r.generated_count == 0
        assert r.approved_count == 0
        assert r.scheduled_count == 0

    def test_save_to_file(self, tmp_path):
        r = BatchPublishResult(
            request_topic="test batch",
            generated_count=3,
            approved_count=2,
            scheduled_count=2,
            failed_count=1,
            manifests=[
                PublishManifest(
                    post_id="p1", caption="C1", hook="H1",
                    page="@test", topic="t", status="scheduled",
                    scheduled_at="2026-05-25T09:00:00-03:00",
                ),
            ],
            total_time_ms=5000,
        )
        path = tmp_path / "batch_result.json"
        r.save(str(path))
        assert path.exists()
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["scheduled_count"] == 2
        assert loaded["generated_count"] == 3
        assert len(loaded["manifests"]) == 1


class TestPublishOrchestrator:
    def test_orchestrator_creation_defaults(self):
        orch = PublishOrchestrator(dry_run=True)
        assert orch.dry_run is True
        assert orch.gate.mode == "auto"
        assert orch.publer.is_mock is True

    def test_orchestrator_accepts_custom_components(self):
        from src.publishing.approval_gate import ApprovalGate
        from src.publishing.publer_client import PublerClient
        from src.skills.caption_factory import CaptionFactory

        factory = CaptionFactory(dry_run=True)
        gate = ApprovalGate(mode="auto", auto_approve_threshold=75)
        publer = PublerClient()
        orch = PublishOrchestrator(factory=factory, gate=gate, publer=publer, dry_run=True)

        assert orch.factory is factory
        assert orch.gate is gate
        assert orch.publer is publer

    def test_publish_single_dry_run(self):
        orch = PublishOrchestrator(dry_run=True)
        manifest = orch.publish_single(
            topic="viagem em Natal",
            page="@lucastigrereal",
            tone="autêntico",
        )
        assert manifest.status in ("scheduled", "rejected", "failed")
        assert manifest.topic == "viagem em Natal"
        assert len(manifest.caption) > 0
        assert manifest.score >= 0
        assert manifest.score <= 100

    def test_publish_single_high_score_succeeds(self):
        orch = PublishOrchestrator(dry_run=True)
        # Set approval threshold low to ensure approval
        orch.gate.auto_approve_threshold = 0
        manifest = orch.publish_single(
            topic="test easy approval",
            page="@lucastigrereal",
            score_threshold=0,
        )
        assert manifest.approved is True
        assert manifest.status == "scheduled"
        assert manifest.post_id.startswith("dry_")

    def test_publish_single_low_score_blocked(self):
        orch = PublishOrchestrator(dry_run=True)
        manifest = orch.publish_single(
            topic="test",
            page="@lucastigrereal",
            score_threshold=101,  # impossible threshold
        )
        assert manifest.status == "failed"
        assert "score" in manifest.error

    def test_publish_batch_dry_run(self):
        orch = PublishOrchestrator(dry_run=True)
        orch.gate.auto_approve_threshold = 0  # approve all
        result = orch.publish_batch(
            topic="viagem em família",
            page="@afamiliatigrereal",
            count=2,
            tones=["autêntico", "informativo"],
            score_threshold=0,
        )
        assert result.generated_count == 2
        assert result.approved_count == 2
        assert result.scheduled_count == 2
        assert result.total_time_ms >= 0  # dry_run may be 0ms
        assert len(result.manifests) == 2
        for m in result.manifests:
            assert m.status == "scheduled"
            assert m.post_id.startswith("dry_")

    def test_publish_batch_rejected_items_not_scheduled(self):
        orch = PublishOrchestrator(dry_run=True)
        orch.gate.auto_approve_threshold = 100  # reject all
        result = orch.publish_batch(
            topic="test rejection",
            page="@lucastigrereal",
            count=2,
            tones=["a", "b"],
            score_threshold=0,
        )
        assert result.generated_count == 2
        assert result.approved_count == 0
        assert result.scheduled_count == 0
        assert result.failed_count == 2

    def test_publish_batch_save_result(self, tmp_path):
        orch = PublishOrchestrator(dry_run=True)
        orch.gate.auto_approve_threshold = 0
        result = orch.publish_batch(
            topic="test save",
            page="@test",
            count=2,
            score_threshold=0,
        )
        result.save(str(tmp_path / "publish_result.json"))
        assert (tmp_path / "publish_result.json").exists()

    def test_score_caption_method(self):
        orch = PublishOrchestrator(dry_run=True)
        from src.skills.caption_skill import CaptionResult

        caption = CaptionResult(
            caption="Ótimo hook!\n\nTexto legal com bastante conteúdo e informação relevante. "
                    "Salva esse post pra planejar sua próxima viagem! 🌊💛\n\n#test #viagem",
            hook="Ótimo hook!",
            hashtags=["#test", "#viagem"],
            topic="test",
            page="@test",
            model_used="mock",
        )
        score = orch._score_caption(caption)
        assert score >= 70  # good structure should score well

    def test_score_caption_minimum(self):
        orch = PublishOrchestrator(dry_run=True)
        from src.skills.caption_skill import CaptionResult

        caption = CaptionResult(
            caption="short",
            hook="s",
            hashtags=[],
            topic="t",
            page="@test",
            model_used="mock",
        )
        score = orch._score_caption(caption)
        assert score >= 50  # base score
        assert score < 70    # no extra points for structure

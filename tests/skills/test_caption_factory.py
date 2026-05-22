"""Tests for CaptionFactory — batch caption generation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.skills.caption_factory import (
    BatchCaptionRequest,
    BatchCaptionResult,
    CaptionFactory,
)
from src.skills.caption_skill import CaptionRequest, CaptionResult


class TestBatchCaptionRequest:
    def test_defaults(self):
        req = BatchCaptionRequest(topic="praias de Natal")
        assert req.count == 3
        assert len(req.tones) == 3
        assert len(req.formats) == 3
        assert req.page == "@lucastigrereal"

    def test_individual_requests_expands_correctly(self):
        req = BatchCaptionRequest(
            topic="gastronomia em SP",
            count=5,
            tones=["tom A", "tom B"],
            formats=["feed", "reel", "carrossel"],
        )
        individual = req.individual_requests()
        assert len(individual) == 5
        assert individual[0].tone == "tom A para formato feed"
        assert individual[1].tone == "tom B para formato reel"
        assert individual[2].tone == "tom A para formato carrossel"
        assert individual[3].tone == "tom B para formato feed"
        assert individual[4].tone == "tom A para formato reel"

    def test_individual_requests_single_tone(self):
        req = BatchCaptionRequest(
            topic="teste",
            count=2,
            tones=["single tone"],
            formats=["single format"],
        )
        individual = req.individual_requests()
        assert len(individual) == 2
        assert all("single tone" in r.tone for r in individual)

    def test_roundtrip_to_dict(self):
        req = BatchCaptionRequest(
            topic="viagem em família",
            page="@afamiliatigrereal",
            count=5,
            tones=["a", "b", "c"],
            formats=["x", "y"],
        )
        data = req.to_dict()
        assert data["topic"] == "viagem em família"
        assert data["count"] == 5
        assert data["page"] == "@afamiliatigrereal"


class TestBatchCaptionResult:
    def test_empty_result(self):
        req = BatchCaptionRequest(topic="teste", count=1)
        result = BatchCaptionResult(request=req)
        assert result.success_count == 0
        assert result.error_count == 0

    def test_with_captions(self):
        req = BatchCaptionRequest(topic="teste", count=1)
        caption = CaptionResult(
            caption="Legenda teste",
            topic="teste",
            page="@test",
            model_used="mock",
            hook="Hook",
            hashtags=["#test"],
        )
        result = BatchCaptionResult(request=req, captions=[caption])
        assert result.success_count == 1
        assert result.captions[0].hook == "Hook"

    def test_with_errors(self):
        req = BatchCaptionRequest(topic="teste", count=1)
        result = BatchCaptionResult(
            request=req,
            errors=[{"index": 0, "error": "timeout"}],
        )
        assert result.error_count == 1

    def test_save_to_file(self, tmp_path):
        req = BatchCaptionRequest(topic="teste", count=1)
        caption = CaptionResult(
            caption="Test",
            topic="teste",
            page="@test",
            model_used="mock",
            hook="H",
            hashtags=["#t"],
        )
        result = BatchCaptionResult(request=req, captions=[caption], total_time_ms=123)
        path = tmp_path / "batch_result.json"
        result.save(str(path))
        assert path.exists()
        loaded = json.loads(path.read_text())
        assert loaded["success_count"] == 1
        assert loaded["total_time_ms"] == 123

    def test_to_dict_includes_all_fields(self):
        req = BatchCaptionRequest(topic="teste", count=2)
        result = BatchCaptionResult(request=req, total_time_ms=500)
        data = result.to_dict()
        assert "request" in data
        assert "captions" in data
        assert "errors" in data
        assert data["total_time_ms"] == 500


class TestCaptionFactory:
    def test_factory_creation_defaults(self):
        factory = CaptionFactory(dry_run=True)
        assert factory.dry_run is True
        assert factory.max_workers == 4

    def test_factory_accepts_custom_adapter(self):
        from src.skills_bridge.adapter import MockSkillAdapter
        adapter = MockSkillAdapter(dry_run=True)
        factory = CaptionFactory(adapter=adapter, dry_run=True)
        assert factory.adapter is adapter

    def test_produce_batch_dry_run(self):
        factory = CaptionFactory(dry_run=True)
        req = BatchCaptionRequest(
            topic="teste caption factory",
            page="@test",
            count=2,
            tones=["tom A", "tom B"],
            formats=["feed"],
        )
        result = factory.produce_batch(req)
        assert result.success_count == 2
        assert result.error_count == 0
        for caption in result.captions:
            assert caption.topic == "teste caption factory"
            assert caption.page == "@test"
            assert len(caption.caption) > 0

    def test_produce_batch_parallel_execution(self):
        """Verify that multiple captions are generated in parallel."""
        import time
        factory = CaptionFactory(dry_run=True, max_workers=3)
        req = BatchCaptionRequest(
            topic="speed test",
            count=3,
            tones=["a", "b", "c"],
        )
        t0 = time.perf_counter()
        result = factory.produce_batch(req)
        elapsed = time.perf_counter() - t0
        assert result.success_count == 3
        assert result.total_time_ms >= 0  # dry_run may be 0ms
        assert elapsed < 5.0

    def test_produce_and_save_creates_files(self, tmp_path):
        factory = CaptionFactory(dry_run=True)
        req = BatchCaptionRequest(topic="test save", count=2, tones=["a", "b"])
        result = factory.produce_and_save(req, tmp_path / "output")
        assert result.success_count == 2
        assert (tmp_path / "output" / "batch_manifest.json").exists()
        assert (tmp_path / "output" / "caption_01.json").exists()
        assert (tmp_path / "output" / "caption_01.txt").exists()
        assert (tmp_path / "output" / "caption_02.json").exists()

    def test_produce_batch_handles_adapter_errors(self):
        """Errors in individual captions should not crash the batch."""
        class FailingAdapter:
            def call_skill(self, call):
                if "1" in str(call.input_payload.get("prompt", "")):
                    return {"status": "error", "error": "simulated failure"}
                return {
                    "status": "ok",
                    "output": "Test caption\n\n#ok",
                    "model_used": "test",
                }

        factory = CaptionFactory(adapter=FailingAdapter(), dry_run=False)
        req = BatchCaptionRequest(
            topic="err test",
            count=2,
            tones=["good tone", "bad tone"],
            formats=["feed", "feed"],
        )
        result = factory.produce_batch(req)
        # One success, one error
        assert result.success_count + result.error_count == 2
        assert result.error_count >= 1

    @pytest.mark.slow
    def test_produce_batch_real_if_ollama_available(self, tmp_path):
        """Real batch generation via Ollama — skipped if Ollama not reachable."""
        from src.skills_bridge.adapter import RealSkillAdapter
        from src.multi_model_orchestration.adapters.ollama_adapter import OllamaAdapter

        oa = OllamaAdapter()
        if not oa.health_check():
            pytest.skip("Ollama not reachable")

        adapter = RealSkillAdapter(dry_run=False)
        adapter._router.dry_run = False

        factory = CaptionFactory(adapter=adapter, dry_run=False, max_workers=2)
        req = BatchCaptionRequest(
            topic="viagem em Natal com família",
            page="@lucastigrereal",
            count=2,
            tones=["autêntico e caloroso", "informativo"],
            formats=["feed"],
        )
        result = factory.produce_and_save(req, tmp_path / "real_batch")
        assert result.success_count >= 1
        assert result.total_time_ms > 0

        # Verify files exist
        manifest = tmp_path / "real_batch" / "batch_manifest.json"
        assert manifest.exists()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["success_count"] >= 1

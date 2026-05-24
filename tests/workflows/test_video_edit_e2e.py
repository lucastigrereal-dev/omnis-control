"""E2E tests — VideoEditWorkflow: vídeo → transcrição → legenda → akasha → run_id.

Cobertura:
  - dry_run plan (sem Whisper real)
  - full pipeline com VideoProcessorLego monkeypatched
  - propagação do run_id ponta a ponta
  - evento akasha com run_id, transcript, SRT preview
  - geração de SRT a partir do texto
  - recuperação do evento via query_events
  - modelo VideoEditResult (to_dict, properties)
  - tratamento de erros (publish gate, transcription failure)
  - _build_srt helper (dry_run placeholder, real text segmentation)
"""
from __future__ import annotations

import pytest

from src.interfaces.video_processor import VideoResult
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.video_edit_workflow import (
    VideoEditWorkflow,
    VideoEditResult,
    _build_srt,
    _secs_to_srt,
    _COST_LOCAL_PCT,
)


# ── helpers ───────────────────────────────────────────────────────────────────

_FAKE_TRANSCRIPT = (
    "Bem-vindo ao relatório de viagem do nordeste brasileiro. "
    "Visitamos Natal, Fortaleza e João Pessoa. "
    "O litoral nordestino tem praias de água mornas e areia fina. "
    "A culinária local inclui tapioca, carne de sol e acarajé."
)

_FAKE_TRANSCRIPT_DRY = "[dry_run] Transcrição planejada para: sample_video.mp4"


def _mock_lego_success(dry_run: bool = True):
    """Retorna um callable que faz o papel do VideoProcessorLego.execute()."""
    def _execute(spec):
        if dry_run or spec.dry_run:
            return VideoResult(
                success=True,
                output=_FAKE_TRANSCRIPT_DRY,
                files_created=[],
                dry_run=True,
                artifacts={"mode": "dry_run", "language": spec.language},
            )
        return VideoResult(
            success=True,
            output=_FAKE_TRANSCRIPT,
            files_created=["output/video/sample_video_transcript.txt"],
            dry_run=False,
            artifacts={"segments": 4, "language": spec.language, "transcript_path": "output/video/sample_video_transcript.txt"},
        )
    return _execute


def _mock_lego_failure():
    def _execute(spec):
        return VideoResult(success=False, output="", files_created=[], dry_run=spec.dry_run, error="whisper_not_available")
    return _execute


def _make_workflow(dry_run_mode: bool = True) -> tuple[VideoEditWorkflow, MockAkashaSink]:
    from src.legos.video_processor_lego import VideoProcessorLego

    lego = VideoProcessorLego()
    sink = MockAkashaSink()
    wf = VideoEditWorkflow(lego=lego, akasha_sink=sink)
    # monkeypatch execute directly on the instance
    lego.execute = _mock_lego_success(dry_run=dry_run_mode)
    return wf, sink


# ── _build_srt helper ─────────────────────────────────────────────────────────

def test_build_srt_dry_run_placeholder():
    srt = _build_srt("[dry_run] some text")
    assert "dry_run" in srt
    assert "00:00:00,000" in srt


def test_build_srt_empty_returns_placeholder():
    srt = _build_srt("")
    assert srt


def test_build_srt_real_text_has_indices():
    srt = _build_srt("Primeira sentença. Segunda sentença. Terceira.")
    assert "1\n" in srt
    assert "2\n" in srt


def test_build_srt_real_text_has_timestamps():
    srt = _build_srt("Texto de exemplo. Outro trecho.")
    assert "-->" in srt


def test_secs_to_srt_zero():
    assert _secs_to_srt(0) == "00:00:00,000"


def test_secs_to_srt_one_minute():
    assert _secs_to_srt(60) == "00:01:00,000"


def test_secs_to_srt_one_hour():
    assert _secs_to_srt(3600) == "01:00:00,000"


# ── dry_run ───────────────────────────────────────────────────────────────────

def test_dry_run_succeeds():
    wf, _ = _make_workflow(dry_run_mode=True)
    result = wf.run("sample_video.mp4", dry_run=True)
    assert result.success is True
    assert result.dry_run is True


def test_dry_run_creates_run_id():
    wf, _ = _make_workflow(dry_run_mode=True)
    result = wf.run("clip.mp4", dry_run=True)
    assert result.run_id
    assert len(result.run_id) == 12


def test_dry_run_cost_local_pct_is_100():
    wf, _ = _make_workflow(dry_run_mode=True)
    result = wf.run("video.mp4", dry_run=True)
    assert result.cost_local_pct == 100


def test_dry_run_srt_has_placeholder():
    wf, _ = _make_workflow(dry_run_mode=True)
    result = wf.run("video.mp4", dry_run=True)
    assert result.srt
    assert "dry_run" in result.srt or "placeholder" in result.srt


def test_dry_run_writes_event_to_akasha():
    wf, sink = _make_workflow(dry_run_mode=True)
    result = wf.run("video.mp4", dry_run=True)
    events = sink.query_events("video_edit_completed")
    assert len(events) == 1


def test_dry_run_event_source_is_run_id():
    wf, sink = _make_workflow(dry_run_mode=True)
    result = wf.run("video.mp4", dry_run=True)
    events = sink.query_events("video_edit_completed")
    assert events[0].source == result.run_id


def test_dry_run_event_payload_has_video_path():
    wf, sink = _make_workflow(dry_run_mode=True)
    result = wf.run("documentario.mp4", dry_run=True)
    events = sink.query_events("video_edit_completed")
    assert events[0].payload["video_path"] == "documentario.mp4"


def test_dry_run_event_payload_has_run_id():
    wf, sink = _make_workflow(dry_run_mode=True)
    result = wf.run("video.mp4", dry_run=True)
    events = sink.query_events("video_edit_completed")
    assert events[0].payload["run_id"] == result.run_id


def test_dry_run_akasha_event_id_nonempty():
    wf, _ = _make_workflow(dry_run_mode=True)
    result = wf.run("video.mp4", dry_run=True)
    assert result.akasha_event_id
    assert result.akasha_event_id.startswith("ske_")


def test_dry_run_no_files_created():
    wf, _ = _make_workflow(dry_run_mode=True)
    result = wf.run("video.mp4", dry_run=True)
    assert result.files_created == []


# ── full pipeline (monkeypatched lego) ───────────────────────────────────────

def test_full_pipeline_succeeds():
    """E2E principal: vídeo entra, transcrição+legenda saem, guardado no akasha."""
    wf, sink = _make_workflow(dry_run_mode=False)
    result = wf.run("viagem_natal.mp4", dry_run=False)
    assert result.success is True
    assert result.dry_run is False
    assert len(result.transcript) > 50


def test_full_pipeline_transcript_has_content():
    wf, _ = _make_workflow(dry_run_mode=False)
    result = wf.run("video.mp4", dry_run=False)
    assert _FAKE_TRANSCRIPT in result.transcript or len(result.transcript) > 50


def test_full_pipeline_srt_has_sentences():
    wf, _ = _make_workflow(dry_run_mode=False)
    result = wf.run("video.mp4", dry_run=False)
    assert "-->" in result.srt
    assert "1\n" in result.srt


def test_full_pipeline_run_id_in_artifacts():
    wf, _ = _make_workflow(dry_run_mode=False)
    result = wf.run("video.mp4", dry_run=False)
    assert result.artifacts.get("run_id") == result.run_id


def test_full_pipeline_akasha_event_id_in_artifacts():
    wf, _ = _make_workflow(dry_run_mode=False)
    result = wf.run("video.mp4", dry_run=False)
    assert result.artifacts.get("akasha_event_id") == result.akasha_event_id


def test_full_pipeline_event_has_transcript():
    wf, sink = _make_workflow(dry_run_mode=False)
    result = wf.run("video.mp4", dry_run=False)
    events = sink.query_events("video_edit_completed")
    assert len(events[0].payload["transcript"]) > 50


def test_full_pipeline_event_has_srt_preview():
    wf, sink = _make_workflow(dry_run_mode=False)
    wf.run("video.mp4", dry_run=False)
    events = sink.query_events("video_edit_completed")
    assert "srt_preview" in events[0].payload


def test_full_pipeline_cost_local_pct_always_100():
    wf, sink = _make_workflow(dry_run_mode=False)
    wf.run("video.mp4", dry_run=False)
    events = sink.query_events("video_edit_completed")
    assert events[0].payload["cost_local_pct"] == 100


def test_full_pipeline_files_created_nonempty():
    wf, _ = _make_workflow(dry_run_mode=False)
    result = wf.run("video.mp4", dry_run=False)
    assert result.files_created  # monkeypatch returns one file


# ── akasha recovery ───────────────────────────────────────────────────────────

def test_akasha_query_recovers_event_by_type():
    wf, sink = _make_workflow()
    result = wf.run("video.mp4", dry_run=True)
    recovered = sink.query_events("video_edit_completed")
    assert len(recovered) == 1
    assert recovered[0].payload["run_id"] == result.run_id


def test_akasha_event_status_is_written():
    wf, sink = _make_workflow()
    wf.run("video.mp4", dry_run=True)
    events = sink.query_events("video_edit_completed")
    assert events[0].status == SinkStatus.WRITTEN


def test_multiple_runs_produce_separate_events():
    wf, sink = _make_workflow()
    r1 = wf.run("video_a.mp4", dry_run=True)
    r2 = wf.run("video_b.mp4", dry_run=True)
    assert r1.run_id != r2.run_id
    events = sink.query_events("video_edit_completed")
    assert len(events) == 2
    run_ids = {e.payload["run_id"] for e in events}
    assert r1.run_id in run_ids and r2.run_id in run_ids


# ── VideoEditResult model ─────────────────────────────────────────────────────

def test_result_to_dict_has_run_id():
    wf, _ = _make_workflow()
    result = wf.run("video.mp4", dry_run=True)
    d = result.to_dict()
    assert d["run_id"] == result.run_id


def test_result_to_dict_has_success():
    wf, _ = _make_workflow()
    result = wf.run("video.mp4", dry_run=True)
    assert result.to_dict()["success"] is True


def test_result_to_dict_has_cost_local_pct():
    wf, _ = _make_workflow()
    result = wf.run("video.mp4", dry_run=True)
    d = result.to_dict()
    assert d["cost_local_pct"] == _COST_LOCAL_PCT


def test_result_to_dict_has_akasha_event_id():
    wf, _ = _make_workflow()
    result = wf.run("video.mp4", dry_run=True)
    assert result.to_dict()["akasha_event_id"] == result.akasha_event_id


def test_result_segment_count_property():
    r = VideoEditResult(run_id="abc", success=True, artifacts={"segments": 5})
    assert r.segment_count == 5


def test_result_segment_count_default_zero():
    r = VideoEditResult(run_id="abc", success=True)
    assert r.segment_count == 0


# ── error handling ────────────────────────────────────────────────────────────

def test_publish_goal_blocked():
    from src.legos.video_processor_lego import VideoProcessorLego
    lego = VideoProcessorLego()
    sink = MockAkashaSink()
    wf = VideoEditWorkflow(lego=lego, akasha_sink=sink)
    # Override execute to simulate: lego approval gate returns error
    lego.execute = lambda spec: VideoResult(
        success=False, output="", files_created=[], dry_run=False,
        error="approval_required", artifacts={"approval_required": True},
    )
    result = wf.run("video.mp4", dry_run=False)
    assert result.success is False
    assert result.error == "approval_required"


def test_error_result_has_run_id():
    from src.legos.video_processor_lego import VideoProcessorLego
    lego = VideoProcessorLego()
    lego.execute = _mock_lego_failure()
    sink = MockAkashaSink()
    wf = VideoEditWorkflow(lego=lego, akasha_sink=sink)
    result = wf.run("video.mp4", dry_run=True)
    assert result.run_id
    assert len(result.run_id) == 12


def test_error_result_writes_no_akasha_event():
    from src.legos.video_processor_lego import VideoProcessorLego
    lego = VideoProcessorLego()
    lego.execute = _mock_lego_failure()
    sink = MockAkashaSink()
    wf = VideoEditWorkflow(lego=lego, akasha_sink=sink)
    wf.run("video.mp4", dry_run=True)
    events = sink.query_events("video_edit_completed")
    assert len(events) == 0

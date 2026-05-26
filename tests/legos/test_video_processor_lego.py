"""Testes do VideoProcessorLego — OMNIS Lego de Vídeo."""
from __future__ import annotations

import pytest

from src.interfaces.video_processor import VideoSpec, VideoResult
from src.legos.video_processor_lego import (
    VideoProcessorLego,
    _VIDEO_SEMAPHORE,
    _requires_publish_approval,
    _assert_path_safe,
)


# ── _requires_publish_approval ────────────────────────────────────────────────

def test_publish_keyword_detected():
    assert _requires_publish_approval("publicar no Instagram") is True

def test_upload_keyword_detected():
    assert _requires_publish_approval("upload do vídeo") is True

def test_safe_goal_not_flagged():
    assert _requires_publish_approval("transcrever vídeo") is False


# ── approval gate ─────────────────────────────────────────────────────────────

def test_real_publish_goal_blocked():
    lego = VideoProcessorLego()
    spec = VideoSpec(video_path="clip.mp4", goal="publicar no Instagram", dry_run=False)
    result = lego.execute(spec)
    assert result.success is False
    assert result.error == "approval_required"
    assert result.artifacts.get("approval_required") is True


def test_dry_run_not_blocked_by_approval():
    lego = VideoProcessorLego()
    spec = VideoSpec(video_path="clip.mp4", goal="publicar no Instagram", dry_run=True)
    # dry_run ignora gate para publicação
    result = lego.execute(spec)
    assert result.error != "approval_required"


# ── health_check ─────────────────────────────────────────────────────────────

def test_health_check_returns_bool():
    assert isinstance(VideoProcessorLego().health_check(), bool)


def test_health_check_true_when_whisper_and_ffmpeg_available():
    assert VideoProcessorLego().health_check() is True


# ── transcribe dry_run ────────────────────────────────────────────────────────

def test_transcribe_dry_run_no_files():
    lego = VideoProcessorLego()
    spec = VideoSpec(video_path="sample.mp4", goal="transcrever", dry_run=True)
    result = lego.execute(spec)
    assert result.success is True
    assert result.dry_run is True
    assert result.files_created == []
    assert "dry_run" in result.output.lower() or "planejada" in result.output.lower()


def test_transcribe_dry_run_artifacts_mode():
    lego = VideoProcessorLego()
    spec = VideoSpec(video_path="sample.mp4", goal="transcribe", dry_run=True)
    result = lego.execute(spec)
    assert result.artifacts.get("mode") == "dry_run"


# ── cut dry_run (usa FFmpegRenderer que já tem dry_run nativo) ────────────────

def test_cut_dry_run_creates_manifest(tmp_path):
    lego = VideoProcessorLego()
    spec = VideoSpec(
        video_path=str(tmp_path / "video.mp4"),
        goal="cut",
        dry_run=True,
        output_dir=str(tmp_path / "out"),
        start_seconds=0.0,
        end_seconds=10.0,
    )
    result = lego.execute(spec)
    assert result.success is True
    assert result.dry_run is True
    # FFmpegRenderer cria .manifest.json em dry_run
    assert len(result.files_created) == 1
    assert result.files_created[0].endswith(".manifest.json")


# ── extract_audio dry_run ─────────────────────────────────────────────────────

def test_extract_audio_dry_run_no_files():
    lego = VideoProcessorLego()
    spec = VideoSpec(video_path="sample.mp4", goal="extract_audio", dry_run=True)
    result = lego.execute(spec)
    assert result.success is True
    assert result.files_created == []


# ── unknown goal ─────────────────────────────────────────────────────────────

def test_unknown_goal_returns_error():
    lego = VideoProcessorLego()
    spec = VideoSpec(video_path="clip.mp4", goal="fazer magia", dry_run=True)
    result = lego.execute(spec)
    assert result.success is False
    assert "goal desconhecido" in (result.error or "")


def test_transcribe_real_returns_semaphore_timeout_when_busy(monkeypatch):
    lego = VideoProcessorLego()
    monkeypatch.setattr(
        "src.legos.video_processor_lego._VIDEO_SEMAPHORE_TIMEOUT_SECONDS",
        0.1,
    )
    acquired = _VIDEO_SEMAPHORE.acquire(blocking=False)
    assert acquired, "semaphore should be free before test"
    try:
        result = lego.execute(VideoSpec(video_path="sample.mp4", goal="transcribe", dry_run=False))
        assert result.success is False
        assert result.error == "video_semaphore_timeout"
    finally:
        _VIDEO_SEMAPHORE.release()


def test_extract_audio_real_returns_error_when_ffmpeg_fails(monkeypatch, tmp_path):
    lego = VideoProcessorLego()

    class _Proc:
        returncode = 1
        stderr = "ffmpeg failed due to invalid stream"

    monkeypatch.setattr("subprocess.run", lambda *_a, **_k: _Proc())
    spec = VideoSpec(
        video_path=str(tmp_path / "sample.mp4"),
        goal="extract_audio",
        dry_run=False,
        output_dir=str(tmp_path / "out"),
    )
    result = lego.execute(spec)
    assert result.success is False
    assert "ffmpeg failed" in (result.error or "")


def test_extract_audio_real_success_branch(monkeypatch, tmp_path):
    lego = VideoProcessorLego()

    class _Proc:
        returncode = 0
        stderr = ""

    monkeypatch.setattr("subprocess.run", lambda *_a, **_k: _Proc())
    spec = VideoSpec(
        video_path=str(tmp_path / "sample.mp4"),
        goal="extract_audio",
        dry_run=False,
        output_dir=str(tmp_path / "out"),
    )
    result = lego.execute(spec)
    assert result.success is True
    assert len(result.files_created) == 1
    assert result.files_created[0].endswith("_audio.mp3")


# ── P2: path traversal hardening ─────────────────────────────────────────────

def test_assert_path_safe_rejects_dotdot():
    import pytest as _pytest
    with _pytest.raises(ValueError, match="path traversal"):
        _assert_path_safe("../../etc/passwd", "video_path")


def test_assert_path_safe_rejects_windows_dotdot():
    import pytest as _pytest
    with _pytest.raises(ValueError, match="path traversal"):
        _assert_path_safe(r"..\..\..\windows\system32", "output_dir")


def test_assert_path_safe_allows_normal_path():
    _assert_path_safe("videos/input.mp4", "video_path")  # não levanta


def test_assert_path_safe_allows_absolute_no_traversal():
    _assert_path_safe("/tmp/output", "output_dir")  # não levanta


def test_video_path_traversal_rejected_in_execute():
    lego = VideoProcessorLego()
    spec = VideoSpec(video_path="../../etc/passwd", goal="transcrever", dry_run=True)
    result = lego.execute(spec)
    assert result.success is False
    assert "path traversal" in (result.error or "").lower()
    assert result.artifacts.get("blocked") is True


def test_output_dir_traversal_rejected_in_execute():
    lego = VideoProcessorLego()
    spec = VideoSpec(
        video_path="sample.mp4",
        goal="transcrever",
        dry_run=True,
        output_dir="../../../tmp/evil",
    )
    result = lego.execute(spec)
    assert result.success is False
    assert "path traversal" in (result.error or "").lower()


def test_path_traversal_blocks_before_approval_gate():
    """path traversal check precede o approval gate."""
    lego = VideoProcessorLego()
    spec = VideoSpec(
        video_path="../../etc/shadow",
        goal="publicar no Instagram",  # teria disparado approval gate
        dry_run=False,
    )
    result = lego.execute(spec)
    # Deve falhar por traversal, não por approval
    assert result.error != "approval_required"
    assert "path traversal" in (result.error or "").lower()


def test_valid_paths_still_work_after_hardening():
    lego = VideoProcessorLego()
    spec = VideoSpec(video_path="sample.mp4", goal="transcrever", dry_run=True)
    result = lego.execute(spec)
    assert result.success is True


# ── P3: Whisper model pin ─────────────────────────────────────────────────────

def test_whisper_model_size_env_respected(monkeypatch):
    monkeypatch.setattr("src.legos.video_processor_lego._WHISPER_MODEL_SIZE", "base")
    from src.legos.video_processor_lego import _WHISPER_MODEL_SIZE
    assert _WHISPER_MODEL_SIZE == "base"


def test_whisper_cache_dir_env_respected(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "src.legos.video_processor_lego._WHISPER_CACHE_DIR", str(tmp_path)
    )
    from src.legos.video_processor_lego import _WHISPER_CACHE_DIR
    assert _WHISPER_CACHE_DIR == str(tmp_path)


def test_whisper_get_model_uses_cache_dir(monkeypatch):
    """_get_whisper_model passa download_root ao whisper.load_model."""
    calls = []

    class _FakeModel:
        pass

    def _fake_load(model_size, download_root=None):
        calls.append({"model_size": model_size, "download_root": download_root})
        return _FakeModel()

    import types
    fake_whisper = types.ModuleType("whisper")
    fake_whisper.load_model = _fake_load

    monkeypatch.setitem(__import__("sys").modules, "whisper", fake_whisper)
    # Reset cached model to force reload
    VideoProcessorLego._whisper_model = None
    try:
        VideoProcessorLego._get_whisper_model()
        assert len(calls) == 1
        assert calls[0]["download_root"] is not None
    finally:
        VideoProcessorLego._whisper_model = None


# ── Protocol compliance ───────────────────────────────────────────────────────

def test_lego_satisfies_video_processor_protocol():
    from src.interfaces.video_processor import VideoProcessor
    lego: VideoProcessor = VideoProcessorLego()
    assert hasattr(lego, "execute")
    assert hasattr(lego, "health_check")

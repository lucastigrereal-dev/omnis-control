"""Testes da AgenciaPipeline — Camada 1 (cortes inteligentes).

Todos os testes rodam em dry_run=True (sem Whisper real, sem FFmpeg real).
A injeção de MockTranscriptionAdapter garante transcrição determinística.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.agencia.pipeline import AgenciaPipeline, AgenciaResult, ClipResult
from src.video_studio.transcription import MockTranscriptionAdapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_adapter():
    return MockTranscriptionAdapter()


@pytest.fixture
def pipeline(mock_adapter):
    return AgenciaPipeline(dry_run=True, transcription_adapter=mock_adapter)


@pytest.fixture
def fake_video(tmp_path):
    """Cria um arquivo .mp4 fake (vazio) para satisfazer a checagem de existência."""
    p = tmp_path / "test_video.mp4"
    p.write_bytes(b"")
    return p


# ---------------------------------------------------------------------------
# Testes estruturais
# ---------------------------------------------------------------------------

class TestAgenciaPipelineSmoke:

    def test_pipeline_retorna_agencia_result(self, pipeline, fake_video):
        result = pipeline.run(fake_video, perfil="lucastigrereal", preset_name="reel")
        assert isinstance(result, AgenciaResult)

    def test_session_id_gerado(self, pipeline, fake_video):
        result = pipeline.run(fake_video)
        assert result.session_id != ""
        assert len(result.session_id) == 8

    def test_output_dir_criado(self, pipeline, fake_video):
        result = pipeline.run(fake_video, perfil="oinatalrn")
        assert result.output_dir.exists()

    def test_manifest_json_escrito(self, pipeline, fake_video):
        result = pipeline.run(fake_video)
        manifest_path = result.output_dir / "manifest.json"
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text())
        assert data["session_id"] == result.session_id
        assert data["dry_run"] is True

    def test_dry_run_flag_propagado(self, pipeline, fake_video):
        result = pipeline.run(fake_video)
        assert result.dry_run is True

    def test_video_name_correto(self, pipeline, fake_video):
        result = pipeline.run(fake_video)
        assert result.video_name == fake_video.name

    def test_perfil_correto(self, pipeline, fake_video):
        result = pipeline.run(fake_video, perfil="agenteviajabrasil")
        assert result.perfil == "agenteviajabrasil"

    def test_preset_correto(self, pipeline, fake_video):
        result = pipeline.run(fake_video, preset_name="reel")
        assert result.preset_name == "reel"


class TestAgenciaPipelineTranscricao:

    def test_segmentos_transcritos_maior_que_zero(self, pipeline, fake_video):
        result = pipeline.run(fake_video)
        assert result.transcript_segments > 0

    def test_hooks_detectados(self, pipeline, fake_video):
        result = pipeline.run(fake_video)
        # O mock de turismo tem "Voce ja imaginou" e "Natal" — pelo menos 1 hook
        assert result.hooks_found >= 1

    def test_tourism_transcript_detecta_hooks(self, mock_adapter):
        pipeline = AgenciaPipeline(dry_run=True, transcription_adapter=mock_adapter)
        transcript = mock_adapter.transcribe("turismo natal", duration_seconds=60.0)
        from src.video_studio.hooks import HookDetector
        hooks = HookDetector(max_hooks=10).detect(transcript.segments)
        assert len(hooks) > 0
        scores = [h.score for h in hooks]
        assert max(scores) > 0


class TestAgenciaPipelineClipes:

    def test_clipes_gerados_dry_run_manifest(self, pipeline, fake_video):
        result = pipeline.run(fake_video, max_clips=3)
        # dry_run → clipes geram .manifest.json, não .mp4
        for clip in result.clips:
            assert isinstance(clip, ClipResult)
            assert clip.dry_run is True

    def test_max_clips_respeitado(self, pipeline, fake_video):
        result = pipeline.run(fake_video, max_clips=2)
        assert len(result.clips) <= 2

    def test_max_clips_5_padrao(self, pipeline, fake_video):
        result = pipeline.run(fake_video)
        assert len(result.clips) <= 5

    def test_clip_tem_campos_obrigatorios(self, pipeline, fake_video):
        result = pipeline.run(fake_video)
        for clip in result.clips:
            assert clip.clip_id != ""
            assert clip.start_seconds >= 0
            assert clip.end_seconds > clip.start_seconds
            assert clip.duration > 0
            assert clip.hook != ""

    def test_output_dir_correto_por_perfil(self, pipeline, fake_video):
        result = pipeline.run(fake_video, perfil="oinatalrn")
        assert "oinatalrn" in str(result.output_dir)

    def test_to_dict_serializavel(self, pipeline, fake_video):
        result = pipeline.run(fake_video)
        d = result.to_dict()
        # Deve ser JSON-serializável sem erros
        serialized = json.dumps(d)
        assert result.session_id in serialized

    def test_summary_nao_vazio(self, pipeline, fake_video):
        result = pipeline.run(fake_video)
        summary = result.summary()
        assert len(summary) > 0
        assert result.session_id in summary


class TestAgenciaPipelinePresets:

    def test_preset_reel_9_16(self, pipeline, fake_video):
        result = pipeline.run(fake_video, preset_name="reel")
        assert result.preset_name == "reel"

    def test_preset_feed(self, pipeline, fake_video):
        result = pipeline.run(fake_video, preset_name="feed")
        assert result.preset_name == "feed"

    def test_preset_original_sem_filtro(self, pipeline, fake_video):
        result = pipeline.run(fake_video, preset_name="original")
        assert result.preset_name == "original"

    def test_preset_invalido_usa_reel(self, mock_adapter):
        pipeline = AgenciaPipeline(dry_run=True, transcription_adapter=mock_adapter)
        from src.agencia.pipeline import AgenciaPipeline as AP
        preset = AP._resolve_preset("invalido")
        from src.video_studio.render_presets import RenderPresets
        assert preset == RenderPresets.REEL


class TestRenderWithPreset:
    """Testa o novo método render_with_preset do FFmpegRenderer."""

    def test_dry_run_gera_manifest(self, tmp_path):
        from src.video_studio.render_ffmpeg import FFmpegRenderer
        from src.video_studio.render_presets import RenderPresets
        renderer = FFmpegRenderer()
        out = tmp_path / "clip_001_reel_1080x1920.mp4"
        result = renderer.render_with_preset(
            video_path=tmp_path / "fake.mp4",
            start=0.0,
            end=30.0,
            output_path=out,
            preset=RenderPresets.REEL,
            dry_run=True,
        )
        assert result.suffix == ".json"
        data = json.loads(result.read_text())
        assert data["dry_run"] is True
        assert data["preset_name"] == "Instagram Reel"
        assert data["duration"] == 30.0

    def test_dry_run_original_sem_preset(self, tmp_path):
        from src.video_studio.render_ffmpeg import FFmpegRenderer
        renderer = FFmpegRenderer()
        out = tmp_path / "clip_001.mp4"
        result = renderer.render_with_preset(
            video_path=tmp_path / "fake.mp4",
            start=5.0,
            end=35.0,
            output_path=out,
            preset=None,
            dry_run=True,
        )
        data = json.loads(result.read_text())
        assert data["preset_name"] is None

    def test_manifest_contem_campos_obrigatorios(self, tmp_path):
        from src.video_studio.render_ffmpeg import FFmpegRenderer
        from src.video_studio.render_presets import RenderPresets
        renderer = FFmpegRenderer()
        result = renderer.render_with_preset(
            video_path=tmp_path / "v.mp4",
            start=10.0,
            end=40.0,
            output_path=tmp_path / "out.mp4",
            preset=RenderPresets.FEED_SQUARE,
            dry_run=True,
        )
        data = json.loads(result.read_text())
        for key in ("dry_run", "video_path", "start", "end", "output_path", "duration", "preset_name"):
            assert key in data, f"campo ausente: {key}"


class TestWhisperToSegments:
    """Testa a conversão de dicts Whisper → TranscriptSegment."""

    def test_converte_segmento_valido(self):
        raw = [{"start": 0.0, "end": 5.0, "text": " Olá mundo ", "no_speech_prob": 0.1}]
        segs = AgenciaPipeline._whisper_to_segments(raw)
        assert len(segs) == 1
        assert segs[0].text == "Olá mundo"
        assert segs[0].start_seconds == 0.0
        assert segs[0].end_seconds == 5.0
        assert abs(segs[0].confidence - 0.9) < 0.001

    def test_ignora_segmento_sem_texto(self):
        raw = [{"start": 0.0, "end": 5.0, "text": "   ", "no_speech_prob": 0.0}]
        segs = AgenciaPipeline._whisper_to_segments(raw)
        assert len(segs) == 0

    def test_ignora_segmento_end_menor_start(self):
        raw = [{"start": 5.0, "end": 3.0, "text": "texto", "no_speech_prob": 0.0}]
        segs = AgenciaPipeline._whisper_to_segments(raw)
        assert len(segs) == 0

    def test_converte_multiplos_segmentos(self):
        raw = [
            {"start": 0.0, "end": 3.0, "text": "primeiro", "no_speech_prob": 0.0},
            {"start": 3.0, "end": 7.0, "text": "segundo", "no_speech_prob": 0.05},
            {"start": 7.0, "end": 12.0, "text": "terceiro", "no_speech_prob": 0.2},
        ]
        segs = AgenciaPipeline._whisper_to_segments(raw)
        assert len(segs) == 3
        assert segs[0].text == "primeiro"
        assert segs[2].end_seconds == 12.0

    def test_confidence_clampado_zero_um(self):
        raw = [{"start": 0.0, "end": 5.0, "text": "texto", "no_speech_prob": 1.5}]
        segs = AgenciaPipeline._whisper_to_segments(raw)
        assert len(segs) == 1
        assert segs[0].confidence == 0.0

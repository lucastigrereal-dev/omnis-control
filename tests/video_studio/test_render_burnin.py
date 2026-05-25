"""Testes do burn-in (Camada 2) — prova que o filtro subtitles= entra no comando ffmpeg.

Captura o cmd via monkeypatch (não precisa de ffmpeg/vídeo real) e valida a
construção. O teste real end-to-end com ffmpeg fica em test_render_burnin_real.
"""
from __future__ import annotations

import subprocess

import pytest

from src.video_studio.render_ffmpeg import FFmpegRenderer, _subtitles_filter
from src.video_studio.render_presets import RenderPresets


class _CmdCapture:
    """Captura o cmd passado ao subprocess.run e finge sucesso."""
    def __init__(self):
        self.cmd = None

    def __call__(self, cmd, *args, **kwargs):
        self.cmd = cmd
        class _R:
            returncode = 0
            stdout = b""
            stderr = b""
        return _R()


@pytest.fixture
def capture(monkeypatch):
    cap = _CmdCapture()
    monkeypatch.setattr(subprocess, "run", cap)
    # Finge que ffmpeg existe (não vamos chamar de verdade)
    monkeypatch.setattr(FFmpegRenderer, "is_ffmpeg_available", staticmethod(lambda: True))
    return cap


class TestSubtitlesFilter:
    def test_filtro_gera_prefixo_subtitles(self, tmp_path):
        srt = tmp_path / "c.srt"
        srt.write_text("1\n", encoding="utf-8")
        f = _subtitles_filter(srt)
        assert f.startswith("subtitles=")

    def test_colon_tem_duplo_backslash(self, tmp_path):
        """Regressão: o colon do filtergraph precisa de DUPLO backslash (\\\\:).

        Um único \\: é consumido no 2º nível de escaping do ffmpeg, deixando ':'
        cru que o 1º nível trata como separador de opção (erro 'original_size').
        Bug provado com ffmpeg real: single -> EINVAL, double -> EXIT 0.
        """
        srt = tmp_path / "c.srt"
        srt.write_text("1\n", encoding="utf-8")
        f = _subtitles_filter(srt)
        body = f[len("subtitles="):]
        # Todo ':' no corpo deve estar precedido por '\\\\' (dois backslashes)
        idx = body.find(":")
        if idx != -1:  # em paths Windows há o colon do drive
            assert body[idx - 2:idx] == "\\\\", f"colon sem duplo backslash em {body!r}"


class TestBurnInCommand:
    def test_burn_adiciona_subtitles_no_vf(self, capture, tmp_path):
        srt = tmp_path / "clip.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:01,000\noi\n", encoding="utf-8")
        out = tmp_path / "out.mp4"

        FFmpegRenderer().render_with_preset(
            tmp_path / "in.mp4", 0.0, 3.0, out,
            preset=RenderPresets.REEL, dry_run=False,
            srt_path=srt, remove_silence=False,
        )

        cmd = capture.cmd
        assert cmd is not None
        # Deve haver -vf com subtitles=
        vf_idx = cmd.index("-vf")
        vf_value = cmd[vf_idx + 1]
        assert "subtitles=" in vf_value

    def test_sem_srt_nao_queima(self, capture, tmp_path):
        out = tmp_path / "out.mp4"
        FFmpegRenderer().render_with_preset(
            tmp_path / "in.mp4", 0.0, 3.0, out,
            preset=RenderPresets.REEL, dry_run=False,
            srt_path=None, remove_silence=False,
        )
        cmd = capture.cmd
        vf_idx = cmd.index("-vf")
        assert "subtitles=" not in cmd[vf_idx + 1]

    def test_preset_burn_false_nao_queima(self, capture, tmp_path):
        # THUMBNAIL tem burn_captions=False
        srt = tmp_path / "clip.srt"
        srt.write_text("1\n", encoding="utf-8")
        out = tmp_path / "out.mp4"
        FFmpegRenderer().render_with_preset(
            tmp_path / "in.mp4", 0.0, 3.0, out,
            preset=RenderPresets.THUMBNAIL, dry_run=False,
            srt_path=srt, remove_silence=False,
        )
        cmd = capture.cmd
        full = " ".join(cmd)
        assert "subtitles=" not in full

    def test_remove_silence_adiciona_filtro_audio(self, capture, tmp_path):
        out = tmp_path / "out.mp4"
        FFmpegRenderer().render_with_preset(
            tmp_path / "in.mp4", 0.0, 3.0, out,
            preset=RenderPresets.REEL, dry_run=False,
            srt_path=None, remove_silence=True,
        )
        cmd = capture.cmd
        af_idx = cmd.index("-af")
        assert "silenceremove" in cmd[af_idx + 1]

    def test_burn_e_silence_juntos(self, capture, tmp_path):
        srt = tmp_path / "clip.srt"
        srt.write_text("1\n", encoding="utf-8")
        out = tmp_path / "out.mp4"
        FFmpegRenderer().render_with_preset(
            tmp_path / "in.mp4", 0.0, 3.0, out,
            preset=RenderPresets.REEL, dry_run=False,
            srt_path=srt, remove_silence=True,
        )
        cmd = capture.cmd
        full = " ".join(cmd)
        assert "subtitles=" in full
        assert "silenceremove" in full


@pytest.mark.skipif(
    not FFmpegRenderer.is_ffmpeg_available(),
    reason="ffmpeg não instalado — teste real de burn-in pulado",
)
class TestBurnInRealFFmpeg:
    """End-to-end com ffmpeg REAL: gera vídeo, queima legenda, valida pixels."""

    def _make_video(self, path) -> None:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi",
             "-i", "testsrc=size=640x360:rate=30:duration=4",
             "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
             "-shortest", str(path)],
            check=True, capture_output=True,
        )

    def test_burn_in_real_produz_video(self, tmp_path):
        src = tmp_path / "src.mp4"
        srt = tmp_path / "cap.srt"
        out = tmp_path / "burned.mp4"
        self._make_video(src)
        srt.write_text(
            "1\n00:00:00,500 --> 00:00:03,500\nLEGENDA QUEIMADA OMNIS\n",
            encoding="utf-8",
        )

        result = FFmpegRenderer().render_with_preset(
            src, 0.0, 4.0, out, preset=RenderPresets.REEL,
            dry_run=False, srt_path=srt, remove_silence=False,
        )
        assert result.exists()
        assert result.stat().st_size > 10_000  # vídeo real, não vazio

    def test_burn_in_muda_pixels(self, tmp_path):
        """Anti-teatro: frame com legenda difere do frame sem legenda."""
        src = tmp_path / "src.mp4"
        srt = tmp_path / "cap.srt"
        self._make_video(src)
        srt.write_text(
            "1\n00:00:00,500 --> 00:00:03,500\nLEGENDA QUEIMADA OMNIS\n",
            encoding="utf-8",
        )

        with_cap = tmp_path / "with.mp4"
        no_cap = tmp_path / "no.mp4"
        renderer = FFmpegRenderer()
        renderer.render_with_preset(src, 0.0, 4.0, with_cap,
                                    preset=RenderPresets.REEL, dry_run=False, srt_path=srt)
        renderer.render_with_preset(src, 0.0, 4.0, no_cap,
                                    preset=RenderPresets.REEL, dry_run=False, srt_path=None)

        def frame_at_2s(video, dest):
            subprocess.run(["ffmpeg", "-y", "-ss", "2", "-i", str(video),
                            "-frames:v", "1", str(dest)], check=True, capture_output=True)
            return dest.read_bytes()

        fc = frame_at_2s(with_cap, tmp_path / "fc.png")
        fs = frame_at_2s(no_cap, tmp_path / "fs.png")
        assert fc != fs, "frame com legenda deveria diferir do sem legenda"

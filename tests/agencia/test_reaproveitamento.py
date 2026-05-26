"""Testes — ReaproveitadorDeVideo (Agência B1).

Cobre: dry_run, formatos/resoluções, FFmpeg ausente (skip),
       manifesto JSON, to_dict round-trip, anti-teatro.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.agencia.reaproveitamento import (
    ReaproveitadorDeVideo,
    ReaproveitamentoResult,
    FormatoResult,
    _FORMATO_CONFIG,
    _ALL_FORMATOS,
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

FAKE_VIDEO = Path("video_fonte.mp4")

RESOLUCOES_ESPERADAS = {
    "reel": "1080x1920",
    "feed": "1080x1080",
    "story": "1080x1920",
    "horizontal": "1920x1080",
}


@pytest.fixture
def reap_dry():
    return ReaproveitadorDeVideo(dry_run=True)


@pytest.fixture
def reap_real():
    return ReaproveitadorDeVideo(dry_run=False)


# ------------------------------------------------------------------
# TestDryRun
# ------------------------------------------------------------------

class TestDryRun:
    def test_retorna_reaproveitamento_result(self, reap_dry, tmp_path):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, output_dir=tmp_path)
        assert isinstance(result, ReaproveitamentoResult)

    def test_nao_chama_ffmpeg(self, reap_dry, tmp_path):
        """dry_run não deve invocar FFmpeg."""
        with patch("subprocess.run") as mock_run:
            reap_dry.reaproveitamento(FAKE_VIDEO, output_dir=tmp_path)
            mock_run.assert_not_called()

    def test_manifest_criado(self, reap_dry, tmp_path):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, output_dir=tmp_path)
        assert Path(result.manifest_path).exists()

    def test_manifest_contem_source_video(self, reap_dry, tmp_path):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, output_dir=tmp_path)
        data = json.loads(Path(result.manifest_path).read_text())
        assert str(FAKE_VIDEO) in data["source_video"]

    def test_to_dict_round_trip(self, reap_dry, tmp_path):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, output_dir=tmp_path)
        d = result.to_dict()
        assert d["dry_run"] is True
        assert isinstance(d["formatos"], list)
        assert d["source_video"] == str(FAKE_VIDEO)
        assert d["formatos_count"] == len(_ALL_FORMATOS)

    def test_dry_run_status_ok(self, reap_dry, tmp_path):
        """dry_run retorna todos os formatos com status 'ok'."""
        result = reap_dry.reaproveitamento(FAKE_VIDEO, output_dir=tmp_path)
        for fr in result.formatos:
            assert fr.status == "ok", f"formato={fr.formato} teve status={fr.status}"

    def test_dry_run_gera_todos_formatos_default(self, reap_dry, tmp_path):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, output_dir=tmp_path)
        nomes = {fr.formato for fr in result.formatos}
        assert nomes == set(_ALL_FORMATOS)

    def test_summary_contem_source(self, reap_dry, tmp_path):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, output_dir=tmp_path)
        s = result.summary()
        assert "video_fonte.mp4" in s

    def test_manifest_dry_run_flag_true(self, reap_dry, tmp_path):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, output_dir=tmp_path)
        data = json.loads(Path(result.manifest_path).read_text())
        assert data["dry_run"] is True

    def test_output_dir_criado(self, reap_dry, tmp_path):
        nested = tmp_path / "deep" / "output"
        result = reap_dry.reaproveitamento(FAKE_VIDEO, output_dir=nested)
        assert nested.exists()


# ------------------------------------------------------------------
# TestFormatos
# ------------------------------------------------------------------

class TestFormatos:
    @pytest.mark.parametrize("fmt,res", RESOLUCOES_ESPERADAS.items())
    def test_resolucao_correta_por_formato(self, reap_dry, tmp_path, fmt, res):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, formatos=[fmt], output_dir=tmp_path / fmt)
        assert len(result.formatos) == 1
        fr = result.formatos[0]
        assert fr.resolucao_ok(res), f"formato={fmt}: esperado {res}, obtido {fr.resolution}"

    def test_reel_resolucao(self, reap_dry, tmp_path):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, formatos=["reel"], output_dir=tmp_path)
        assert result.formatos[0].resolution == "1080x1920"

    def test_feed_resolucao(self, reap_dry, tmp_path):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, formatos=["feed"], output_dir=tmp_path)
        assert result.formatos[0].resolution == "1080x1080"

    def test_story_resolucao(self, reap_dry, tmp_path):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, formatos=["story"], output_dir=tmp_path)
        assert result.formatos[0].resolution == "1080x1920"

    def test_horizontal_resolucao(self, reap_dry, tmp_path):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, formatos=["horizontal"], output_dir=tmp_path)
        assert result.formatos[0].resolution == "1920x1080"

    def test_story_duracao_15s(self, reap_dry, tmp_path):
        """story deve ter duração de 15s (corte do início)."""
        result = reap_dry.reaproveitamento(FAKE_VIDEO, formatos=["story"], output_dir=tmp_path)
        assert result.formatos[0].duration_s == 15.0

    def test_subset_formatos(self, reap_dry, tmp_path):
        """Pode pedir apenas 2 formatos."""
        result = reap_dry.reaproveitamento(
            FAKE_VIDEO, formatos=["reel", "feed"], output_dir=tmp_path
        )
        assert len(result.formatos) == 2
        nomes = {fr.formato for fr in result.formatos}
        assert nomes == {"reel", "feed"}

    def test_output_path_contem_formato(self, reap_dry, tmp_path):
        """Path gerado deve conter o nome do formato."""
        result = reap_dry.reaproveitamento(FAKE_VIDEO, formatos=["reel"], output_dir=tmp_path)
        assert "reel" in result.formatos[0].output_path

    def test_formato_tem_mp4_extensao(self, reap_dry, tmp_path):
        result = reap_dry.reaproveitamento(FAKE_VIDEO, formatos=["feed"], output_dir=tmp_path)
        assert result.formatos[0].output_path.endswith(".mp4")


# ------------------------------------------------------------------
# TestFFmpegAusente
# ------------------------------------------------------------------

class TestFFmpegAusente:
    def test_ffmpeg_ausente_nao_crasha(self, tmp_path):
        """FileNotFoundError ao chamar ffmpeg → status skip, sem raise."""
        reap = ReaproveitadorDeVideo(dry_run=False)
        with patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg not found")):
            result = reap.reaproveitamento(FAKE_VIDEO, formatos=["reel"], output_dir=tmp_path)
        assert len(result.formatos) == 1
        assert result.formatos[0].status == "skip"

    def test_ffmpeg_ausente_todos_formatos_skip(self, tmp_path):
        """FFmpeg ausente → todos os formatos ficam skip."""
        reap = ReaproveitadorDeVideo(dry_run=False)
        with patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg not found")):
            result = reap.reaproveitamento(FAKE_VIDEO, output_dir=tmp_path)
        for fr in result.formatos:
            assert fr.status == "skip", f"formato={fr.formato} deveria ser skip"

    def test_ffmpeg_ausente_manifest_ainda_salvo(self, tmp_path):
        """Mesmo com FFmpeg ausente, manifest.json deve ser criado."""
        reap = ReaproveitadorDeVideo(dry_run=False)
        with patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg not found")):
            result = reap.reaproveitamento(FAKE_VIDEO, output_dir=tmp_path)
        assert Path(result.manifest_path).exists()

    def test_ffmpeg_ausente_error_descricao(self, tmp_path):
        """FormatoResult.error deve conter a mensagem de erro."""
        reap = ReaproveitadorDeVideo(dry_run=False)
        with patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg not found")):
            result = reap.reaproveitamento(FAKE_VIDEO, formatos=["feed"], output_dir=tmp_path)
        assert result.formatos[0].error is not None
        assert "ffmpeg" in result.formatos[0].error.lower()

    def test_ffmpeg_calledprocess_error_status_fail(self, tmp_path):
        """CalledProcessError → status fail (ffmpeg presente mas retornou erro)."""
        reap = ReaproveitadorDeVideo(dry_run=False)
        err = subprocess.CalledProcessError(1, "ffmpeg", stderr=b"codec error")
        with patch("subprocess.run", side_effect=err):
            result = reap.reaproveitamento(FAKE_VIDEO, formatos=["reel"], output_dir=tmp_path)
        assert result.formatos[0].status == "fail"


# ------------------------------------------------------------------
# TestAntiTeatro
# ------------------------------------------------------------------

class TestAntiTeatro:
    def test_source_video_no_manifest_reflete_path_real(self, reap_dry, tmp_path):
        """Anti-teatro: source_video no manifest deve ser o path passado, não um hardcode."""
        video = Path("meu_video_especifico.mp4")
        result = reap_dry.reaproveitamento(video, output_dir=tmp_path)
        data = json.loads(Path(result.manifest_path).read_text())
        assert "meu_video_especifico" in data["source_video"]

    def test_mudanca_formato_reflete_na_resolucao(self, reap_dry, tmp_path):
        """Anti-teatro: trocar formato de 'reel' para 'feed' muda a resolução."""
        r_reel = reap_dry.reaproveitamento(FAKE_VIDEO, formatos=["reel"], output_dir=tmp_path / "r")
        r_feed = reap_dry.reaproveitamento(FAKE_VIDEO, formatos=["feed"], output_dir=tmp_path / "f")
        assert r_reel.formatos[0].resolution != r_feed.formatos[0].resolution

    def test_output_dir_reflete_no_resultado(self, reap_dry, tmp_path):
        """Anti-teatro: output_dir no resultado deve bater com o dir passado."""
        custom_dir = tmp_path / "custom_output"
        result = reap_dry.reaproveitamento(FAKE_VIDEO, output_dir=custom_dir)
        assert "custom_output" in result.output_dir

    def test_to_dict_formatos_ok_contagem_correta(self, reap_dry, tmp_path):
        """formatos_ok deve contar exatamente os formatos com status 'ok'."""
        result = reap_dry.reaproveitamento(FAKE_VIDEO, formatos=["reel", "feed"], output_dir=tmp_path)
        d = result.to_dict()
        assert d["formatos_ok"] == 2

    def test_formato_resultado_nome_bate(self, reap_dry, tmp_path):
        """FormatoResult.formato deve ser o nome exato do formato solicitado."""
        result = reap_dry.reaproveitamento(FAKE_VIDEO, formatos=["horizontal"], output_dir=tmp_path)
        assert result.formatos[0].formato == "horizontal"


# ------------------------------------------------------------------
# Monkey-patch helper p/ parametrize de resolução
# ------------------------------------------------------------------

def _patch_formato_result():
    """Adiciona método helper resolucao_ok para uso em testes parametrizados."""
    def resolucao_ok(self, expected: str) -> bool:
        return self.resolution == expected
    FormatoResult.resolucao_ok = resolucao_ok


_patch_formato_result()

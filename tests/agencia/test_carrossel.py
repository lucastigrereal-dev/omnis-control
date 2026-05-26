"""Testes — CarrosselGenerator (Agência Camada 3).

Cobre: dry_run, geração real de PNG, manifesto JSON,
       paleta de cores, anti-teatro (slide texts refletem no output),
       thumbnail, resultado to_dict/summary.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.agencia.carrossel import CarrosselGenerator, CarrosselResult, _PERFIL_PALETTE


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

SLIDES_SAMPLE = ["Piscina privativa", "Café da manhã gourmet", "Vista pro mar"]
TITLE_SAMPLE  = "Hotel Vista Mar"
PERFIL        = "oinatalrn"


@pytest.fixture
def gen_dry():
    return CarrosselGenerator(dry_run=True)


@pytest.fixture
def gen_real():
    return CarrosselGenerator(dry_run=False)


# ------------------------------------------------------------------
# Testes dry_run
# ------------------------------------------------------------------

class TestDryRun:
    def test_retorna_carrossel_result(self, gen_dry, tmp_path):
        result = gen_dry.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        assert isinstance(result, CarrosselResult)

    def test_slides_count_correto(self, gen_dry, tmp_path):
        """Capa + 3 conteúdo + CTA = 5 slides."""
        result = gen_dry.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        assert result.slides_count == len(SLIDES_SAMPLE) + 2  # capa + CTA

    def test_thumbnail_path_presente(self, gen_dry, tmp_path):
        result = gen_dry.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        assert result.thumbnail is not None

    def test_manifesto_json_gerado(self, gen_dry, tmp_path):
        result = gen_dry.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        manifests = list(tmp_path.glob("*.manifest.json"))
        assert len(manifests) == 1
        data = json.loads(manifests[0].read_text())
        assert data["perfil"] == PERFIL
        assert data["dry_run"] is True

    def test_dry_run_nao_cria_png(self, gen_dry, tmp_path):
        gen_dry.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        pngs = list(tmp_path.glob("*.png"))
        assert pngs == []  # sem PNG em dry_run

    def test_to_dict_round_trip(self, gen_dry, tmp_path):
        result = gen_dry.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        d = result.to_dict()
        assert d["perfil"] == PERFIL
        assert d["slides_count"] == result.slides_count
        assert isinstance(d["slides"], list)

    def test_summary_contem_perfil(self, gen_dry, tmp_path):
        result = gen_dry.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        s = result.summary()
        assert PERFIL in s

    def test_session_id_customizavel(self, gen_dry, tmp_path):
        result = gen_dry.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
            session_id="abc123",
        )
        assert result.session_id == "abc123"

    def test_cta_customizavel(self, gen_dry, tmp_path):
        result = gen_dry.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
            cta="Reserva agora!",
        )
        assert result.metadata["cta"] == "Reserva agora!"

    def test_sem_slides_gera_capa_mais_cta(self, gen_dry, tmp_path):
        """Lista vazia → só capa + CTA = 2 slides."""
        result = gen_dry.generate(
            title="Só título",
            slides=[],
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        assert result.slides_count == 2


# ------------------------------------------------------------------
# Testes paleta
# ------------------------------------------------------------------

class TestPaleta:
    def test_perfil_oinatalrn_usa_azul(self, gen_dry, tmp_path):
        result = gen_dry.generate(
            title="T", slides=[], perfil="oinatalrn", output_dir=tmp_path
        )
        assert result.metadata["bg_color"] == "#0d3b66"

    def test_perfil_desconhecido_usa_default(self, gen_dry, tmp_path):
        result = gen_dry.generate(
            title="T", slides=[], perfil="perfil_inexistente", output_dir=tmp_path
        )
        bg = _PERFIL_PALETTE["default"][0]
        assert result.metadata["bg_color"] == bg

    @pytest.mark.parametrize("perfil", list(_PERFIL_PALETTE.keys()))
    def test_todos_perfis_tem_paleta(self, gen_dry, tmp_path, perfil):
        result = gen_dry.generate(
            title="T", slides=["item"], perfil=perfil, output_dir=tmp_path
        )
        assert result.metadata["bg_color"] is not None


# ------------------------------------------------------------------
# Testes com geração REAL de PNG
# ------------------------------------------------------------------

class TestGeracaoReal:
    def test_cria_pngs_reais(self, gen_real, tmp_path):
        result = gen_real.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        for slide_path in result.slides:
            assert Path(slide_path).exists(), f"PNG não criado: {slide_path}"

    def test_thumbnail_criado(self, gen_real, tmp_path):
        result = gen_real.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        assert result.thumbnail is not None
        assert Path(result.thumbnail).exists()

    def test_png_e_valido_via_pillow(self, gen_real, tmp_path):
        from PIL import Image
        result = gen_real.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        img = Image.open(str(result.slides[0]))
        assert img.size == (1080, 1080)
        assert img.mode == "RGB"

    def test_thumbnail_dimensoes(self, gen_real, tmp_path):
        from PIL import Image
        result = gen_real.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        img = Image.open(str(result.thumbnail))
        assert img.size == (1280, 720)

    def test_manifesto_json_gerado_real(self, gen_real, tmp_path):
        gen_real.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        manifests = list(tmp_path.glob("*.manifest.json"))
        assert len(manifests) == 1

    def test_anti_teatro_titulo_diferente_gera_sessao_diferente(self, gen_real, tmp_path):
        """Anti-teatro: título diferente → session_id diferente (UUID gerado) → nomes únicos."""
        r1 = gen_real.generate(title="Hotel A", slides=["s1"], perfil=PERFIL, output_dir=tmp_path / "r1")
        r2 = gen_real.generate(title="Hotel B", slides=["s2"], perfil=PERFIL, output_dir=tmp_path / "r2")
        assert r1.session_id != r2.session_id

    def test_anti_teatro_metadata_reflete_titulo(self, gen_real, tmp_path):
        """Anti-teatro: manifesto contém o título exato passado."""
        titulo = "HOTEL_ANTI_TEATRO_123"
        result = gen_real.generate(
            title=titulo,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=tmp_path,
        )
        manifests = list(tmp_path.glob("*.manifest.json"))
        data = json.loads(manifests[0].read_text())
        assert data["metadata"]["title"] == titulo

    def test_output_dir_criado_automaticamente(self, gen_real, tmp_path):
        nested = tmp_path / "deep" / "nested" / "dir"
        gen_real.generate(
            title=TITLE_SAMPLE,
            slides=SLIDES_SAMPLE,
            perfil=PERFIL,
            output_dir=nested,
        )
        assert nested.exists()

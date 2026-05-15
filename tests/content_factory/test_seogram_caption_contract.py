"""Tests for W092 — SEOgram Caption Generator contract."""
from __future__ import annotations

import pytest

from src.content_factory.brief import ContentBrief
from src.content_factory.seogram import SEOgramCaption, SEOgramGenerator


class TestSEOgramCaption:
    def test_create_minimal_caption(self):
        cap = SEOgramCaption(caption_id="c1", brief_id="b1")
        assert cap.caption_id == "c1"
        assert cap.brief_id == "b1"
        assert cap.hook == ""
        assert cap.approval_status == "draft"

    def test_full_caption_formatting(self):
        cap = SEOgramCaption(
            caption_id="c2",
            brief_id="b2",
            hook="Descubra o paraiso!",
            paragraph_1="Primeiro paragrafo com info.",
            paragraph_2="Segundo paragrafo com detalhes.",
            paragraph_3="Terceiro paragrafo extra.",
            cta="Salve esse post!",
            hashtags=["#turismo", "#viagem", "#brasil"],
        )
        fc = cap.full_caption
        assert "Descubra o paraiso!" in fc
        assert "Primeiro paragrafo com info." in fc
        assert "Segundo paragrafo com detalhes." in fc
        assert "Terceiro paragrafo extra." in fc
        assert "Salve esse post!" in fc
        assert "#turismo #viagem #brasil" in fc

    def test_full_caption_without_paragraph_3(self):
        cap = SEOgramCaption(
            caption_id="c3",
            brief_id="b3",
            hook="Hook!",
            paragraph_1="P1",
            paragraph_2="P2",
            cta="CTA!",
            hashtags=["#tag"],
        )
        fc = cap.full_caption
        assert cap.paragraph_3 == ""
        assert "P2" in fc
        assert "CTA!" in fc

    def test_to_dict_roundtrip(self):
        cap = SEOgramCaption(
            caption_id="c4",
            brief_id="b4",
            hook="Hook test",
            paragraph_1="P1 test",
            paragraph_2="P2 test",
            cta="CTA test",
            hashtags=["#h1", "#h2"],
            keywords_used=["kw1", "kw2"],
            approval_status="approved",
        )
        d = cap.to_dict()
        restored = SEOgramCaption.from_dict(d)
        assert restored.caption_id == cap.caption_id
        assert restored.hook == cap.hook
        assert restored.hashtags == cap.hashtags
        assert restored.keywords_used == cap.keywords_used

    def test_to_markdown(self):
        cap = SEOgramCaption(
            caption_id="c5",
            brief_id="b5",
            hook="Hook MD",
            paragraph_1="P1 MD",
            paragraph_2="P2 MD",
            cta="CTA MD",
            hashtags=["#md"],
        )
        md = cap.to_markdown()
        assert "Hook MD" in md
        assert "P1 MD" in md
        assert "CTA MD" in md

    def test_approval_status_defaults_to_draft(self):
        cap = SEOgramCaption(caption_id="c6", brief_id="b6")
        assert cap.approval_status == "draft"


class TestSEOgramGenerator:
    def setup_method(self):
        self.generator = SEOgramGenerator()

    def _make_brief(self, **kwargs) -> ContentBrief:
        defaults = {
            "brief_id": "b_test",
            "title": "Resort em Natal",
            "brand": "Tigre Real",
            "keywords": ["turismo", "praia", "natal"],
            "cta": "Reserve agora!",
        }
        defaults.update(kwargs)
        return ContentBrief(**defaults)

    def test_generate_returns_caption(self):
        brief = self._make_brief()
        cap = self.generator.generate(brief)
        assert isinstance(cap, SEOgramCaption)
        assert cap.caption_id != ""
        assert cap.brief_id == brief.brief_id

    def test_generate_uses_alcance_objective(self):
        brief = self._make_brief(objective="alcance")
        cap = self.generator.generate(brief)
        assert "Descubra" in cap.hook

    def test_generate_uses_autoridade_objective(self):
        brief = self._make_brief(objective="autoridade")
        cap = self.generator.generate(brief)
        assert "guia definitivo" in cap.hook or "guia definitivo" in cap.hook

    def test_generate_uses_conversao_objective(self):
        brief = self._make_brief(objective="conversao")
        cap = self.generator.generate(brief)
        assert "Economize" in cap.hook or "Oportunidade" in cap.paragraph_1

    def test_generate_falls_back_to_alcance_for_unknown_objective(self):
        brief = self._make_brief(objective="invalido")
        cap = self.generator.generate(brief)
        assert cap.hook != ""

    def test_generate_includes_hashtags(self):
        brief = self._make_brief(keywords=["turismo", "praia", "destino"])
        cap = self.generator.generate(brief)
        assert len(cap.hashtags) > 0
        assert any("turismo" in h for h in cap.hashtags)

    def test_generate_default_cta_when_none(self):
        brief = self._make_brief(cta="")
        cap = self.generator.generate(brief)
        assert cap.cta != ""

    def test_generate_uses_brief_cta(self):
        brief = self._make_brief(cta="Meu CTA customizado!")
        cap = self.generator.generate(brief)
        assert cap.cta == "Meu CTA customizado!"

    def test_detect_niche_turismo(self):
        niche = self.generator._detect_niche(["turismo", "praia"])
        assert niche == "turismo"

    def test_detect_niche_hotel(self):
        niche = self.generator._detect_niche(["hotel", "resort"])
        assert niche == "hotel"

    def test_detect_niche_gastronomia(self):
        niche = self.generator._detect_niche(["restaurante", "comida"])
        assert niche == "gastronomia"

    def test_detect_niche_familia(self):
        niche = self.generator._detect_niche(["familia", "crianca"])
        assert niche == "familia"

    def test_detect_niche_default(self):
        niche = self.generator._detect_niche(["tecnologia"])
        assert niche == "default"

    def test_detect_niche_case_insensitive(self):
        niche = self.generator._detect_niche(["TURISMO", "Praia"])
        assert niche == "turismo"

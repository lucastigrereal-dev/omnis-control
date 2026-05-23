"""Tests for W091 — ContentBrief model."""
from __future__ import annotations

import pytest

from src.content_factory.brief import ContentBrief


class TestContentBrief:
    def test_create_minimal_brief(self):
        brief = ContentBrief(brief_id="b1", title="Viagem em Familia")
        assert brief.brief_id == "b1"
        assert brief.title == "Viagem em Familia"
        assert brief.brand == ""
        assert brief.objective == "alcance"
        assert brief.dry_run is True

    def test_create_full_brief(self):
        brief = ContentBrief(
            brief_id="b2",
            title="Resort All-Inclusive",
            brand="Tigre Real",
            audience="Familias com filhos",
            objective="conversao",
            platform="instagram",
            format="carousel",
            pillar="vendas",
            tone="inspirational",
            keywords=["resort", "familia", "all-inclusive"],
            cta="Reserve ja com desconto!",
            constraints="Max 6 slides",
        )
        assert brief.brand == "Tigre Real"
        assert brief.audience == "Familias com filhos"
        assert brief.objective == "conversao"
        assert brief.format == "carousel"
        assert brief.pillar == "vendas"
        assert brief.tone == "inspirational"
        assert len(brief.keywords) == 3
        assert brief.cta == "Reserve ja com desconto!"
        assert brief.constraints == "Max 6 slides"

    def test_default_values(self):
        brief = ContentBrief(brief_id="b3", title="Test")
        assert brief.brand == ""
        assert brief.audience == ""
        assert brief.objective == "alcance"
        assert brief.platform == "instagram"
        assert brief.format == "feed"
        assert brief.pillar == ""
        assert brief.tone == "conversational"
        assert brief.keywords == []
        assert brief.cta == ""
        assert brief.constraints == ""
        assert brief.dry_run is True
        assert brief.notes == ""

    def test_to_dict_roundtrip(self):
        brief = ContentBrief(
            brief_id="b4",
            title="Hotel Fazenda",
            brand="Familia Tigre",
            keywords=["hotel", "fazenda"],
            cta="Agende sua visita",
        )
        d = brief.to_dict()
        restored = ContentBrief.from_dict(d)
        assert restored.brief_id == brief.brief_id
        assert restored.title == brief.title
        assert restored.brand == brief.brand
        assert restored.keywords == brief.keywords
        assert restored.cta == brief.cta

    def test_to_dict_minimal_brief(self):
        brief = ContentBrief(brief_id="b5", title="Minimal")
        d = brief.to_dict()
        assert d["brief_id"] == "b5"
        assert d["title"] == "Minimal"
        assert d["brand"] == ""
        assert d["keywords"] == []

    def test_to_markdown(self):
        brief = ContentBrief(
            brief_id="b6",
            title="Praia Natal",
            brand="Natal Aí Vou Eu",
            keywords=["praia", "natal"],
            cta="Salve esse post!",
        )
        md = brief.to_markdown()
        assert "# Content Brief: Praia Natal" in md
        assert "**ID:** b6" in md
        assert "**Brand:** Natal Aí Vou Eu" in md
        assert "**Keywords:** praia, natal" in md
        assert "**CTA:** Salve esse post!" in md

    def test_created_at_is_set(self):
        brief = ContentBrief(brief_id="b7", title="Timestamp")
        assert brief.created_at != ""

    def test_brief_with_notes(self):
        brief = ContentBrief(brief_id="b8", title="With Notes", notes="Extra info")
        assert brief.notes == "Extra info"
        md = brief.to_markdown()
        assert "Extra info" in md

    def test_dry_run_default_true(self):
        brief = ContentBrief(brief_id="b9", title="Dry Run Check")
        assert brief.dry_run is True

    def test_dry_run_explicit_false(self):
        brief = ContentBrief(brief_id="b10", title="Not Dry", dry_run=False)
        assert brief.dry_run is False

    def test_keywords_empty_list(self):
        brief = ContentBrief(brief_id="b11", title="No Keywords")
        md = brief.to_markdown()
        assert "**Keywords:** none" in md

    def test_from_dict_missing_optional_fields(self):
        d = {"brief_id": "b12"}
        brief = ContentBrief.from_dict(d)
        assert brief.brief_id == "b12"
        assert brief.title == ""
        assert brief.dry_run is True

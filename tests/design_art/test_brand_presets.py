"""Tests for brand presets."""

from src.design_art.brand_presets import BrandPresets


class TestBrandPresets:
    def test_all_six_profiles(self):
        assert len(BrandPresets.ALL) == 6

    def test_each_profile_has_required_fields(self):
        for p in BrandPresets.ALL:
            assert p.name
            assert p.brand_id
            assert p.primary_color.startswith("#")
            assert p.secondary_color.startswith("#")
            assert p.accent_color.startswith("#")
            assert p.visual_archetype

    def test_get_by_brand_id(self):
        p = BrandPresets.get("lucastigrereal")
        assert p is not None
        assert p.name == "Lucas Tigre Real"

    def test_get_missing(self):
        assert BrandPresets.get("nonexistent") is None

    def test_all_dicts(self):
        dicts = BrandPresets.all_dicts()
        assert len(dicts) == 6
        assert all(isinstance(d, dict) for d in dicts)
        assert dicts[0]["brand_id"] == "lucastigrereal"

    def test_lucas_profile_archetype(self):
        p = BrandPresets.LUCAS_TIGRE_REAL
        assert p.visual_archetype == "bold"

    def test_familia_profile_mood(self):
        p = BrandPresets.A_FAMILIA_TIGRE_REAL
        assert "familia" in p.mood_keywords

    def test_gastronomia_profile_colors(self):
        p = BrandPresets.O_QUE_COMER_NATAL_RN
        assert p.primary_color == "#8B0000"

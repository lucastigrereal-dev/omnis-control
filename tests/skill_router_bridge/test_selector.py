from src.skill_router_bridge.catalog import SkillCatalog
from src.skill_router_bridge.selector import SkillSelector, FALLBACK_SKILL_ID
from src.skill_router_bridge.models import SkillDefinition


def make_catalog(skills: list[dict]) -> SkillCatalog:
    catalog = SkillCatalog()
    for s in skills:
        catalog.add_skill(SkillDefinition.from_dict(s))
    return catalog


class TestSkillSelector:
    def test_select_by_id_exact_match(self):
        catalog = make_catalog([
            {"skill_id": "seogram", "name": "SEOgram"},
            {"skill_id": "brainstorm", "name": "Brainstorm"},
        ])
        selector = SkillSelector(catalog)
        result = selector.select_by_id("seogram")
        assert result.selected_skill_id == "seogram"
        assert result.confidence == 1.0
        assert result.fallback is False

    def test_select_by_id_by_name_case_insensitive(self):
        catalog = make_catalog([
            {"skill_id": "id_x", "name": "Seogram"},
        ])
        selector = SkillSelector(catalog)
        result = selector.select_by_id("seogram")
        assert result.selected_skill_id == "id_x"
        assert result.confidence == 0.9

    def test_select_by_id_not_found_fallback(self):
        catalog = make_catalog([{"skill_id": "s1", "name": "S1"}])
        selector = SkillSelector(catalog)
        result = selector.select_by_id("missing")
        assert result.selected_skill_id == FALLBACK_SKILL_ID
        assert result.fallback is True
        assert result.confidence == 0.0

    def test_select_by_intent_direct_match(self):
        catalog = make_catalog([
            {"skill_id": "seogram", "name": "SEOgram",
             "description": "Generate SEO-optimized Instagram captions", "tags": ["seo"]},
            {"skill_id": "brainstorm", "name": "Brainstorm",
             "description": "Generate content ideas", "tags": ["ideas"]},
        ])
        selector = SkillSelector(catalog)
        result = selector.select_by_intent("SEO caption generation")
        assert result.selected_skill_id == "seogram"
        assert result.confidence > 0

    def test_select_by_intent_no_match_fallback(self):
        catalog = make_catalog([
            {"skill_id": "s1", "name": "Z1", "description": "alpha", "tags": ["a"]},
        ])
        selector = SkillSelector(catalog)
        result = selector.select_by_intent("xyzzy")
        assert result.selected_skill_id == FALLBACK_SKILL_ID
        assert result.fallback is True

    def test_select_by_tags_exact_match(self):
        catalog = make_catalog([
            {"skill_id": "s3", "name": "C", "tags": ["x", "y", "z"]},
            {"skill_id": "s1", "name": "A", "tags": ["x", "y"]},
            {"skill_id": "s2", "name": "B", "tags": ["z"]},
        ])
        selector = SkillSelector(catalog)
        result = selector.select_by_tags(["x", "y"])
        assert result.selected_skill_id == "s3"
        assert result.confidence > 0

    def test_select_by_tags_no_match_fallback(self):
        catalog = make_catalog([{"skill_id": "s1", "name": "A", "tags": ["a"]}])
        selector = SkillSelector(catalog)
        result = selector.select_by_tags(["unknown"])
        assert result.fallback is True

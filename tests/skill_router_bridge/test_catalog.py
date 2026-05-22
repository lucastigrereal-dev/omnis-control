import json
import pytest
from pathlib import Path

from src.skills_bridge.skill_catalog import SkillCatalog
from src.skills_bridge.models import SkillDefinition, SkillRisk
from src.skills_bridge.errors import CatalogLoadError


class TestSkillCatalog:
    def test_load_empty_catalog_no_path(self):
        catalog = SkillCatalog()
        skills = catalog.load()
        assert skills == []

    def test_load_empty_catalog_nonexistent_path(self, tmp_path):
        catalog = SkillCatalog(str(tmp_path / "nonexistent.json"))
        skills = catalog.load()
        assert skills == []

    def test_load_json_catalog(self, tmp_path):
        data = {
            "skills": [
                {"skill_id": "s1", "name": "Skill 1", "risk": "LOW"},
                {"skill_id": "s2", "name": "Skill 2", "risk": "MEDIUM", "tags": ["tag1"]},
                {"skill_id": "s3", "name": "Skill 3", "risk": "HIGH"},
            ]
        }
        path = tmp_path / "catalog.json"
        path.write_text(json.dumps(data), encoding="utf-8")

        catalog = SkillCatalog(str(path))
        skills = catalog.load()
        assert len(skills) == 3
        assert skills[0].skill_id == "s1"
        assert skills[1].risk == SkillRisk.MEDIUM

    def test_load_list_format(self, tmp_path):
        data = [
            {"skill_id": "a", "name": "A"},
            {"skill_id": "b", "name": "B"},
        ]
        path = tmp_path / "list.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        catalog = SkillCatalog(str(path))
        skills = catalog.load()
        assert len(skills) == 2

    def test_load_items_key(self, tmp_path):
        data = {"items": [{"skill_id": "x", "name": "X"}]}
        path = tmp_path / "items.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        catalog = SkillCatalog(str(path))
        skills = catalog.load()
        assert len(skills) == 1
        assert skills[0].skill_id == "x"

    def test_resolve_existing_skill(self, tmp_path):
        data = {"skills": [{"skill_id": "seogram", "name": "SEOgram"}]}
        path = tmp_path / "cat.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        catalog = SkillCatalog(str(path))
        skill = catalog.resolve("seogram")
        assert skill.skill_id == "seogram"
        assert skill.name == "SEOgram"

    def test_resolve_missing_returns_empty(self):
        catalog = SkillCatalog()
        skill = catalog.resolve("nonexistent")
        assert skill.skill_id == ""
        assert skill.name == ""

    def test_resolve_by_name_case_insensitive(self, tmp_path):
        data = {"skills": [{"skill_id": "id1", "name": "Seogram"}]}
        path = tmp_path / "cat.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        catalog = SkillCatalog(str(path))
        skill = catalog.resolve("seogram")
        assert skill.skill_id == "id1"

    def test_skill_count(self, tmp_path):
        data = {"skills": [{"skill_id": f"s{i}", "name": f"S{i}"} for i in range(5)]}
        path = tmp_path / "count.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        catalog = SkillCatalog(str(path))
        assert catalog.skill_count == 5

    def test_load_cached(self, tmp_path):
        data = {"skills": [{"skill_id": "s1", "name": "S1"}]}
        path = tmp_path / "cache.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        catalog = SkillCatalog(str(path))
        skills1 = catalog.load()
        skills2 = catalog.load()
        assert skills1 is not skills2
        assert len(skills1) == len(skills2)

    def test_catalog_load_error_invalid_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json", encoding="utf-8")
        catalog = SkillCatalog(str(path))
        with pytest.raises(CatalogLoadError):
            catalog.load()

    def test_add_skill(self):
        catalog = SkillCatalog()
        catalog.add_skill(SkillDefinition(skill_id="added", name="Added"))
        assert catalog.skill_count == 1
        resolved = catalog.resolve("added")
        assert resolved.name == "Added"

    def test_add_skills(self):
        catalog = SkillCatalog()
        s1 = SkillDefinition(skill_id="a", name="A")
        s2 = SkillDefinition(skill_id="b", name="B")
        catalog.add_skills([s1, s2])
        assert catalog.skill_count == 2

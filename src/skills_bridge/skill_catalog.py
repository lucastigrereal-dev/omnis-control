"""SkillCatalog — load and resolve skills from JSON catalog or registry."""
import json
from pathlib import Path

from src.skills_bridge.models import SkillDefinition
from src.skills_bridge.errors import CatalogLoadError


class SkillCatalog:
    """Loads skills from a JSON catalog file or builds from a list.

    Merged from src/skill_router_bridge/catalog.py (archived).
    """

    def __init__(self, catalog_path: str | None = None) -> None:
        self.catalog_path = Path(catalog_path) if catalog_path else None
        self._skills: dict[str, SkillDefinition] = {}
        self._loaded = False

    def load(self) -> list[SkillDefinition]:
        if self._loaded:
            return list(self._skills.values())
        if not self.catalog_path or not self.catalog_path.exists():
            self._loaded = True
            return []
        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._skills = {}
            if isinstance(data, dict):
                skills_list = data.get("skills", data.get("items", []))
            elif isinstance(data, list):
                skills_list = data
            else:
                skills_list = []
            for entry in skills_list:
                skill = SkillDefinition.from_dict(entry)
                self._skills[skill.skill_id] = skill
            self._loaded = True
        except json.JSONDecodeError as e:
            raise CatalogLoadError(str(self.catalog_path), str(e))
        except Exception as e:
            raise CatalogLoadError(str(self.catalog_path), str(e))
        return list(self._skills.values())

    def resolve(self, skill_id: str) -> SkillDefinition:
        if not self._loaded:
            self.load()
        skill = self._skills.get(skill_id)
        if skill:
            return skill
        for sid, s in self._skills.items():
            if s.name.lower() == skill_id.lower():
                return s
        return SkillDefinition()

    @property
    def skill_count(self) -> int:
        if not self._loaded:
            self.load()
        return len(self._skills)

    def add_skill(self, skill: SkillDefinition) -> None:
        self._skills[skill.skill_id] = skill
        self._loaded = True

    def add_skills(self, skills: list[SkillDefinition]) -> None:
        for s in skills:
            self._skills[s.skill_id] = s
        self._loaded = True

    def activate_skill(self, skill_id: str) -> bool:
        """Set an in-memory skill's status to 'active'. Returns False if not found."""
        if not self._loaded:
            self.load()
        skill = self._skills.get(skill_id)
        if skill is None:
            return False
        skill.status = "active"
        return True

    def write_skill(self, skill: SkillDefinition) -> None:
        """Append skill to the JSON catalog on disk. No-op if no catalog_path is set."""
        if not self.catalog_path:
            return
        if self.catalog_path.exists():
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"skills": []}

        if isinstance(data, dict):
            skills_list = data.setdefault("skills", [])
        elif isinstance(data, list):
            skills_list = data
        else:
            return

        existing_ids = {s.get("skill_id", s.get("id", "")) for s in skills_list}
        if skill.skill_id not in existing_ids:
            skills_list.append(skill.to_dict())

        if isinstance(data, dict):
            data["skills"] = skills_list

        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._loaded = False

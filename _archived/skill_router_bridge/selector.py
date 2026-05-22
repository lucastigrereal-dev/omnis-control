from src.skill_router_bridge.models import SkillDefinition, SkillSelectorResult
from src.skill_router_bridge.catalog import SkillCatalog

FALLBACK_SKILL_ID = "manual-review"


class SkillSelector:
    def __init__(self, catalog: SkillCatalog):
        self.catalog = catalog

    def select_by_id(self, skill_id: str) -> SkillSelectorResult:
        skill = self.catalog.resolve(skill_id)
        if skill and skill.skill_id != skill_id and skill.name.lower() == skill_id.lower():
            return SkillSelectorResult(
                selected_skill_id=skill.skill_id,
                confidence=0.9,
                reason=f"Matched by name: {skill_id}",
            )
        if skill.skill_id == skill_id:
            return SkillSelectorResult(
                selected_skill_id=skill_id,
                confidence=1.0,
                reason="Exact ID match",
            )
        return SkillSelectorResult(
            selected_skill_id=FALLBACK_SKILL_ID,
            confidence=0.0,
            fallback=True,
            reason=f"Skill not found: {skill_id}",
        )

    def select_by_intent(self, intent: str) -> SkillSelectorResult:
        skills = self.catalog.load()
        intent_lower = intent.lower()
        best = None
        best_score = 0
        alternatives = []
        for skill in skills:
            score = self._match_score(skill, intent_lower)
            if score > 0:
                alternatives.append(skill.skill_id)
            if score > best_score:
                best_score = score
                best = skill.skill_id
        if best and best_score >= 1:
            return SkillSelectorResult(
                selected_skill_id=best,
                confidence=min(best_score / 3.0, 1.0),
                alternatives=[a for a in alternatives if a != best],
                reason=f"Intent match: {intent}",
            )
        return SkillSelectorResult(
            selected_skill_id=FALLBACK_SKILL_ID,
            confidence=0.0,
            fallback=True,
            alternatives=alternatives,
            reason=f"No skill matched intent: {intent}",
        )

    def select_by_tags(self, tags: list[str]) -> SkillSelectorResult:
        skills = self.catalog.load()
        tags_lower = {t.lower() for t in tags}
        best = None
        best_score = 0
        for skill in skills:
            skill_tags = {t.lower() for t in skill.tags}
            overlap = len(tags_lower & skill_tags)
            if overlap > best_score:
                best_score = overlap
                best = skill.skill_id
        if best and best_score > 0:
            return SkillSelectorResult(
                selected_skill_id=best,
                confidence=min(best_score / len(tags_lower), 1.0),
                reason=f"Tag match: {best_score} tags",
            )
        return SkillSelectorResult(
            selected_skill_id=FALLBACK_SKILL_ID,
            confidence=0.0,
            fallback=True,
            reason=f"No tags matched: {tags}",
        )

    def _match_score(self, skill: SkillDefinition, intent_lower: str) -> int:
        score = 0
        if intent_lower in skill.name.lower():
            score += 3
        if intent_lower in skill.description.lower():
            score += 2
        for tag in skill.tags:
            if intent_lower in tag.lower():
                score += 1
        words = [w for w in intent_lower.split() if len(w) > 2]
        for word in words:
            if word in skill.name.lower():
                score += 1
            if word in skill.description.lower():
                score += 1
            for tag in skill.tags:
                if word in tag.lower() or tag.lower() in word:
                    score += 1
        return score

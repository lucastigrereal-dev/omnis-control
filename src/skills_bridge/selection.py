from typing import Optional

from src.skills_bridge.models import SkillCall, SkillSelection, SkillIntent, SkillDefinition, SkillSelectorResult
from src.skills_bridge.errors import SkillNotFoundError
from src.skills_bridge.dryrun import FALLBACK_SKILL_ID


MOCK_SKILLS = [
    {
        "skill_id": "jarvis-router",
        "name": "Jarvis Router",
        "intents": [SkillIntent.READ, SkillIntent.ANALYZE],
        "tags": ["router", "intent", "classify", "dispatch"],
    },
    {
        "skill_id": "jarvis-brain",
        "name": "Jarvis Brain",
        "intents": [SkillIntent.ANALYZE, SkillIntent.GENERATE],
        "tags": ["brain", "context", "memory", "analyse"],
    },
    {
        "skill_id": "generate_seogram_caption",
        "name": "Generate SEOgram Caption",
        "intents": [SkillIntent.CREATE, SkillIntent.GENERATE],
        "tags": ["seo", "caption", "instagram", "content", "social"],
    },
    {
        "skill_id": "create_instagram_carousel",
        "name": "Create Instagram Carousel",
        "intents": [SkillIntent.CREATE, SkillIntent.GENERATE],
        "tags": ["instagram", "carousel", "design", "content", "social"],
    },
    {
        "skill_id": "revenue-tracker",
        "name": "Revenue Tracker",
        "intents": [SkillIntent.READ, SkillIntent.ANALYZE],
        "tags": ["revenue", "finance", "tracking", "metrics"],
    },
    {
        "skill_id": "crm-pipeline",
        "name": "CRM Pipeline",
        "intents": [SkillIntent.READ, SkillIntent.UPDATE],
        "tags": ["crm", "sales", "pipeline", "leads"],
    },
    {
        "skill_id": "manual-review",
        "name": "Manual Review",
        "intents": [],
        "tags": ["manual", "fallback", "review"],
    },
]


def _definition_to_skill(definition: SkillDefinition) -> dict:
    """Converte um SkillDefinition para o formato interno do SkillSelector."""
    intents = []
    for intent_str in definition.intents:
        try:
            intents.append(SkillIntent(intent_str))
        except ValueError:
            pass
    return {
        "skill_id": definition.skill_id,
        "name": definition.name,
        "description": definition.description,
        "intents": intents,
        "tags": definition.tags,
    }


class SkillSelector:

    def __init__(self, catalog: "SkillCatalog | None" = None, dry_run: bool = True):
        self.dry_run = dry_run
        self.catalog = catalog
        self.skills = list(MOCK_SKILLS)
        if catalog is not None:
            try:
                self._skills_list = catalog.load() if callable(getattr(catalog, "load", None)) else []
            except Exception:
                self._skills_list = []
            if self._skills_list:
                self.skills = [_definition_to_skill(skill) for skill in self._skills_list]
        else:
            self._skills_list = []

    def select_by_id(self, skill_id: str) -> SkillSelectorResult:
        """Select skill by ID or name (case-insensitive). Returns SkillSelectorResult."""
        for skill in self._skills_list:
            if skill.skill_id == skill_id:
                return SkillSelectorResult(
                    selected_skill_id=skill.skill_id,
                    confidence=1.0,
                    reason=f"Exact ID match: {skill_id}",
                )
        for skill in self._skills_list:
            if skill.name.lower() == skill_id.lower():
                return SkillSelectorResult(
                    selected_skill_id=skill.skill_id,
                    confidence=0.9,
                    reason=f"Name match: {skill_id}",
                )
        return SkillSelectorResult(
            selected_skill_id=FALLBACK_SKILL_ID,
            confidence=0.0,
            fallback=True,
            reason=f"Skill '{skill_id}' not found"
        )

    def select_by_intent(self, intent_text: str) -> SkillSelectorResult:
        """Select skill by intent text matching description and tags. Returns SkillSelectorResult."""
        intent_lower = intent_text.lower()
        for skill in self._skills_list:
            if intent_lower in skill.description.lower():
                return SkillSelectorResult(
                    selected_skill_id=skill.skill_id,
                    confidence=0.7,
                    reason=f"Intent match in description: {intent_text}",
                )
            for tag in skill.tags:
                if tag.lower() in intent_lower:
                    return SkillSelectorResult(
                        selected_skill_id=skill.skill_id,
                        confidence=0.6,
                        reason=f"Intent match via tag '{tag}': {intent_text}",
                    )
        return SkillSelectorResult(
            selected_skill_id=FALLBACK_SKILL_ID,
            confidence=0.0,
            fallback=True,
            reason=f"No skill for intent: {intent_text}"
        )

    def select_by_tags(self, tags: list[str]) -> SkillSelectorResult:
        """Select skill by tags — picks the one with the most matching tags. Returns SkillSelectorResult."""
        best = None
        best_score = 0
        for skill in self._skills_list:
            score = len(set(tags) & set(skill.tags))
            if score > best_score:
                best_score = score
                best = skill
        if best and best_score > 0:
            return SkillSelectorResult(
                selected_skill_id=best.skill_id,
                confidence=min(0.5 + best_score * 0.2, 1.0),
                reason=f"Tag match: {best_score} tags",
            )
        return SkillSelectorResult(
            selected_skill_id=FALLBACK_SKILL_ID,
            confidence=0.0,
            fallback=True,
            reason="No matching tags"
        )

    def select(self, call: SkillCall) -> SkillSelection:
        if call.skill_id:
            return self._select_by_id(call)

        if call.tags:
            return self._select_by_tags(call)

        if call.intent != SkillIntent.UNKNOWN:
            return self._select_by_intent(call)

        return self._fallback(call)

    def _select_by_id(self, call: SkillCall) -> SkillSelection:
        for skill in self.skills:
            if skill["skill_id"] == call.skill_id:
                return SkillSelection(
                    skill_id=skill["skill_id"],
                    skill_name=skill["name"],
                    intent=call.intent,
                    confidence=1.0,
                    reason=f"Direct match: {call.skill_id}",
                )
        return self._fallback(call, reason=f"Skill '{call.skill_id}' not found")

    def _select_by_intent(self, call: SkillCall) -> SkillSelection:
        matches = [
            s for s in self.skills
            if call.intent in s["intents"]
        ]
        if not matches:
            return self._fallback(call, reason=f"No skill for intent '{call.intent.value}'")

        best = matches[0]
        return SkillSelection(
            skill_id=best["skill_id"],
            skill_name=best["name"],
            intent=call.intent,
            confidence=0.7,
            fallback_skill_id="manual-review",
            reason=f"Intent match: {call.intent.value}",
            tags=best.get("tags", []),
        )

    def _select_by_tags(self, call: SkillCall) -> SkillSelection:
        best = None
        best_score = 0
        for skill in self.skills:
            score = len(set(call.tags) & set(skill.get("tags", [])))
            if score > best_score:
                best_score = score
                best = skill

        if best and best_score > 0:
            return SkillSelection(
                skill_id=best["skill_id"],
                skill_name=best["name"],
                intent=call.intent,
                confidence=min(0.5 + best_score * 0.2, 1.0),
                fallback_skill_id="manual-review",
                reason=f"Tag match: {best_score} tags matched",
                tags=best.get("tags", []),
            )

        return self._fallback(call, reason=f"No skills match tags: {call.tags}")

    def _fallback(
        self, call: SkillCall, reason: str = ""
    ) -> SkillSelection:
        return SkillSelection(
            skill_id="manual-review",
            skill_name="Manual Review",
            intent=call.intent,
            confidence=0.0,
            requires_manual_review=True,
            reason=reason or "No matching skill found",
            tags=["manual", "fallback"],
        )

    def select_by_project(self, project: str, intent: SkillIntent) -> SkillSelection:
        tags = project.lower().replace("-", " ").replace("_", " ").split()
        call = SkillCall(intent=intent, tags=tags)
        return self.select(call)

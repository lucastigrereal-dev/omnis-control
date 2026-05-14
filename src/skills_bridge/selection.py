from src.skills_bridge.models import SkillCall, SkillSelection, SkillIntent
from src.skills_bridge.errors import SkillNotFoundError


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


class SkillSelector:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.skills = list(MOCK_SKILLS)

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

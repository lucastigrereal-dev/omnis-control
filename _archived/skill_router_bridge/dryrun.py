from datetime import datetime, timezone

from src.skill_router_bridge.models import SkillCall, SkillSelectorResult
from src.skill_router_bridge.catalog import SkillCatalog
from src.skill_router_bridge.errors import SkillNotAvailableError, DispatchError


class DryRunDispatcher:
    def __init__(self, catalog: SkillCatalog, dry_run: bool = True):
        self.catalog = catalog
        self.dry_run = dry_run
        self._history: list[dict] = []

    def dispatch(self, call: SkillCall) -> dict:
        if self.dry_run:
            return self._simulate(call)
        raise DispatchError(call.skill_id, "Real dispatch not implemented (dry_run only)")

    def _simulate(self, call: SkillCall) -> dict:
        skill = self.catalog.resolve(call.skill_id)
        available = skill is not None and skill.skill_id not in ("", FALLBACK_SKILL_ID)
        if not available and call.skill_id != FALLBACK_SKILL_ID:
            skill = self.catalog.resolve(FALLBACK_SKILL_ID)

        result = {
            "call_id": call.call_id,
            "skill_id": call.skill_id,
            "resolved_skill": skill.skill_id if skill else FALLBACK_SKILL_ID,
            "dry_run": True,
            "status": "DRY_RUN_OK",
            "output": {
                "message": f"Dry-run of {call.skill_id} with intent: {call.intent}",
                "payload_echo": call.payload,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if call.skill_id != result["resolved_skill"]:
            result["status"] = "FALLBACK"
            result["output"]["message"] = f"Fell back to {result['resolved_skill']} (requested: {call.skill_id})"

        self._history.append(result)
        return result

    @property
    def history(self) -> list[dict]:
        return list(self._history)


FALLBACK_SKILL_ID = "manual-review"

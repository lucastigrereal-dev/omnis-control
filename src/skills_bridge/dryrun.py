from datetime import datetime, timezone

from src.skills_bridge.models import SkillCall, SkillDefinition
from src.skills_bridge.errors import DryRunError, DispatchError
from src.skills_bridge.skill_catalog import SkillCatalog

FALLBACK_SKILL_ID = "manual-review"


class DryRunEngine:
    """Canonical dry-run engine. Records all calls, never executes for real."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.records: list[dict[str, object]] = []

    def execute(self, call: SkillCall) -> dict[str, object]:
        if not call.dry_run:
            if hasattr(call, 'risk_level') and call.risk_level.upper() in ("HIGH", "CRITICAL"):
                raise DryRunError(
                    f"Cannot execute non-dry-run on {call.risk_level} risk "
                    f"skill '{call.skill_id}'"
                )

        intent_val = call.intent.value if hasattr(call.intent, 'value') else str(call.intent)
        record = {
            "call_id": call.call_id,
            "skill_id": call.skill_id,
            "intent": intent_val,
            "dry_run": call.dry_run,
            "risk_level": getattr(call, 'risk_level', 'LOW'),
            "status": "dry_run_completed",
            "artifacts_simulated": getattr(call, 'expected_artifacts', []),
            "output": f"[DRY_RUN] Skill '{call.skill_id}' would execute "
                      f"with intent '{intent_val}'",
        }
        self.records.append(record)
        return record

    def get_records(self) -> list[dict[str, object]]:
        return self.records

    def clear(self) -> None:
        self.records.clear()


class DryRunDispatcher:
    """Alias for DryRunEngine from skill_router_bridge merge. Uses SkillCatalog for resolution."""

    def __init__(self, catalog: SkillCatalog, dry_run: bool = True) -> None:
        self.catalog = catalog
        self.dry_run = dry_run
        self._history: list[dict[str, object]] = []

    def dispatch(self, call: SkillCall) -> dict[str, object]:
        if self.dry_run:
            return self._simulate(call)
        raise DispatchError(call.skill_id, "Real dispatch not implemented (dry_run only)")

    def _simulate(self, call: SkillCall) -> dict[str, object]:
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
                "message": f"Dry-run of {call.skill_id} with intent: {getattr(call, 'intent', '')}",
                "payload_echo": getattr(call, 'payload', {}),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if call.skill_id != result["resolved_skill"]:
            result["status"] = "FALLBACK"
            result["output"]["message"] = f"Fell back to {result['resolved_skill']} (requested: {call.skill_id})"

        self._history.append(result)
        return result

    @property
    def history(self) -> list[dict[str, object]]:
        return list(self._history)

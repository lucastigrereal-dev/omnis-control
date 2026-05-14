from src.skills_bridge.models import SkillCall
from src.skills_bridge.errors import DryRunError


class DryRunEngine:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.records: list[dict] = []

    def execute(self, call: SkillCall) -> dict:
        if not call.dry_run:
            if call.risk_level.upper() in ("HIGH", "CRITICAL"):
                raise DryRunError(
                    f"Cannot execute non-dry-run on {call.risk_level} risk "
                    f"skill '{call.skill_id}'"
                )

        record = {
            "call_id": call.call_id,
            "skill_id": call.skill_id,
            "intent": call.intent.value,
            "dry_run": call.dry_run,
            "risk_level": call.risk_level,
            "status": "dry_run_completed",
            "artifacts_simulated": call.expected_artifacts,
            "output": f"[DRY_RUN] Skill '{call.skill_id}' would execute "
                      f"with intent '{call.intent.value}'",
        }
        self.records.append(record)
        return record

    def get_records(self) -> list[dict]:
        return self.records

    def clear(self) -> None:
        self.records.clear()

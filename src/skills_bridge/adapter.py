from abc import ABC, abstractmethod
from src.skills_bridge.models import SkillCall
from src.skills_bridge.selection import SkillSelector
from src.skills_bridge.dryrun import DryRunEngine


class SkillAdapter(ABC):

    @abstractmethod
    def call_skill(self, call: SkillCall) -> dict:
        ...

    @abstractmethod
    def health_check(self) -> bool:
        ...


class MockSkillAdapter(SkillAdapter):

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.selector = SkillSelector(dry_run=dry_run)
        self.dryrun_engine = DryRunEngine(dry_run=dry_run)
        self.calls: list[SkillCall] = []

    def call_skill(self, call: SkillCall) -> dict:
        self.calls.append(call)
        selection = self.selector.select(call)

        if selection.requires_manual_review:
            return {
                "status": "needs_manual_review",
                "selection": selection.to_dict(),
                "output": f"Skill '{call.skill_id or call.intent.value}' "
                          f"requires manual review",
            }

        if call.dry_run:
            return self.dryrun_engine.execute(call)

        return {
            "status": "executed",
            "skill_id": call.skill_id,
            "selection": selection.to_dict(),
            "output": f"Skill '{call.skill_id}' executed successfully",
        }

    def health_check(self) -> bool:
        return True

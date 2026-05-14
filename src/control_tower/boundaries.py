from src.control_tower.models import BoundarySystem, BoundaryRule
from src.control_tower.errors import BoundaryViolationError


DEFAULT_BOUNDARIES: list[BoundaryRule] = [
    BoundaryRule(
        source_system=BoundarySystem.OMNIS,
        target_system=BoundarySystem.KRATOS,
        allowed_actions=["read_status", "health_check"],
        forbidden_actions=["write", "modify", "delete", "execute", "configure"],
    ),
    BoundaryRule(
        source_system=BoundarySystem.OMNIS,
        target_system=BoundarySystem.AURORA,
        allowed_actions=["read_work_order", "submit_report"],
        forbidden_actions=["modify_canon", "override_decision"],
    ),
    BoundaryRule(
        source_system=BoundarySystem.OMNIS,
        target_system=BoundarySystem.AKASHA,
        allowed_actions=["read_memory", "query", "write_event"],
        forbidden_actions=["delete_memory", "modify_vector"],
    ),
    BoundaryRule(
        source_system=BoundarySystem.OMNIS,
        target_system=BoundarySystem.SKILLS,
        allowed_actions=["call_skill", "dry_run_skill", "list_skills"],
        forbidden_actions=["modify_skill", "delete_skill", "register_skill"],
    ),
    BoundaryRule(
        source_system=BoundarySystem.OMNIS,
        target_system=BoundarySystem.LUCAS,
        allowed_actions=["request_approval", "send_report", "notify"],
        forbidden_actions=["decide", "approve", "override"],
    ),
]


class BoundaryGuard:

    def __init__(self, boundaries: list[BoundaryRule] | None = None,
                 dry_run: bool = True):
        self.boundaries = boundaries or DEFAULT_BOUNDARIES
        self.dry_run = dry_run

    def check(
        self,
        source: BoundarySystem,
        target: BoundarySystem,
        action: str,
    ) -> bool:
        for rule in self.boundaries:
            if rule.source_system == source and rule.target_system == target:
                return rule.allows(action)
        return False

    def guard(
        self,
        source: BoundarySystem,
        target: BoundarySystem,
        action: str,
    ) -> None:
        if not self.check(source, target, action):
            raise BoundaryViolationError(
                f"Boundary violation: {source.value} cannot "
                f"'{action}' on {target.value}"
            )

    def get_forbidden_actions(
        self, source: BoundarySystem, target: BoundarySystem
    ) -> list[str]:
        for rule in self.boundaries:
            if rule.source_system == source and rule.target_system == target:
                return rule.forbidden_actions
        return []

    def get_allowed_actions(
        self, source: BoundarySystem, target: BoundarySystem
    ) -> list[str]:
        for rule in self.boundaries:
            if rule.source_system == source and rule.target_system == target:
                return rule.allowed_actions
        return []

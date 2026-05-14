from src.control_tower.models import (
    Decision,
    TowerRequest,
    ActionType,
    RiskLevel,
    BoundarySystem,
)
from src.control_tower.risk import RiskClassifier
from src.control_tower.boundaries import BoundaryGuard
from src.control_tower.errors import RiskBlockedError


class DecisionEngine:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.risk_classifier = RiskClassifier(dry_run=dry_run)
        self.boundary_guard = BoundaryGuard(dry_run=dry_run)
        self.history: list[Decision] = []

    def evaluate(self, request: TowerRequest) -> Decision:
        risk = self.risk_classifier.classify(
            action=request.action,
            target_system=request.target_system.value,
            is_external=request.is_external,
            is_destructive=request.is_destructive,
            paths_touched=request.paths_touched,
        )

        boundary_ok = self.boundary_guard.check(
            source=request.source_system,
            target=request.target_system,
            action=request.action,
        )

        if not boundary_ok and request.target_system != BoundarySystem.OMNIS:
            action_type = ActionType.BLOCK
            rationale = (
                f"Boundary violation: {request.source_system.value} cannot "
                f"'{request.action}' on {request.target_system.value}"
            )
            requires_human = True
        elif risk == RiskLevel.CRITICAL:
            action_type = ActionType.BLOCK
            rationale = f"Action '{request.action}' classified as CRITICAL risk"
            requires_human = True
        elif risk == RiskLevel.HIGH:
            action_type = ActionType.EXECUTE_WITH_APPROVAL
            rationale = f"Action '{request.action}' classified as HIGH risk"
            requires_human = True
        elif risk == RiskLevel.MEDIUM:
            action_type = ActionType.DRY_RUN
            rationale = f"Action '{request.action}' classified as MEDIUM risk"
            requires_human = False
        else:
            if request.is_destructive or request.is_external:
                action_type = ActionType.DRY_RUN
                rationale = "Low risk but has external/destructive flags"
                requires_human = False
            else:
                action_type = ActionType.OBSERVE
                rationale = "Low risk, local action"
                requires_human = False

        do_not_do = self.boundary_guard.get_forbidden_actions(
            source=request.source_system,
            target=request.target_system,
        )

        decision = Decision(
            title=request.title,
            recommendation=rationale,
            risk_level=risk,
            action_type=action_type,
            requires_human_approval=requires_human,
            rationale=rationale,
            do_not_do=do_not_do,
            next_step=(
                "Request human approval before proceeding"
                if requires_human
                else "Proceed with dry run"
                if action_type == ActionType.DRY_RUN
                else "Proceed with observation only"
            ),
            request_id=request.request_id,
        )

        self.history.append(decision)
        return decision

    def get_history(self) -> list[Decision]:
        return self.history

    def last_decision(self) -> Decision | None:
        return self.history[-1] if self.history else None

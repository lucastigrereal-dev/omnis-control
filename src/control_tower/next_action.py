from src.control_tower.models import (
    NextAction,
    Decision,
    ActionType,
    BoundarySystem,
)


class NextActionGenerator:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def generate(self, decision: Decision) -> NextAction:
        target = BoundarySystem.OMNIS
        action = decision.action_type.value

        dry_run_required = decision.action_type in (
            ActionType.DRY_RUN,
            ActionType.EXECUTE_WITH_APPROVAL,
        )
        requires_approval = decision.requires_human_approval

        description = (
            f"Decision {decision.decision_id}: {decision.recommendation}. "
            f"Risk: {decision.risk_level.value}."
        )

        if decision.action_type == ActionType.BLOCK:
            description += " ACTION BLOCKED."
            action = "blocked"
        elif decision.action_type == ActionType.OBSERVE:
            description += " Observe only."
            action = "observe"
        elif decision.action_type == ActionType.DRY_RUN:
            description += " Execute dry run."
            action = "dry_run"
        elif decision.action_type == ActionType.EXECUTE_WITH_APPROVAL:
            description += " AWAITING HUMAN APPROVAL."
            action = "awaiting_approval"

        return NextAction(
            decision_id=decision.decision_id,
            title=decision.title or "Next Action",
            description=description,
            target_system=target,
            action=action,
            dry_run_required=dry_run_required,
            requires_approval=requires_approval,
            expected_output=(
                "Dry run report"
                if dry_run_required
                else "Observation report"
            ),
        )

    def generate_from_request(
        self, decision: Decision, target_system: BoundarySystem,
        action: str, dry_run_required: bool = True,
        requires_approval: bool = False,
    ) -> NextAction:
        return NextAction(
            decision_id=decision.decision_id,
            title=decision.title or action,
            description=decision.rationale,
            target_system=target_system,
            action=action,
            dry_run_required=dry_run_required,
            requires_approval=requires_approval,
            expected_output="Execution report",
        )

from src.observability.models import RollbackPlan, RollbackStatus


class RollbackEngine:
    def __init__(self):
        self._plans: dict[str, RollbackPlan] = {}

    def plan(self, contract_id: str, rollback_hint: str = "") -> RollbackPlan:
        steps = []
        is_reversible = True
        if rollback_hint:
            steps.append(rollback_hint)
        if not rollback_hint or "irreversible" in rollback_hint.lower():
            is_reversible = False

        plan = RollbackPlan(
            contract_id=contract_id,
            status=RollbackStatus.POSSIBLE if is_reversible else RollbackStatus.NOT_POSSIBLE,
            steps=steps,
            is_reversible=is_reversible,
            hint=rollback_hint,
        )
        self._plans[contract_id] = plan
        return plan

    def can_rollback(self, contract_id: str) -> bool:
        plan = self._plans.get(contract_id)
        if not plan:
            return False
        return plan.is_reversible

    def get_plan(self, contract_id: str) -> RollbackPlan | None:
        return self._plans.get(contract_id)

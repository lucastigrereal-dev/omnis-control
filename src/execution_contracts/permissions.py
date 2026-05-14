from src.execution_contracts.models import ExecutionContract
from src.execution_contracts.errors import PermissionError


class PermissionChecker:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def check_action(self, contract: ExecutionContract, action: str) -> bool:
        if action in contract.forbidden_actions:
            return False
        if contract.allowed_actions and action not in contract.allowed_actions:
            return False
        return True

    def check_approval(self, contract: ExecutionContract) -> None:
        if contract.requires_approval and contract.status.value not in (
            "APPROVED", "EXECUTING", "COMPLETED"
        ):
            raise PermissionError(
                f"Contract '{contract.contract_id}' requires approval but "
                f"status is '{contract.status.value}'. Must be APPROVED."
            )

    def check_dry_run(self, contract: ExecutionContract) -> None:
        if contract.dry_run_required and contract.status.value not in (
            "EXECUTING", "COMPLETED"
        ):
            raise PermissionError(
                f"Contract '{contract.contract_id}' requires a dry-run before "
                f"execution. Status is '{contract.status.value}'."
            )

    def check_all(self, contract: ExecutionContract, action: str = "") -> list[str]:
        issues: list[str] = []

        if action and not self.check_action(contract, action):
            issues.append(f"Action '{action}' is not permitted by contract")

        try:
            self.check_approval(contract)
        except PermissionError as e:
            issues.append(str(e))

        try:
            self.check_dry_run(contract)
        except PermissionError as e:
            issues.append(str(e))

        return issues

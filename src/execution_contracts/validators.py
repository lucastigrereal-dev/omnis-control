from pathlib import Path

from src.execution_contracts.models import ExecutionContract, ContractStatus
from src.execution_contracts.errors import ValidationError


class ContractValidator:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def validate(self, contract: ExecutionContract) -> list[str]:
        errors: list[str] = []

        if not contract.title.strip():
            errors.append("Contract title is required")

        if not contract.project.strip():
            errors.append("Contract project is required")

        if not contract.target_system.strip():
            errors.append("Contract target_system is required")

        if not contract.allowed_actions and not contract.allowed_paths:
            errors.append(
                "Contract must specify at least one allowed_action or allowed_path"
            )

        path_errors = self._validate_paths(contract)
        errors.extend(path_errors)

        return errors

    def _validate_paths(self, contract: ExecutionContract) -> list[str]:
        errors: list[str] = []

        for forbidden in contract.forbidden_paths:
            for allowed in contract.allowed_paths:
                if str(Path(allowed)).startswith(str(Path(forbidden))):
                    errors.append(
                        f"Allowed path '{allowed}' is inside forbidden path "
                        f"'{forbidden}' — contract cannot proceed"
                    )

        for action_path in contract.allowed_paths:
            for forbidden in contract.forbidden_paths:
                if str(Path(action_path)).startswith(str(Path(forbidden))):
                    errors.append(
                        f"Action path '{action_path}' violates forbidden "
                        f"path '{forbidden}'"
                    )

        return errors

    def is_valid(self, contract: ExecutionContract) -> bool:
        return len(self.validate(contract)) == 0

    def check_path_allowed(self, contract: ExecutionContract, path: str) -> bool:
        if not contract.allowed_paths:
            return True

        path_obj = Path(path)
        for allowed in contract.allowed_paths:
            allowed_obj = Path(allowed)
            try:
                path_obj.resolve().relative_to(allowed_obj.resolve())
                return True
            except ValueError:
                continue
        return False

    def check_path_forbidden(self, contract: ExecutionContract, path: str) -> bool:
        path_obj = Path(path)
        for forbidden in contract.forbidden_paths:
            forbidden_obj = Path(forbidden)
            try:
                path_obj.resolve().relative_to(forbidden_obj.resolve())
                return True
            except ValueError:
                continue
        return False

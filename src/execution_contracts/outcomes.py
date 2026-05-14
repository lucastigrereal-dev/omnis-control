from src.execution_contracts.models import (
    ExecutionContract, ContractOutcome, OutcomeStatus,
)


class OutcomeGenerator:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def generate(
        self,
        contract: ExecutionContract,
        status: OutcomeStatus,
        summary: str = "",
    ) -> ContractOutcome:
        return ContractOutcome(
            contract_id=contract.contract_id,
            status=status,
            summary=summary,
        )

    def planned(self, contract: ExecutionContract) -> ContractOutcome:
        return self.generate(
            contract,
            OutcomeStatus.PLANNED,
            f"Contract '{contract.title}' planned. Awaiting validation.",
        )

    def dry_run_ok(
        self,
        contract: ExecutionContract,
        changed_files: list[str] | None = None,
    ) -> ContractOutcome:
        return ContractOutcome(
            contract_id=contract.contract_id,
            status=OutcomeStatus.DRY_RUN_OK,
            summary=f"Dry-run of '{contract.title}' completed successfully",
            changed_files=changed_files or [],
            tests_run=0,
            tests_passed=0,
            next_recommendation="Proceed to execution with approval",
        )

    def blocked(
        self, contract: ExecutionContract, reason: str = ""
    ) -> ContractOutcome:
        return ContractOutcome(
            contract_id=contract.contract_id,
            status=OutcomeStatus.BLOCKED,
            summary=f"Contract '{contract.title}' blocked: {reason}",
            errors=[reason],
            next_recommendation="Review and fix blocking issues before retrying",
        )

    def executed(
        self,
        contract: ExecutionContract,
        tests_run: int = 0,
        tests_passed: int = 0,
        changed_files: list[str] | None = None,
        reports: list[str] | None = None,
    ) -> ContractOutcome:
        return ContractOutcome(
            contract_id=contract.contract_id,
            status=OutcomeStatus.EXECUTED,
            summary=f"Contract '{contract.title}' executed",
            changed_files=changed_files or [],
            tests_run=tests_run,
            tests_passed=tests_passed,
            reports_generated=reports or [],
            next_recommendation="Verify results and close contract",
        )

    def needs_approval(self, contract: ExecutionContract) -> ContractOutcome:
        return ContractOutcome(
            contract_id=contract.contract_id,
            status=OutcomeStatus.NEEDS_APPROVAL,
            summary=f"Contract '{contract.title}' requires human approval",
            next_recommendation="Submit for human approval before execution",
        )

    def failed(
        self, contract: ExecutionContract, errors: list[str] | None = None
    ) -> ContractOutcome:
        return ContractOutcome(
            contract_id=contract.contract_id,
            status=OutcomeStatus.FAILED,
            summary=f"Contract '{contract.title}' failed",
            errors=errors or [],
            next_recommendation="Review errors and create new contract if needed",
        )

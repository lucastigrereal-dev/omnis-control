"""P28 ImprovementExecutor — implements approved improvement proposals."""
from typing import Optional

from src.self_improvement.models import (
    ImprovementProposal, ImpactMeasurement,
    IMPL_CODE_CHANGE, IMPL_CONFIG_CHANGE, IMPL_NEW_CAPABILITY, IMPL_PROCESS_CHANGE,
    PROPOSAL_APPROVED, PROPOSAL_IMPLEMENTED, PROPOSAL_ROLLED_BACK,
    VERDICT_INSUFFICIENT_DATA,
)
from src.self_improvement.errors import ExecutionError


class ImprovementExecutor:
    """Implements approved improvement proposals. Dry-run safe."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._measurements: list[ImpactMeasurement] = []
        self._rolled_back: list[str] = []

    def execute(self, proposal: ImprovementProposal) -> ImpactMeasurement:
        """Implement a proposal. Returns a measurement for tracking."""
        if proposal.status != PROPOSAL_APPROVED:
            raise ExecutionError(f"Proposal {proposal.proposal_id} is not approved (status: {proposal.status})")

        if self.dry_run:
            m = ImpactMeasurement.new(
                proposal.proposal_id,
                metric="estimated",
                verdict=VERDICT_INSUFFICIENT_DATA,
            )
            self._measurements.append(m)
            return m

        # Route to implementation handler
        impl_type = proposal.implementation_type
        if impl_type == IMPL_CODE_CHANGE:
            m = self._execute_code_change(proposal)
        elif impl_type == IMPL_CONFIG_CHANGE:
            m = self._execute_config_change(proposal)
        elif impl_type == IMPL_NEW_CAPABILITY:
            m = self._execute_new_capability(proposal)
        elif impl_type == IMPL_PROCESS_CHANGE:
            m = self._execute_process_change(proposal)
        else:
            raise ExecutionError(f"Unknown implementation type: {impl_type}")

        proposal.status = PROPOSAL_IMPLEMENTED
        self._measurements.append(m)
        return m

    # ── Implementation handlers ───────────────────────────────────

    def _execute_code_change(self, proposal: ImprovementProposal) -> ImpactMeasurement:
        return ImpactMeasurement.new(proposal.proposal_id, metric="code_change_applied",
                                     verdict=VERDICT_INSUFFICIENT_DATA, sample_size=0)

    def _execute_config_change(self, proposal: ImprovementProposal) -> ImpactMeasurement:
        return ImpactMeasurement.new(proposal.proposal_id, metric="config_change_applied",
                                     verdict=VERDICT_INSUFFICIENT_DATA, sample_size=0)

    def _execute_new_capability(self, proposal: ImprovementProposal) -> ImpactMeasurement:
        return ImpactMeasurement.new(proposal.proposal_id, metric="new_capability_scaffolded",
                                     verdict=VERDICT_INSUFFICIENT_DATA, sample_size=0)

    def _execute_process_change(self, proposal: ImprovementProposal) -> ImpactMeasurement:
        return ImpactMeasurement.new(proposal.proposal_id, metric="process_change_documented",
                                     verdict=VERDICT_INSUFFICIENT_DATA, sample_size=0)

    # ── Rollback ──────────────────────────────────────────────────

    def rollback(self, proposal_id: str) -> bool:
        """Roll back an implemented proposal."""
        self._rolled_back.append(proposal_id)
        for m in self._measurements:
            if m.proposal_id == proposal_id:
                self._measurements.remove(m)
                break
        return True

    # ── Query ─────────────────────────────────────────────────────

    def get_measurements(self) -> list[ImpactMeasurement]:
        return list(self._measurements)

    @property
    def implemented_count(self) -> int:
        return len(self._measurements)

    @property
    def rolled_back_count(self) -> int:
        return len(self._rolled_back)

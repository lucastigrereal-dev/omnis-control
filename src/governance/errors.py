"""Governance module errors."""


class GovernanceError(Exception):
    pass


class RiskClassificationError(GovernanceError):
    pass


class PolicyViolationError(GovernanceError):
    pass


class ScopeViolationError(GovernanceError):
    pass


class AuditError(GovernanceError):
    pass


class DecisionError(GovernanceError):
    pass

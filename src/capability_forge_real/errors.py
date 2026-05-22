"""Errors for Capability Forge Real — merged from capabilityforge + capability_forge_lite."""


class ForgeLiteError(Exception):
    pass


class ForgeRealError(Exception):
    pass


class GapNotFoundError(ForgeLiteError):
    pass


class ProposalNotFoundError(ForgeLiteError):
    pass


class ProposalNotApprovedError(ForgeLiteError):
    pass


class DuplicateCapabilityError(ForgeLiteError):
    pass


class BuildError(ForgeRealError):
    pass


class ScaffoldError(BuildError):
    pass


class PolicyScanError(BuildError):
    pass


class TestGenerationError(BuildError):
    pass


class RegistrationError(ForgeRealError):
    pass


class RollbackError(ForgeRealError):
    pass

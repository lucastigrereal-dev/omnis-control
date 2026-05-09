"""Errors for Capability Forge Lite."""


class ForgeLiteError(Exception):
    pass


class GapNotFoundError(ForgeLiteError):
    pass


class ProposalNotFoundError(ForgeLiteError):
    pass


class ProposalNotApprovedError(ForgeLiteError):
    pass


class DuplicateCapabilityError(ForgeLiteError):
    pass

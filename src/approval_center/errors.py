"""Errors for Approval Center."""


class ApprovalCenterError(Exception):
    pass


class ApprovalNotFoundError(ApprovalCenterError):
    pass


class ApprovalAlreadyResolvedError(ApprovalCenterError):
    pass

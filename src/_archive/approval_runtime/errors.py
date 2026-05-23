class ApprovalError(Exception):
    """Base error for approval runtime operations."""
    pass


class UnauthorizedApprovalError(ApprovalError):
    def __init__(self, request_id: str):
        super().__init__(f"Unauthorized approval attempt for request: {request_id}")


class InvalidTokenError(ApprovalError):
    def __init__(self, token: str):
        super().__init__(f"Invalid or expired approval token: {token}")


class AlreadyDecidedError(ApprovalError):
    def __init__(self, request_id: str):
        super().__init__(f"Approval request already decided: {request_id}")

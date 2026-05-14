"""P27 Real World Actions — error hierarchy."""


class RealWorldActionError(Exception):
    """Base error for P27 actions."""
    pass


class UnknownActionError(RealWorldActionError):
    """Action not found in registry."""
    pass


class ActionBlockedError(RealWorldActionError):
    """Action blocked by sandbox or policy."""
    pass


class AdapterUnavailableError(RealWorldActionError):
    """Provider adapter is offline or not responding."""
    pass


class RateLimitError(RealWorldActionError):
    """Rate limit exceeded for provider or action."""
    pass


class ActionDeniedError(RealWorldActionError):
    """Action denied by approval chain."""
    pass


class ActionTimeoutError(RealWorldActionError):
    """Action exceeded timeout."""
    pass


class InvalidParamsError(RealWorldActionError):
    """Parameters failed validation against input_schema."""
    pass

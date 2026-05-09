"""Errors for Squad Execution."""


class SquadExecutionError(Exception):
    pass


class SquadRunNotFoundError(SquadExecutionError):
    pass

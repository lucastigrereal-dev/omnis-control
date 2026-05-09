"""Errors for Task Decomposer."""


class TaskDecomposerError(Exception):
    pass


class CyclicDependencyError(TaskDecomposerError):
    pass

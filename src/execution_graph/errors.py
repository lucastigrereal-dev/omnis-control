"""Errors for Execution Graph module."""


class ExecutionGraphError(Exception):
    """Base error for execution graph operations."""


class InvalidGraphError(ExecutionGraphError):
    """Graph structure is invalid (missing deps, broken edges)."""


class CycleDetectedError(ExecutionGraphError):
    """Graph contains a cycle."""


class GraphBuildError(ExecutionGraphError):
    """Failed to build graph from input plans."""

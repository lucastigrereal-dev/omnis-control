"""Execution Graph Lite — DAG de passos com estados simulados + shadow mode."""

from src.execution_graph.models import ExecutionGraph, StepNode, StepStatus, ShadowConfig
from src.execution_graph.builder import build_graph
from src.execution_graph.validator import validate_graph
from src.execution_graph.errors import ExecutionGraphError, InvalidGraphError, CycleDetectedError
from src.execution_graph.shadow import run_shadow, promote_node, promote_all_nodes, ShadowRunResult
from src.execution_graph.runner import run_graph_dry

__all__ = [
    "ExecutionGraph",
    "StepNode",
    "StepStatus",
    "ShadowConfig",
    "build_graph",
    "validate_graph",
    "run_graph_dry",
    "run_shadow",
    "promote_node",
    "promote_all_nodes",
    "ShadowRunResult",
    "ExecutionGraphError",
    "InvalidGraphError",
    "CycleDetectedError",
]

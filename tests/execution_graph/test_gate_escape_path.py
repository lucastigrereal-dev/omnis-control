"""Guardrail test for approval gate escape paths in mission bridge."""
from __future__ import annotations

import pytest

from src.execution_graph.mission_bridge import run_graph_from_orchestrator
from src.mission_orchestrator.planner import build_plan


@pytest.mark.xfail(
    reason=(
        "Known gap: run_graph_from_orchestrator executa run_graph_dry direto, "
        "sem enforcement do approval_center gate."
    ),
    strict=False,
)
def test_run_graph_from_orchestrator_should_block_when_approval_required():
    run = build_plan(
        "criar crm pipeline de leads com follow-up para hotel",
        allow_unknown=True,
    )
    run.approval_required = True
    run.approval_id = None

    step_run = run_graph_from_orchestrator(run)

    assert step_run.status == "blocked_pending_approval"

"""Tests for mission_graph/nodes/ — each node tested in isolation."""
from __future__ import annotations

import pytest
from src.mission_graph.mission_state import initial_state
from src.mission_graph.nodes.validate_node import validate_node, route_after_validate
from src.mission_graph.nodes.execute_node import execute_node, route_after_execute
from src.mission_graph.nodes.checkpoint_node import checkpoint_node
from src.mission_graph.nodes.finalize_node import finalize_node


# ---------------------------------------------------------------------------
# validate_node
# ---------------------------------------------------------------------------

def test_validate_ok():
    state = initial_state("mission-123")
    result = validate_node(state)
    assert result["status"] == "running"
    assert result["current_step"] == 0


def test_validate_empty():
    state = initial_state("")
    result = validate_node(state)
    assert result["status"] == "failed"
    assert result.get("error") is not None
    assert result["error"]  # non-empty error message


# ---------------------------------------------------------------------------
# execute_node
# ---------------------------------------------------------------------------

def test_execute_increments_step():
    state = initial_state("mission-abc")
    state["current_step"] = 1
    result = execute_node(state)
    assert result["current_step"] == 2


# ---------------------------------------------------------------------------
# checkpoint_node
# ---------------------------------------------------------------------------

def test_checkpoint_sets_run_checkpoint_id():
    state = initial_state("mission-chk")
    result = checkpoint_node(state)
    assert "run_checkpoint_id" in result
    assert result["run_checkpoint_id"] is not None
    assert len(result["run_checkpoint_id"]) > 0


# ---------------------------------------------------------------------------
# finalize_node
# ---------------------------------------------------------------------------

def test_finalize_completed():
    state = initial_state("mission-fin")
    state["error"] = None
    result = finalize_node(state)
    assert result["status"] == "completed"


def test_finalize_failed():
    state = initial_state("mission-fail")
    state["error"] = "something went wrong"
    result = finalize_node(state)
    assert result["status"] == "failed"


# ---------------------------------------------------------------------------
# route_after_validate
# ---------------------------------------------------------------------------

def test_route_after_validate_ok():
    state = initial_state("mission-route")
    state["status"] = "running"
    assert route_after_validate(state) == "execute"


def test_route_after_validate_error():
    state = initial_state("mission-route-fail")
    state["error"] = "bad mission"
    assert route_after_validate(state) == "fail"


# ---------------------------------------------------------------------------
# route_after_execute
# ---------------------------------------------------------------------------

def test_route_after_execute_checkpoint():
    state = initial_state("mission-exec-route")
    state["current_step"] = 3  # >= 3 → checkpoint
    assert route_after_execute(state) == "checkpoint"


def test_route_after_execute_fail():
    state = initial_state("mission-exec-fail")
    state["error"] = "execution error"
    state["max_retries"] = 0  # exhausted retries
    assert route_after_execute(state) == "fail"

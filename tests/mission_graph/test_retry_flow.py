import pytest
from src.mission_graph.runner import run_mission_graph
from src.mission_graph.nodes.execute_node import execute_node as _execute_node


class TestRetryFlow:
    def test_run_requires_use_langgraph_true(self):
        with pytest.raises(NotImplementedError):
            run_mission_graph("m1", use_langgraph=False)

    def test_run_completes_with_langgraph_true(self):
        result = run_mission_graph("m1", use_langgraph=True)
        assert result["status"] in ("completed", "failed")
        assert result["mission_id"] == "m1"

    def test_run_empty_mission_id_fails(self):
        result = run_mission_graph("", use_langgraph=True)
        assert result["status"] == "failed"

    def test_execute_node_increments_step(self):
        from src.mission_graph.mission_state import initial_state
        s = initial_state("m1")
        s["status"] = "running"
        patch_result = _execute_node(s)
        assert patch_result["current_step"] == 1

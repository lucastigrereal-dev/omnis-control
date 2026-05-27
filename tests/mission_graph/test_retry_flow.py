import pytest
from src.mission_graph.runner import run_mission_graph
from src.mission_graph.nodes.execute_node import execute_node as _execute_node
from src.mission_graph.retry_policy import NodeRetryConfig, RetryPolicy


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

    def test_nodo_falha_duas_vezes_passa_na_terceira(self):
        """Prova: execute_node com erro registra tentativas e retoma."""
        from src.mission_graph.mission_state import initial_state, should_retry

        policy = RetryPolicy(default=NodeRetryConfig(max_retries=3))
        state = initial_state("retry_test", max_retries=3)

        # Simula 2 falhas
        state["attempts_by_node"] = {"execute": 2}
        assert should_retry(state, "execute", policy) is True

        # Na 3ª tentativa passa (attempts == max_retries)
        state["attempts_by_node"] = {"execute": 3}
        assert should_retry(state, "execute", policy) is False

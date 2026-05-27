from src.mission_graph.mission_state import (
    MissionGraphState, initial_state, should_retry, record_attempt
)


class TestInitialState:
    def test_initial_state_fields(self):
        s = initial_state("m1")
        assert s["mission_id"] == "m1"
        assert s["status"] == "draft"
        assert s["current_step"] == 0
        assert s["attempts_by_node"] == {}
        assert s["max_retries"] == 3
        assert s["events"] == []
        assert s["artifacts"] == []
        assert s["error"] is None
        assert s["run_checkpoint_id"] is None

    def test_custom_max_retries(self):
        s = initial_state("m2", max_retries=5)
        assert s["max_retries"] == 5

    def test_should_retry_within_limit(self):
        s = initial_state("m1", max_retries=3)
        s["attempts_by_node"] = {"execute": 1}
        assert should_retry(s, "execute") is True

    def test_should_retry_at_limit(self):
        s = initial_state("m1", max_retries=3)
        s["attempts_by_node"] = {"execute": 3}
        assert should_retry(s, "execute") is False

    def test_should_retry_new_node(self):
        s = initial_state("m1", max_retries=3)
        s["attempts_by_node"] = {}
        assert should_retry(s, "execute") is True

    def test_record_attempt_increments(self):
        s = initial_state("m1")
        s["attempts_by_node"] = {"execute": 2}
        patch = record_attempt(s, "execute")
        assert patch["attempts_by_node"]["execute"] == 3

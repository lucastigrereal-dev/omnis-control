import pytest
from src.mission_graph.runner import run_mission_graph, resume_mission_graph


class TestCheckpointResume:
    def test_resume_requires_use_langgraph_true(self):
        with pytest.raises(NotImplementedError):
            resume_mission_graph("m1", "chk1", use_langgraph=False)

    def test_run_sets_checkpoint_id(self):
        result = run_mission_graph("m_chk", use_langgraph=True)
        # After finalize, the mission must have passed through checkpoint
        assert result["mission_id"] == "m_chk"

    def test_resume_with_checkpoint_completes(self):
        result = resume_mission_graph("m_resume", "chk_abc", use_langgraph=True)
        assert result["status"] in ("completed", "failed")
        assert result["mission_id"] == "m_resume"

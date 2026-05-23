import json
import uuid

from src.utils import logger


def test_new_session_id_is_uuid():
    session_id = logger.new_session_id()

    assert str(uuid.UUID(session_id)) == session_id


def test_log_mission_writes_jsonl(tmp_path, monkeypatch):
    missions_file = tmp_path / "missions.jsonl"
    monkeypatch.setattr(logger, "_MISSIONS_FILE", str(missions_file))

    logger.log_mission(
        session_id="session-1",
        command="doctor",
        status="ok",
        duration_ms=12,
        summary="done",
        errors=["warning"],
    )

    record = json.loads(missions_file.read_text(encoding="utf-8").strip())
    assert record["session_id"] == "session-1"
    assert record["command"] == "doctor"
    assert record["errors"] == ["warning"]


def test_log_tool_run_writes_truncated_previews(tmp_path, monkeypatch):
    tool_runs_file = tmp_path / "tool_runs.jsonl"
    monkeypatch.setattr(logger, "_TOOL_RUNS_FILE", str(tool_runs_file))

    logger.log_tool_run(
        session_id="session-1",
        skill="demo",
        payload_file="payload.json",
        status="ok",
        stdout_preview="x" * 600,
        stderr_preview="y" * 600,
    )

    record = json.loads(tool_runs_file.read_text(encoding="utf-8").strip())
    assert record["session_id"] == "session-1"
    assert record["skill"] == "demo"
    assert len(record["stdout_preview"]) == 500
    assert len(record["stderr_preview"]) == 500

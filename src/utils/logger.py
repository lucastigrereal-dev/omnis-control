import json
import uuid
import time
import os
from datetime import datetime, timezone

_LOG_DIR = os.path.expanduser("~/omnis-control/logs")
_MISSIONS_FILE = os.path.join(_LOG_DIR, "missions.jsonl")
_TOOL_RUNS_FILE = os.path.join(_LOG_DIR, "tool_runs.jsonl")

os.makedirs(_LOG_DIR, exist_ok=True)


def new_session_id() -> str:
    return str(uuid.uuid4())


def _write_jsonl(filepath: str, record: dict) -> None:
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def log_mission(
    session_id: str,
    command: str,
    status: str,
    duration_ms: int,
    summary: str = "",
    errors: list | None = None,
) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": session_id,
        "command": command,
        "status": status,
        "duration_ms": duration_ms,
        "summary": summary,
        "errors": errors or [],
    }
    _write_jsonl(_MISSIONS_FILE, record)


def log_tool_run(
    session_id: str,
    skill: str,
    payload_file: str,
    status: str,
    stdout_preview: str = "",
    stderr_preview: str = "",
    duration_ms: int = 0,
    timeout_used: int = 60,
) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": session_id,
        "skill": skill,
        "payload_file": payload_file,
        "status": status,
        "stdout_preview": stdout_preview[:500],
        "stderr_preview": stderr_preview[:500],
        "duration_ms": duration_ms,
        "timeout_used": timeout_used,
    }
    _write_jsonl(_TOOL_RUNS_FILE, record)

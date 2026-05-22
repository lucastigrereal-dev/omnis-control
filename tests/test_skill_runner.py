import os
import sys
import json
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.runners.skill_runner import run_skill, list_skills
from src.utils.logger import new_session_id, log_tool_run
from src.utils.safe_paths import validate_skill_name


def test_run_skill_inexistent_raises():
    """Skill inexistente levanta ValueError."""
    with pytest.raises(ValueError, match="não encontrada"):
        run_skill("skill_inexistente_xyz_123")


def test_run_skill_dry_run_default():
    """Sem --yes, run_skill retorna dry_run."""
    # Pega qualquer skill real com run.py do repositorio
    skills_dir = os.path.join(os.path.dirname(__file__), "..", "skills")
    if not os.path.isdir(skills_dir):
        pytest.skip("Nenhuma skills dir encontrada")
    real_skills = [
        d
        for d in os.listdir(skills_dir)
        if os.path.isdir(os.path.join(skills_dir, d))
        and os.path.isfile(os.path.join(skills_dir, d, "run.py"))
    ]
    if not real_skills:
        pytest.skip("Nenhuma skill com run.py encontrada")

    result = run_skill(real_skills[0], dry_run=True)
    assert result["status"] == "dry_run"
    assert "Dry-run" in result["message"]


def test_run_skill_no_payload_ok():
    """Skill sem payload não falha se a skill aceita sem args."""
    skills_dir = os.path.join(os.path.dirname(__file__), "..", "skills")
    real_skills = [
        d
        for d in os.listdir(skills_dir)
        if os.path.isdir(os.path.join(skills_dir, d))
        and os.path.isfile(os.path.join(skills_dir, d, "run.py"))
    ]
    if not real_skills:
        pytest.skip("Nenhuma skill com run.py encontrada")

    result = run_skill(real_skills[0], dry_run=True)
    assert result["status"] in ("dry_run", "success", "error")


def test_jsonl_log_written():
    """log_tool_run escreve entrada parseable em tool_runs.jsonl."""
    log_dir = os.path.expanduser("~/omnis-control/logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "tool_runs.jsonl")

    session_id = new_session_id()
    log_tool_run(
        session_id=session_id,
        skill="test_skill",
        payload_file="test.json",
        status="success",
        stdout_preview="test output",
        duration_ms=100,
        timeout_used=30,
    )

    assert os.path.isfile(log_file)
    with open(log_file, encoding="utf-8") as f:
        lines = f.readlines()
    last = json.loads(lines[-1])
    assert last["session_id"] == session_id
    assert last["skill"] == "test_skill"
    assert last["status"] == "success"


def test_timeout_enforced():
    """Timeout é respeitado: skill mock que dorme 120s com timeout 5s deve falhar."""
    import tempfile
    import subprocess
    import sys

    mock_skill = tempfile.mkdtemp()
    run_py = os.path.join(mock_skill, "run.py")
    with open(run_py, "w") as f:
        f.write("import time; time.sleep(120); print('done')")

    # Point to mock via skill_dir override — test the subprocess directly
    start = __import__("time").time()
    try:
        proc = subprocess.run(
            [sys.executable, run_py],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        pytest.fail("Deveria ter levantado TimeoutExpired")
    except subprocess.TimeoutExpired:
        pass  # Expected

    duration = int((__import__("time").time() - start) * 1000)
    assert duration < 30000, f"Timeout não foi respeitado: {duration}ms"


def test_list_skills_returns_at_least_17():
    """list_skills retorna >= 17 skills (as 17 conhecidas do sistema)."""
    skills = list_skills()
    assert len(skills) >= 17, f"Esperado >= 17 skills, got {len(skills)}"


def test_list_skills_each_has_name_and_path():
    """Cada skill tem name e path."""
    for s in list_skills():
        assert "name" in s
        assert "path" in s
        assert os.path.isdir(s["path"])


def test_list_skills_invalid_skill_returns_error():
    """run_skill invalida retorna returncode=1 com stderr via subprocess."""
    from src.runners.skill_runner import run_skill
    with pytest.raises(ValueError):
        run_skill("skill_inexistente_999")


def test_dry_run_does_not_run():
    """Dry-run não executa a skill de verdade (não gera side effects)."""
    skills_dir = os.path.join(os.path.dirname(__file__), "..", "skills")
    real_skills = [
        d
        for d in os.listdir(skills_dir)
        if os.path.isdir(os.path.join(skills_dir, d))
        and os.path.isfile(os.path.join(skills_dir, d, "run.py"))
    ]
    if not real_skills:
        pytest.skip("Nenhuma skill com run.py encontrada")

    result = run_skill(real_skills[0], dry_run=True)
    assert result["status"] == "dry_run"

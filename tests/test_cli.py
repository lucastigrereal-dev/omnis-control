import os
import sys
import json
import tempfile
import subprocess

import pytest
import yaml

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.safe_paths import validate_write_path, validate_skill_name, safe_read_path
from src.checkers import skills_check
from src.checkers import disk_check
from src.reports import status_report


def test_paths_yaml_loads():
    """paths.yaml carrega sem erro."""
    path = os.path.expanduser("~/omnis-control/config/paths.yaml")
    assert os.path.isfile(path), f"paths.yaml não encontrado em {path}"
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data is not None
    assert "paths" in data
    assert "services" in data
    assert "_metadata" in data


def test_jarvis_py_exists():
    """jarvis.py shim existe e é executável."""
    path = os.path.expanduser("~/omnis-control/jarvis.py")
    assert os.path.isfile(path)


@pytest.mark.integration  # requer psutil funcional
def test_status_does_not_crash():
    """jarvis status não levanta exceção (usa paths reais)."""
    output = subprocess.run(
        [sys.executable, os.path.expanduser("~/omnis-control/jarvis.py"), "status"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert output.returncode == 0, f"stderr: {output.stderr[:500]}"


def test_skills_lists_categories():
    """skills retorna executable/doc_folder/doc_file."""
    result = skills_check.check()
    assert result["total"] >= 0
    assert isinstance(result["executable"], int)
    assert isinstance(result["doc_folder"], int)
    assert isinstance(result["doc_file"], int)
    assert isinstance(result["executable_list"], list)
    assert isinstance(result["doc_folder_list"], list)


def test_run_skill_inexistent_returns_clear_error():
    """run-skill com skill inexistente retorna erro claro."""
    output = subprocess.run(
        [
            sys.executable,
            os.path.expanduser("~/omnis-control/jarvis.py"),
            "run-skill",
            "skill_inexistente_xyz",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert output.returncode != 0, "Deveria falhar"
    assert "Erro" in output.stderr or "Erro" in output.stdout


def test_doctor_does_not_crash():
    """doctor roda sem crash (pode ter warnings, mas não exception)."""
    output = subprocess.run(
        [sys.executable, os.path.expanduser("~/omnis-control/jarvis.py"), "doctor"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert output.returncode == 0
    # Should output valid JSON
    try:
        data = json.loads(output.stdout)
        assert "session_id" in data
        assert "checks" in data
    except json.JSONDecodeError:
        pytest.fail("doctor output não é JSON válido")


def test_skills_command_does_not_crash():
    """skills command não quebra."""
    output = subprocess.run(
        [sys.executable, os.path.expanduser("~/omnis-control/jarvis.py"), "skills"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert output.returncode == 0

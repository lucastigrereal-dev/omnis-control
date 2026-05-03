"""
Testes da Fase 1.1 — artefatos obrigatórios da OMNIS.

Não quebra os 25 testes existentes.
"""

import os
import sys
import json
import subprocess

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

CONTROL_DIR = os.path.expanduser("~/jarvis-control")
PYTHON = sys.executable


def test_omnis_py_exists():
    """omnis.py existe na raiz do projeto."""
    path = os.path.join(CONTROL_DIR, "omnis.py")
    assert os.path.isfile(path), f"omnis.py não encontrado em {path}"


def test_omnis_status_works():
    """python omnis.py status funciona sem erro."""
    output = subprocess.run(
        [PYTHON, os.path.join(CONTROL_DIR, "omnis.py"), "status"],
        capture_output=True, text=True, timeout=30,
    )
    assert output.returncode == 0, f"stderr: {output.stderr[:500]}"


def test_pyproject_has_both_entry_points():
    """pyproject.toml declara omnis e jarvis."""
    path = os.path.join(CONTROL_DIR, "pyproject.toml")
    assert os.path.isfile(path)
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "omnis = \"src.cli:app\"" in content
    assert "jarvis = \"src.cli:app\"" in content


def test_video_pipeline_check_exists():
    """video_pipeline_check.py existe."""
    path = os.path.join(CONTROL_DIR, "src", "checkers", "video_pipeline_check.py")
    assert os.path.isfile(path), f"video_pipeline_check.py não encontrado"


def test_paths_yaml_has_video_pipeline():
    """paths.yaml contém seção video_pipeline."""
    path = os.path.join(CONTROL_DIR, "config", "paths.yaml")
    assert os.path.isfile(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data is not None
    assert "video_pipeline" in data, "Seção video_pipeline ausente do paths.yaml"
    vp = data["video_pipeline"]
    assert "local_search_roots" in vp
    assert "known_extensions" in vp
    assert "keywords" in vp


def test_video_pipeline_checker_structure():
    """checker retorna estrutura esperada."""
    from src.checkers import video_pipeline_check
    result = video_pipeline_check.check()
    assert "classification" in result
    assert result["classification"] in (
        "operational", "partial", "documented_only", "not_found", "scan_timeout_partial"
    )
    assert "confidence" in result
    assert result["confidence"] in ("high", "medium", "low")
    assert "signals" in result
    assert "counts" in result
    assert "evidence" in result
    assert isinstance(result["evidence"], list)
    assert "risks" in result
    assert isinstance(result["risks"], list)


def test_doctor_includes_video_pipeline():
    """doctor output inclui chave video_pipeline."""
    output = subprocess.run(
        [PYTHON, os.path.join(CONTROL_DIR, "omnis.py"), "doctor"],
        capture_output=True, text=True, timeout=60,
    )
    assert output.returncode == 0
    try:
        data = json.loads(output.stdout)
    except json.JSONDecodeError:
        pytest.fail("doctor output não é JSON válido")
    assert "video_pipeline" in data.get("checks", {})


def test_report_includes_video_pipeline():
    """report gera seção Video Pipeline."""
    output = subprocess.run(
        [PYTHON, os.path.join(CONTROL_DIR, "omnis.py"), "report"],
        capture_output=True, text=True, timeout=30,
    )
    assert output.returncode == 0
    report_path = os.path.join(CONTROL_DIR, "docs", "ESTADO_ATUAL_RESUMIDO.md")
    assert os.path.isfile(report_path)
    with open(report_path, encoding="utf-8") as f:
        content = f.read()
    assert "## 9. Video Pipeline" in content


def test_jarvis_status_still_works():
    """jarvis.py status continua funcionando."""
    output = subprocess.run(
        [PYTHON, os.path.join(CONTROL_DIR, "jarvis.py"), "status"],
        capture_output=True, text=True, timeout=30,
    )
    assert output.returncode == 0


def test_video_status_command_works():
    """omnis video-status funciona sem crash."""
    output = subprocess.run(
        [PYTHON, os.path.join(CONTROL_DIR, "omnis.py"), "video-status"],
        capture_output=True, text=True, timeout=60,
    )
    assert output.returncode == 0

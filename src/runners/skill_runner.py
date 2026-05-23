"""Skill runner — executa skills do projeto OMNIS.

SKILLS_PATH resolve para o diretório skills/ do projeto OMNIS.
Pode ser sobrescrito via env var OMNIS_SKILLS_PATH para uso em testes/CI.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from src.utils.safe_paths import resolve_skill_path, validate_skill_name

# PROJECT_ROOT = ~/omnis-control/ (3 levels up: src/runners/skill_runner.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# SKILLS_PATH com 3 fallbacks em ordem de prioridade:
#   1. env OMNIS_SKILLS_PATH (override explícito para testes)
#   2. <PROJECT_ROOT>/skills/ (caso normal)
#   3. ~/.claude/skills/ (legacy, retrocompat — DEPRECATED)
SKILLS_PATH = Path(
    os.getenv("OMNIS_SKILLS_PATH")
    or str(PROJECT_ROOT / "skills")
)


def list_skills() -> list[dict[str, str]]:
    """Lista skills com run.py disponiveis."""
    if not SKILLS_PATH.is_dir():
        return []
    skills = []
    for entry in sorted(SKILLS_PATH.iterdir()):
        if entry.is_dir() and (entry / "run.py").is_file():
            skills.append({"name": entry.name, "path": str(entry)})
    return skills


def run_skill(
    skill_name: str,
    payload_path: str | None = None,
    timeout: int = 60,
    dry_run: bool = True,
) -> dict[str, object]:
    """Run a skill by name with timeout and safety checks.

    Args:
        skill_name: Name of the skill directory under skills/
        payload_path: Optional path to JSON payload file
        timeout: Timeout in seconds (max 300)
        dry_run: If True, only validate and return dry-run info

    Returns:
        dict with status, stdout, stderr, duration_ms, etc.

    Raises:
        ValueError: If skill name is invalid or skill not found
        PermissionError: If path traversal detected
    """
    validate_skill_name(skill_name)

    run_py = _resolve_run_py(skill_name)
    timeout = max(1, min(timeout, 300))
    cmd = _build_command(run_py, payload_path)

    if dry_run:
        return _dry_run_result(skill_name, cmd)

    return _execute_command(skill_name, cmd, timeout)


def _resolve_run_py(skill_name: str) -> str:
    skill_dir = resolve_skill_path(skill_name)
    if not skill_dir:
        raise ValueError(f"Skill '{skill_name}' não encontrada em {SKILLS_PATH}")

    run_py = os.path.join(skill_dir, "run.py")
    if not os.path.isfile(run_py):
        raise ValueError(
            f"Skill '{skill_name}' não tem run.py executável. "
            f"Tipo: doc_folder ou doc_file (não executável)"
        )
    return run_py


def _build_command(run_py: str, payload_path: str | None) -> list[str]:
    cmd = [sys.executable, run_py]
    if payload_path:
        payload_abs = _validate_payload_path(payload_path)
        cmd.extend(["--payload", payload_abs])
    return cmd


def _validate_payload_path(payload_path: str) -> str:
    payload_abs = os.path.abspath(os.path.expanduser(payload_path))
    if not os.path.isfile(payload_abs):
        raise ValueError(f"Payload não encontrado: {payload_path}")
    try:
        with open(payload_abs, encoding="utf-8") as f:
            json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Payload JSON inválido: {e}")
    return payload_abs


def _dry_run_result(skill_name: str, cmd: list[str]) -> dict[str, object]:
    return {
        "status": "dry_run",
        "skill": skill_name,
        "command": " ".join(cmd),
        "message": "Dry-run: esta skill seria executada. Adicione --yes para executar de verdade.",
    }


def _execute_command(
    skill_name: str,
    cmd: list[str],
    timeout: int,
) -> dict[str, object]:
    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        duration_ms = int((time.time() - start) * 1000)
        status = "success" if proc.returncode == 0 else "error"
        return {
            "status": status,
            "skill": skill_name,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
            "duration_ms": duration_ms,
            "stdout_preview": proc.stdout[:500],
            "stderr_preview": proc.stderr[:500],
        }
    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start) * 1000)
        return {
            "status": "timeout",
            "skill": skill_name,
            "stdout": "",
            "stderr": f"Skill excedeu timeout de {timeout}s",
            "returncode": -1,
            "duration_ms": duration_ms,
            "stdout_preview": "",
            "stderr_preview": f"Skill excedeu timeout de {timeout}s",
        }

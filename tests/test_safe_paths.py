import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.safe_paths import (
    validate_write_path,
    validate_skill_name,
    resolve_skill_path,
    safe_read_path,
    CONTROL_DIR,
)


def test_path_traversal_blocked():
    """Path traversal com .. é bloqueado."""
    with pytest.raises(PermissionError):
        validate_write_path(os.path.join(CONTROL_DIR, "..", "etc", "passwd"))


def test_outside_write_blocked():
    """Escrita fora de ~/omnis-control/ é bloqueada."""
    with pytest.raises(PermissionError):
        validate_write_path(os.path.expanduser("~/.claude/skills"))


def test_valid_internal_path_ok():
    """Escrita dentro de ~/omnis-control/ é permitida."""
    path = validate_write_path(os.path.join(CONTROL_DIR, "logs", "test.jsonl"))
    assert path.startswith(CONTROL_DIR)


def test_skill_name_traversal_blocked():
    """Nome de skill com .. é bloqueado."""
    with pytest.raises(ValueError, match="inválido"):
        validate_skill_name("../etc/passwd")


def test_skill_name_slash_blocked():
    """Nome de skill com / é bloqueado."""
    with pytest.raises(ValueError):
        validate_skill_name("some/path")


def test_skill_name_clean_allowed():
    """Nome de skill limpo é permitido."""
    name = validate_skill_name("jarvis-router")
    assert name == "jarvis-router"


def test_skill_name_with_hyphen_underscore_allowed():
    """Nome com hífen e underscore é permitido."""
    name = validate_skill_name("content-machine_v2")
    assert name == "content-machine_v2"


def test_env_not_read():
    """Confirma que .env não é lido — verifica que não há leitura de .env no safe_paths."""
    # safe_paths.py não importa dotenv nem lê arquivos .env
    with open(os.path.join(CONTROL_DIR, "src", "utils", "safe_paths.py"), encoding="utf-8") as f:
        content = f.read()
    assert "dotenv" not in content
    assert ".env" not in content


def test_resolve_skill_inexistent():
    """resolve_skill_path retorna None para skill inexistente."""
    result = resolve_skill_path("skill_inexistente_xyz")
    assert result is None


def test_resolve_skill_real():
    """resolve_skill_path encontra skill real se existir."""
    skills_dir = os.path.expanduser("~/.claude/skills")
    real = [
        d
        for d in os.listdir(skills_dir)
        if os.path.isdir(os.path.join(skills_dir, d))
    ]
    if not real:
        pytest.skip("Nenhuma skill encontrada")
    result = resolve_skill_path(real[0])
    assert result is not None
    assert os.path.isdir(result)


def test_safe_read_outside_blocked():
    """safe_read_path bloqueia caminhos fora dos prefixos permitidos."""
    with pytest.raises(PermissionError):
        safe_read_path("C:/Windows/System32")


def test_safe_read_control_dir_ok():
    """safe_read_path permite ~/omnis-control/."""
    path = safe_read_path(CONTROL_DIR)
    assert os.path.isdir(path)

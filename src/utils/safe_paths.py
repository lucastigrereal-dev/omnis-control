import os
import sys


CONTROL_DIR = os.path.normpath(os.path.expanduser("~/jarvis-control"))


def validate_write_path(path: str) -> str:
    """Validate that path is inside ~/jarvis-control/ and has no traversal.

    Returns the normalized absolute path.
    Raises PermissionError if the path violates rules.
    """
    expanded = os.path.normpath(os.path.expanduser(path))
    abs_path = os.path.abspath(expanded)

    if not abs_path.startswith(CONTROL_DIR + os.sep) and abs_path != CONTROL_DIR:
        raise PermissionError(
            f"Escrita bloqueada: {abs_path} não está dentro de {CONTROL_DIR}"
        )

    if os.path.islink(abs_path):
        real = os.path.realpath(abs_path)
        if not real.startswith(CONTROL_DIR + os.sep) and real != CONTROL_DIR:
            raise PermissionError(
                f"Escrita bloqueada: symlink {abs_path} aponta para fora ({real})"
            )

    return abs_path


def validate_skill_name(name: str) -> str:
    """Validate skill name blocks path traversal characters.

    Returns the cleaned name (alphanumeric, hyphens, underscores only).
    Raises ValueError if the name contains path traversal patterns.
    """
    if not name or not name.strip():
        raise ValueError("Nome da skill não pode ser vazio")

    blocked = {"..", "/", "\\", "~", ":"}
    for ch in blocked:
        if ch in name:
            raise ValueError(f"Nome de skill inválido: contém '{ch}'")

    allowed = all(c.isalnum() or c in ("-", "_") for c in name)
    if not allowed:
        raise ValueError(
            "Nome de skill deve conter apenas letras, números, hífens e underscores"
        )

    return name.strip()


def resolve_skill_path(name: str) -> str | None:
    """Resolve skill name to its directory path.

    Checks ~/.claude/skills/<name>/run.py and ~/.claude/skills/<name>/.
    Returns the directory path if found, None otherwise.
    """
    safe = validate_skill_name(name)
    skills_dir = os.path.expanduser("~/.claude/skills")
    candidate = os.path.join(skills_dir, safe)

    if not os.path.isdir(candidate):
        return None

    return candidate


def safe_read_path(path: str) -> str:
    """Validate a path for reading: must be in known ecosystem paths.

    Returns the normalized absolute path.
    Raises PermissionError if the path is not allowed.
    """
    expanded = os.path.normpath(os.path.expanduser(path))
    abs_path = os.path.abspath(expanded)

    allowed_prefixes = [
        CONTROL_DIR,
        os.path.normpath(os.path.expanduser("~/.claude")),
        os.path.normpath(os.path.expanduser("~/publisher-os")),
        os.path.normpath(os.path.expanduser("~/JARVIS_OS")),
    ]

    allowed = any(abs_path.startswith(p + os.sep) or abs_path == p for p in allowed_prefixes)
    if not allowed:
        raise PermissionError(
            f"Leitura bloqueada: {abs_path} não está em caminho permitido"
        )

    return abs_path

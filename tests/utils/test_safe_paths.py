from pathlib import Path

import pytest

from src.utils import safe_paths


def test_validate_write_path_allows_control_dir_child():
    target = Path(safe_paths.CONTROL_DIR) / "logs" / "missions.jsonl"
    expected = safe_paths.os.path.abspath(safe_paths.os.path.normpath(str(target)))

    assert safe_paths.validate_write_path(str(target)) == expected


def test_validate_write_path_blocks_outside(tmp_path):
    with pytest.raises(PermissionError):
        safe_paths.validate_write_path(str(tmp_path / "outside.txt"))


def test_validate_skill_name_accepts_simple_names():
    assert safe_paths.validate_skill_name("jarvis-router_1") == "jarvis-router_1"


@pytest.mark.parametrize(
    "name",
    ["", "../x", "bad/name", "bad\\name", "~bad", "bad:name", "bad name"],
)
def test_validate_skill_name_blocks_unsafe_names(name):
    with pytest.raises(ValueError):
        safe_paths.validate_skill_name(name)


def test_resolve_skill_path_uses_env_root(tmp_path, monkeypatch):
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "demo-skill"
    skill_dir.mkdir(parents=True)
    monkeypatch.setenv("OMNIS_SKILLS_PATH", str(skills_root))

    assert safe_paths.resolve_skill_path("demo-skill") == str(skill_dir)


def test_safe_read_path_blocks_outside(tmp_path):
    with pytest.raises(PermissionError):
        safe_paths.safe_read_path(str(tmp_path / "outside.txt"))

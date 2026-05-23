import json
from pathlib import Path

import pytest

from src.runners import skill_runner


def test_list_skills_returns_executable_skill_dirs(tmp_path, monkeypatch):
    skills_root = tmp_path / "skills"
    runnable = skills_root / "runnable"
    docs_only = skills_root / "docs-only"
    runnable.mkdir(parents=True)
    docs_only.mkdir()
    (runnable / "run.py").write_text("print('ok')", encoding="utf-8")
    (docs_only / "SKILL.md").write_text("# docs", encoding="utf-8")
    monkeypatch.setattr(skill_runner, "SKILLS_PATH", skills_root)

    result = skill_runner.list_skills()

    assert result == [{"name": "runnable", "path": str(runnable)}]


def test_run_skill_dry_run_validates_payload(tmp_path, monkeypatch):
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "run.py").write_text("print('ok')", encoding="utf-8")
    payload = tmp_path / "payload.json"
    payload.write_text(json.dumps({"ok": True}), encoding="utf-8")
    monkeypatch.setenv("OMNIS_SKILLS_PATH", str(skills_root))
    monkeypatch.setattr(skill_runner, "SKILLS_PATH", skills_root)

    result = skill_runner.run_skill("demo", str(payload), dry_run=True)

    assert result["status"] == "dry_run"
    assert result["skill"] == "demo"
    assert str(payload) in result["command"]


def test_run_skill_rejects_invalid_payload(tmp_path, monkeypatch):
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "run.py").write_text("print('ok')", encoding="utf-8")
    payload = tmp_path / "payload.json"
    payload.write_text("{bad json", encoding="utf-8")
    monkeypatch.setenv("OMNIS_SKILLS_PATH", str(skills_root))
    monkeypatch.setattr(skill_runner, "SKILLS_PATH", skills_root)

    with pytest.raises(ValueError, match="Payload JSON inválido"):
        skill_runner.run_skill("demo", str(payload), dry_run=True)


def test_run_skill_executes_run_py_when_not_dry_run(tmp_path, monkeypatch):
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "run.py").write_text(
        "print('hello from skill')",
        encoding="utf-8",
    )
    monkeypatch.setenv("OMNIS_SKILLS_PATH", str(skills_root))
    monkeypatch.setattr(skill_runner, "SKILLS_PATH", skills_root)

    result = skill_runner.run_skill("demo", dry_run=False)

    assert result["status"] == "success"
    assert result["skill"] == "demo"
    assert result["returncode"] == 0
    assert "hello from skill" in result["stdout"]
    assert "hello from skill" in result["stdout_preview"]


def test_run_skill_returns_timeout_status(tmp_path, monkeypatch):
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "run.py").write_text(
        "import time\ntime.sleep(2)",
        encoding="utf-8",
    )
    monkeypatch.setenv("OMNIS_SKILLS_PATH", str(skills_root))
    monkeypatch.setattr(skill_runner, "SKILLS_PATH", skills_root)

    result = skill_runner.run_skill("demo", timeout=1, dry_run=False)

    assert result["status"] == "timeout"
    assert result["skill"] == "demo"
    assert result["returncode"] == -1
    assert "timeout de 1s" in result["stderr"]

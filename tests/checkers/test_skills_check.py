"""Tests for skills_check checker."""
from __future__ import annotations

import pytest
import os
import yaml


class TestSkillsCheck:
    def test_check_returns_dict_with_expected_keys(self, monkeypatch, tmp_path):
        """Skills check returns dict with expected structure."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "my-skill").mkdir()

        registry_file = tmp_path / "skills.yaml"
        registry_file.write_text("skills: []")

        monkeypatch.setattr("src.checkers.skills_check.SKILLS_DIR", str(skills_dir))
        monkeypatch.setattr("src.checkers.skills_check.REGISTRY_FILE", str(registry_file))

        from src.checkers.skills_check import check

        result = check()
        assert "total" in result
        assert "executable" in result
        assert "doc_folder" in result
        assert "doc_file" in result
        assert "orphan_skills" in result
        assert "registry_missing_from_disk" in result
        assert "registry_available" in result

    def test_check_empty_when_no_skills_dir(self, monkeypatch):
        monkeypatch.setattr("src.checkers.skills_check.SKILLS_DIR", "/nonexistent/path")
        monkeypatch.setattr("src.checkers.skills_check.REGISTRY_FILE", "/nonexistent/registry.yaml")

        from src.checkers.skills_check import check

        result = check()
        assert result["total"] == 0
        assert result["registry_available"] is False

    def test_check_counts_executable_skills(self, monkeypatch, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        exec_skill = skills_dir / "exec-skill"
        exec_skill.mkdir()
        (exec_skill / "run.py").write_text("print('hello')")
        (exec_skill / "SKILL.md").write_text("# Skill")

        registry_file = tmp_path / "skills.yaml"
        registry_file.write_text("skills: [{name: exec-skill}]")

        monkeypatch.setattr("src.checkers.skills_check.SKILLS_DIR", str(skills_dir))
        monkeypatch.setattr("src.checkers.skills_check.REGISTRY_FILE", str(registry_file))

        from src.checkers.skills_check import check

        result = check()
        assert result["total"] == 1
        assert result["executable"] == 1
        assert "exec-skill" in result["executable_list"]

    def test_check_detects_orphans(self, monkeypatch, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "orphan-skill").mkdir()

        registry_file = tmp_path / "skills.yaml"
        registry_file.write_text("skills: [{name: registered-skill}]")

        monkeypatch.setattr("src.checkers.skills_check.SKILLS_DIR", str(skills_dir))
        monkeypatch.setattr("src.checkers.skills_check.REGISTRY_FILE", str(registry_file))

        from src.checkers.skills_check import check

        result = check()
        assert "orphan-skill" in result["orphan_skills"]
        assert "registered-skill" in result["registry_missing_from_disk"]

    def test_check_doc_file_skills(self, monkeypatch, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "doc-skill.md").write_text("# Doc skill")

        registry_file = tmp_path / "skills.yaml"
        registry_file.write_text("skills: []")

        monkeypatch.setattr("src.checkers.skills_check.SKILLS_DIR", str(skills_dir))
        monkeypatch.setattr("src.checkers.skills_check.REGISTRY_FILE", str(registry_file))

        from src.checkers.skills_check import check

        result = check()
        assert result["total"] == 1
        assert result["doc_file"] == 1
        assert "doc-skill" in result["doc_file_list"]

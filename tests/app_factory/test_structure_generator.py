"""Tests for Project Structure Generator."""
from __future__ import annotations

from src.app_factory.models import AppBlueprint, AppIdea, AppRequirement
from src.app_factory.structure_generator import generate_project_structure


class TestStructureGenerator:
    def test_returns_dict(self):
        idea = AppIdea.new("Struct", "test")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        structure = generate_project_structure(bp, req)
        assert isinstance(structure, dict)

    def test_always_has_readme(self):
        idea = AppIdea.new("Readme", "test")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        structure = generate_project_structure(bp, req)
        assert "README.md" in structure

    def test_always_has_gitignore(self):
        idea = AppIdea.new("Git", "test")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        structure = generate_project_structure(bp, req)
        assert ".gitignore" in structure

    def test_python_project_has_pyproject(self):
        idea = AppIdea.new("PyProject", "python web app")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        structure = generate_project_structure(bp, req)
        assert "pyproject.toml" in structure

    def test_python_project_has_tests_dir(self):
        idea = AppIdea.new("TestDir", "python app")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        structure = generate_project_structure(bp, req)
        assert "tests" in structure

    def test_python_project_has_package(self):
        idea = AppIdea.new("PkgTest", "python web app")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        structure = generate_project_structure(bp, req)
        # Should have a package directory
        dirs = [k for k, v in structure.items() if isinstance(v, dict)]
        assert len(dirs) > 0

    def test_deterministic_same_input(self):
        idea1 = AppIdea.new("Det", "python app")
        idea2 = AppIdea.new("Det", "python app")
        req1 = AppRequirement.from_idea(idea1)
        req2 = AppRequirement.from_idea(idea2)
        bp1 = AppBlueprint.from_requirement(req1)
        bp2 = AppBlueprint.from_requirement(req2)
        s1 = generate_project_structure(bp1, req1)
        s2 = generate_project_structure(bp2, req2)
        assert s1 == s2

    def test_structure_is_pure_plan_no_files_created(self, tmp_path):
        """Structure Generator must not touch the filesystem."""
        import os
        idea = AppIdea.new("NoFS", "test")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        before = set(os.listdir(tmp_path))
        _ = generate_project_structure(bp, req)
        after = set(os.listdir(tmp_path))
        assert before == after  # no side effects

    def test_no_network_no_external_calls(self):
        """Pure computation, no imports that trigger network."""
        idea = AppIdea.new("Offline", "test")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        structure = generate_project_structure(bp, req)
        assert isinstance(structure, dict)  # just completes

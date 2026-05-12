"""Tests for AppFactoryPlanner — deterministic pipeline."""
from __future__ import annotations

import pytest

from src.app_factory.errors import InvalidAppIdeaError, PlannerError
from src.app_factory.models import (
    AppIdea,
    STATUS_GENERATED,
    STATUS_PLANNED,
)
from src.app_factory.planner import AppFactoryPlanner


class TestAppFactoryPlanner:
    def test_plan_dry_run_returns_artifact(self):
        planner = AppFactoryPlanner()
        idea = AppIdea.new("Test App", "A test application for planning")
        artifact = planner.plan(idea, dry_run=True)
        assert artifact.artifact_id.startswith("art_")
        assert len(artifact.prd_markdown) > 0
        assert "# PRD: Test App" in artifact.prd_markdown
        assert idea.status == STATUS_PLANNED

    def test_plan_dry_run_sets_status_planned(self):
        planner = AppFactoryPlanner()
        idea = AppIdea.new("Status Check", "check planned status")
        planner.plan(idea, dry_run=True)
        assert idea.status == STATUS_PLANNED

    def test_plan_non_dry_run_sets_status_generated(self, tmp_path):
        log = tmp_path / "plans.jsonl"
        planner = AppFactoryPlanner(log_path=log)
        idea = AppIdea.new("Persist App", "this should persist")
        planner.plan(idea, dry_run=False)
        assert idea.status == STATUS_GENERATED
        assert log.exists()

    def test_plan_non_dry_run_writes_log(self, tmp_path):
        log = tmp_path / "plans.jsonl"
        planner = AppFactoryPlanner(log_path=log)
        idea = AppIdea.new("Logged App", "should write a log line")
        planner.plan(idea, dry_run=False)
        assert log.exists()
        content = log.read_text(encoding="utf-8")
        assert idea.idea_id in content

    def test_plan_invalid_idea_raises(self):
        planner = AppFactoryPlanner()
        idea = AppIdea.new("", "")  # no title, no description
        with pytest.raises(InvalidAppIdeaError):
            planner.plan(idea, dry_run=True)

    def test_plan_batch_returns_all_artifacts(self):
        planner = AppFactoryPlanner()
        ideas = [
            AppIdea.new("App A", "First app"),
            AppIdea.new("App B", "Second app"),
            AppIdea.new("App C", "Third app"),
        ]
        artifacts = planner.plan_batch(ideas, dry_run=True)
        assert len(artifacts) == 3

    def test_plan_batch_stops_on_invalid(self):
        planner = AppFactoryPlanner()
        ideas = [
            AppIdea.new("Good", "Valid app"),
            AppIdea.new("", ""),  # invalid — will raise
            AppIdea.new("Never", "Should not reach this"),
        ]
        with pytest.raises(InvalidAppIdeaError):
            planner.plan_batch(ideas, dry_run=True)

    def test_get_history_tracks_generated(self):
        planner = AppFactoryPlanner()
        idea = AppIdea.new("Historic", "track this")
        planner.plan(idea, dry_run=True)
        hist = planner.get_history()
        assert len(hist) >= 1

    def test_load_history_from_empty_log(self, tmp_path):
        log = tmp_path / "nonexistent.jsonl"
        planner = AppFactoryPlanner(log_path=log)
        items = planner.load_history()
        assert items == []

    def test_load_history_reads_existing(self, tmp_path):
        log = tmp_path / "plans.jsonl"
        planner = AppFactoryPlanner(log_path=log)
        idea = AppIdea.new("Historic", "persist this")
        planner.plan(idea, dry_run=False)
        items = planner.load_history()
        assert len(items) >= 1

    def test_prd_contains_blueprint_id(self):
        planner = AppFactoryPlanner()
        idea = AppIdea.new("Full Stack", "complete web app with auth and dashboard")
        artifact = planner.plan(idea, dry_run=True)
        assert artifact.blueprint_id in artifact.prd_markdown

    def test_prd_contains_all_sections(self):
        planner = AppFactoryPlanner()
        idea = AppIdea.new("Sectioned", "app that deserves a full PRD")
        artifact = planner.plan(idea, dry_run=True)
        md = artifact.prd_markdown
        assert "## 1. Overview" in md
        assert "## 2. Features" in md
        assert "## 3. Requirements" in md
        assert "## 4. Domain Model" in md
        assert "## 5. Architecture" in md

    def test_project_structure_is_dict(self):
        planner = AppFactoryPlanner()
        idea = AppIdea.new("Structured", "python app")
        artifact = planner.plan(idea, dry_run=True)
        assert isinstance(artifact.project_structure, dict)
        assert len(artifact.project_structure) > 0


class TestPlannerDeterminism:
    """Planner must produce identical output for identical input."""

    def test_same_input_same_prd(self):
        p1 = AppFactoryPlanner()
        p2 = AppFactoryPlanner()
        idea1 = AppIdea.new("Same", "identical description with auth", features=["login", "dashboard"])
        idea2 = AppIdea.new("Same", "identical description with auth", features=["login", "dashboard"])
        art1 = p1.plan(idea1, dry_run=True)
        art2 = p2.plan(idea2, dry_run=True)
        # Markdown content should be identical (timestamps will differ, skip header)
        body1 = art1.prd_markdown.split("---", 1)[-1] if "---" in art1.prd_markdown else art1.prd_markdown
        body2 = art2.prd_markdown.split("---", 1)[-1] if "---" in art2.prd_markdown else art2.prd_markdown
        assert body1 == body2

    def test_same_input_same_structure(self):
        p1 = AppFactoryPlanner()
        p2 = AppFactoryPlanner()
        idea1 = AppIdea.new("Struct", "app with entities")
        idea2 = AppIdea.new("Struct", "app with entities")
        art1 = p1.plan(idea1, dry_run=True)
        art2 = p2.plan(idea2, dry_run=True)
        assert art1.project_structure == art2.project_structure

    def test_same_input_same_tech_stack(self):
        p1 = AppFactoryPlanner()
        p2 = AppFactoryPlanner()
        idea1 = AppIdea.new("Tech", "web app")
        idea2 = AppIdea.new("Tech", "web app")
        art1 = p1.plan(idea1, dry_run=True)
        art2 = p2.plan(idea2, dry_run=True)
        assert art1.tech_stack_summary == art2.tech_stack_summary

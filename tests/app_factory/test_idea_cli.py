"""Tests for Idea CLI: omnis idea new | list | show."""
from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.app_factory.idea_cli import idea_app
from src.app_factory.idea_store import IdeaStore


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_dir(app_factory_tmp_dir: Path):
    return app_factory_tmp_dir


class TestIdeaCLI:
    def test_idea_new_with_required_args(self, runner, temp_dir):
        result = runner.invoke(idea_app, [
            "new", "--title", "My App", "--description", "Does things",
        ])
        assert result.exit_code == 0
        assert "Dry-run" in result.stdout or "dry-run" in result.stdout.lower()

    def test_idea_new_without_title_fails(self, runner):
        result = runner.invoke(idea_app, [
            "new", "--description", "No title here",
        ])
        assert result.exit_code != 0

    def test_idea_list_shows_ideas(self, runner, temp_dir):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        from src.app_factory.models import AppIdea
        idea = AppIdea.new(title="Listed", description="An idea")
        store.save(idea)

        import src.app_factory.idea_cli as cli_mod
        original = cli_mod.IdeaStore
        cli_mod.IdeaStore = lambda dry_run=True: store

        try:
            result = runner.invoke(idea_app, ["list"])
            assert result.exit_code == 0
            assert "Listed" in result.stdout
        finally:
            cli_mod.IdeaStore = original

    def test_idea_list_empty(self, runner):
        result = runner.invoke(idea_app, ["list"])
        assert result.exit_code == 0

    def test_idea_show_found(self, runner, temp_dir):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        from src.app_factory.models import AppIdea
        idea = AppIdea.new(title="Shown", description="Visible idea", domain="test")
        store.save(idea)

        import src.app_factory.idea_cli as cli_mod
        original = cli_mod.IdeaStore
        cli_mod.IdeaStore = lambda dry_run=True: store

        try:
            result = runner.invoke(idea_app, ["show", idea.idea_id])
            assert result.exit_code == 0
            assert "Shown" in result.stdout
            assert "test" in result.stdout
        finally:
            cli_mod.IdeaStore = original

    def test_idea_show_not_found(self, runner):
        result = runner.invoke(idea_app, ["show", "nonexist"])
        assert result.exit_code != 0

    def test_idea_plan_generates_prd(self, runner, temp_dir):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        from src.app_factory.models import AppIdea
        idea = AppIdea.new(title="Planned", description="Generate PRD")
        store.save(idea)

        import src.app_factory.idea_cli as cli_mod
        original = cli_mod.IdeaStore
        cli_mod.IdeaStore = lambda dry_run=True: store

        try:
            result = runner.invoke(idea_app, ["plan", idea.idea_id])
            assert result.exit_code == 0
            assert "PRD gerado" in result.stdout
        finally:
            cli_mod.IdeaStore = original

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


class TestIdeaCLISafety:
    def test_safety_audit_dir(self, runner, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("print('hello')")
        result = runner.invoke(idea_app, ["safety", "--dir", str(tmp_path)])
        assert result.exit_code == 0

    def test_safety_check_safe_command(self, runner):
        result = runner.invoke(idea_app, ["safety", "--check-cmd", "python -m pytest tests/"])
        assert result.exit_code == 0

    def test_safety_check_blocked_command(self, runner):
        result = runner.invoke(idea_app, ["safety", "--check-cmd", "rm -rf /tmp"])
        assert result.exit_code != 0

    def test_safety_audit_detects_env(self, runner, tmp_path):
        (tmp_path / ".env").write_text("SECRET=x")
        result = runner.invoke(idea_app, ["safety", "--dir", str(tmp_path)])
        assert result.exit_code != 0


class TestIdeaCLIQuality:
    def test_quality_score(self, runner, temp_dir):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        from src.app_factory.models import AppIdea
        idea = AppIdea.new(title="Quality Test", description="Testing quality scoring system")
        store.save(idea)

        import src.app_factory.idea_cli as cli_mod
        original = cli_mod.IdeaStore
        cli_mod.IdeaStore = lambda dry_run=True: store

        try:
            result = runner.invoke(idea_app, ["quality", idea.idea_id])
            assert result.exit_code == 0
            assert "Quality Score" in result.stdout
        finally:
            cli_mod.IdeaStore = original


class TestIdeaCLIDiff:
    def test_diff_two_ideas(self, runner, temp_dir):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        from src.app_factory.models import AppIdea
        idea1 = AppIdea.new(title="App Alpha", description="First app", features=["auth"])
        idea2 = AppIdea.new(title="App Beta", description="Second app", features=["auth", "search"])
        store.save(idea1)
        store.save(idea2)

        import src.app_factory.idea_cli as cli_mod
        original = cli_mod.IdeaStore
        cli_mod.IdeaStore = lambda dry_run=True: store

        try:
            result = runner.invoke(idea_app, ["diff", idea1.idea_id, idea2.idea_id])
            assert result.exit_code == 0
        finally:
            cli_mod.IdeaStore = original

    def test_diff_same_idea(self, runner, temp_dir):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        from src.app_factory.models import AppIdea
        idea = AppIdea.new(title="Solo", description="One app")
        store.save(idea)

        import src.app_factory.idea_cli as cli_mod
        original = cli_mod.IdeaStore
        cli_mod.IdeaStore = lambda dry_run=True: store

        try:
            result = runner.invoke(idea_app, ["diff", idea.idea_id, idea.idea_id])
            assert result.exit_code == 0
        finally:
            cli_mod.IdeaStore = original


class TestIdeaCLIRecovery:
    def test_recovery_plan(self, runner):
        result = runner.invoke(idea_app, ["recovery", "idea_test_recovery"])
        assert result.exit_code == 0
        assert "Recovery Plan" in result.stdout or "Recovery" in result.stdout

    def test_recovery_with_force(self, runner):
        result = runner.invoke(idea_app, ["recovery", "idea_test", "--force"])
        assert result.exit_code == 0


class TestIdeaCLIStatus:
    def test_status_list(self, runner):
        result = runner.invoke(idea_app, ["status"])
        assert result.exit_code == 0

    def test_status_summary(self, runner):
        result = runner.invoke(idea_app, ["status", "--summary"])
        assert result.exit_code == 0

    def test_status_nonexistent_idea(self, runner):
        result = runner.invoke(idea_app, ["status", "--idea-id", "nonexistent_xyz"])
        assert result.exit_code != 0

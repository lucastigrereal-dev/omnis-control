"""E2E tests for idea intake pipeline: CLI -> Store -> Verify."""
from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.app_factory.idea_cli import idea_app
from src.app_factory.idea_store import IdeaStore
from src.app_factory.models import AppIdea


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_dir(app_factory_tmp_dir: Path):
    return app_factory_tmp_dir


class TestIdeaIntakeE2E:
    def test_cli_new_then_list_same_data(self, runner, temp_dir):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        import src.app_factory.idea_cli as cli_mod
        original = cli_mod.IdeaStore

        cli_mod.IdeaStore = lambda dry_run=True: store
        try:
            result = runner.invoke(idea_app, [
                "new", "--title", "E2E App", "--description", "End to end test",
                "--domain", "e2e", "--target-audience", "devs",
                "--features", "a,b,c", "--apply",
            ])
            assert result.exit_code == 0

            result2 = runner.invoke(idea_app, ["list"])
            assert result2.exit_code == 0
            assert "E2E App" in result2.stdout
        finally:
            cli_mod.IdeaStore = original

    def test_cli_new_invalid_shows_error(self, runner):
        result = runner.invoke(idea_app, [
            "new", "--title", "", "--description", "", "--apply",
        ])
        assert result.exit_code != 0

    def test_duplicate_title_same_description_still_saves(self, temp_dir):
        idea1 = AppIdea.new(title="Dup", description="Same")
        idea2 = AppIdea.new(title="Dup", description="Same")
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        store.save(idea1)
        store.save(idea2)
        assert idea1.idea_id != idea2.idea_id
        assert len(store.list_all()) == 2

    def test_round_trip_jsonl_integrity(self, temp_dir):
        idea = AppIdea.new(
            title="Cafe com Acucar",
            description="Unicode test - espanhol e portugues",
            domain="unicode",
            features=["login", "busca"],
            constraints=["offline-first"],
        )
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        store.save(idea)
        found = store.get(idea.idea_id)
        assert found is not None
        assert found.title == idea.title
        assert found.description == idea.description
        assert found.features == idea.features
        assert found.constraints == idea.constraints

    def test_deterministic_shape_for_same_input(self):
        idea1 = AppIdea.new(
            title="Deterministic", description="Same inputs",
            domain="test", features=["x"], constraints=["y"],
            target_audience="anyone",
        )
        idea2 = AppIdea.new(
            title="Deterministic", description="Same inputs",
            domain="test", features=["x"], constraints=["y"],
            target_audience="anyone",
        )
        assert idea1.idea_id != idea2.idea_id
        assert idea1.title == idea2.title
        assert idea1.to_dict().keys() == idea2.to_dict().keys()

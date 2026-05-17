"""Tests for App Factory planning waves W133-W142."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.app_factory.api_contract import build_api_contract
from src.app_factory.artifact_registry import ArtifactRegistry, ArtifactRegistryEntry
from src.app_factory.bundle_exporter import build_bundle
from src.app_factory.docs_generator import build_generated_docs
from src.app_factory.idea_cli import idea_app
from src.app_factory.idea_store import IdeaStore
from src.app_factory.models import AppBlueprint, AppIdea, AppRequirement
from src.app_factory.pipeline import build_planning_pipeline
from src.app_factory.prd_service import StoredIdeaPRDGenerator
from src.app_factory.quality_gate import validate_bundle
from src.app_factory.schema_planner import build_schema_plan
from src.app_factory.scaffold_engine import run_scaffold
from src.app_factory.scaffold_plan import ScaffoldFilePlan, ScaffoldPlan, build_scaffold_plan
from src.app_factory.task_plan import build_task_plan


@pytest.fixture
def idea() -> AppIdea:
    return AppIdea.new(
        title="Client Portal",
        description="Portal with login, customer records, reports and search",
        target_audience="operators",
        features=["login", "manage customer", "reports", "search"],
        constraints=["dry-run only"],
        domain="operations",
    )


@pytest.fixture
def blueprint(idea: AppIdea) -> AppBlueprint:
    return AppBlueprint.from_requirement(AppRequirement.from_idea(idea))


def test_w133_schema_infers_fk_indexes_and_json_fallback(blueprint: AppBlueprint):
    blueprint.data_models.append({
        "name": "Audit",
        "table": "audits",
        "fields": [
            {"name": "id", "type": "UUID", "pk": True},
            {"name": "user_id", "type": "UUID", "nullable": False},
            {"name": "payload", "type": "dict"},
        ],
    })
    plan = build_schema_plan(blueprint)
    audit = next(table for table in plan.tables if table.name == "audits")
    assert any(rel["field"] == "user_id" for rel in audit.relationships)
    assert any(index["fields"] == ["user_id"] for index in audit.indexes)
    assert next(field for field in audit.fields if field.name == "payload").type == "jsonb"


def test_w134_api_contract_has_shapes_auth_notes(blueprint: AppBlueprint):
    schema = build_schema_plan(blueprint)
    contract = build_api_contract(blueprint, schema)
    assert contract.endpoints
    assert any(endpoint.request for endpoint in contract.endpoints)
    assert any(endpoint.response for endpoint in contract.endpoints)


def test_w135_task_plan_orders_data_backend_frontend_qa(blueprint: AppBlueprint):
    schema = build_schema_plan(blueprint)
    api = build_api_contract(blueprint, schema)
    plan = build_task_plan(blueprint, schema, api)
    areas = [task.area for task in plan.tasks]
    assert "data" in areas
    assert "backend" in areas
    assert "frontend" in areas
    assert areas[-1] == "qa"


def test_w136_bundle_exports_markdown_and_json(idea: AppIdea, blueprint: AppBlueprint):
    artifact = StoredIdeaPRDGenerator(store=_store_with(idea)).generate(idea.idea_id).artifact
    schema = build_schema_plan(blueprint)
    api = build_api_contract(blueprint, schema)
    tasks = build_task_plan(blueprint, schema, api)
    bundle = build_bundle(artifact, schema, api, tasks)
    assert "# App Factory Bundle" in bundle.to_markdown()
    assert json.loads(bundle.to_json())["artifact_id"] == artifact.artifact_id


def test_w137_quality_gate_passes_complete_bundle(idea: AppIdea, blueprint: AppBlueprint):
    artifact = StoredIdeaPRDGenerator(store=_store_with(idea)).generate(idea.idea_id).artifact
    schema = build_schema_plan(blueprint)
    api = build_api_contract(blueprint, schema)
    tasks = build_task_plan(blueprint, schema, api)
    report = validate_bundle(build_bundle(artifact, schema, api, tasks))
    assert report.passed is True


def test_w138_artifact_registry_lists_latest():
    registry = ArtifactRegistry(dry_run=True)
    registry.register(ArtifactRegistryEntry("idea_1", "schema", "bp_1"))
    registry.register(ArtifactRegistryEntry("idea_1", "schema", "bp_2"))
    assert registry.latest("idea_1", "schema").artifact_id == "bp_2"


def test_w139_scaffold_plan_suggests_backend_frontend_and_tests(blueprint: AppBlueprint):
    schema = build_schema_plan(blueprint)
    api = build_api_contract(blueprint, schema)
    tasks = build_task_plan(blueprint, schema, api)
    plan = build_scaffold_plan(schema, api, tasks)
    paths = {file.path for file in plan.files}
    assert "README.md" in paths
    assert any(path.startswith("backend/models/") for path in paths)
    assert "tests/test_smoke.py" in paths


def test_w140_scaffold_dry_run_does_not_write_and_blocks_traversal(app_factory_tmp_dir: Path):
    plan = ScaffoldPlan("bp_1", [ScaffoldFilePlan("README.md", "readme", "docs")])
    result = run_scaffold(plan, app_factory_tmp_dir / "app", dry_run=True)
    assert result.written_files == []
    assert not (app_factory_tmp_dir / "app" / "README.md").exists()
    bad = ScaffoldPlan("bp_1", [ScaffoldFilePlan("../escape.txt", "bad", "test")])
    with pytest.raises(ValueError):
        run_scaffold(bad, app_factory_tmp_dir / "app", dry_run=True)


def test_w141_docs_generator_creates_expected_documents(idea: AppIdea, blueprint: AppBlueprint):
    artifact = StoredIdeaPRDGenerator(store=_store_with(idea)).generate(idea.idea_id).artifact
    schema = build_schema_plan(blueprint)
    api = build_api_contract(blueprint, schema)
    tasks = build_task_plan(blueprint, schema, api)
    docs = build_generated_docs(build_bundle(artifact, schema, api, tasks))
    assert {"ARCHITECTURE.md", "API.md", "DATA.md", "README.md"} <= set(docs.documents)


def test_w142_pipeline_and_cli_commands(app_factory_tmp_dir: Path, idea: AppIdea, monkeypatch):
    store = _store_with(idea, app_factory_tmp_dir)
    result = build_planning_pipeline(idea.idea_id, store=store)
    assert result.quality_report.passed is True

    import src.app_factory.idea_cli as cli_mod
    monkeypatch.setattr(cli_mod, "IdeaStore", lambda dry_run=True: store)
    runner = CliRunner()
    for command in ["schema", "api", "tasks", "validate", "artifacts", "scaffold-plan", "docs", "build-plan"]:
        output = runner.invoke(idea_app, [command, idea.idea_id])
        assert output.exit_code == 0, output.stdout
    assert runner.invoke(idea_app, ["export", idea.idea_id, "--format", "json"]).exit_code == 0


def _store_with(idea: AppIdea, data_dir: Path | None = None) -> IdeaStore:
    store = IdeaStore(data_dir=data_dir or Path(".test_tmp/app_factory_unit"), dry_run=False)
    store.save(idea)
    store.dry_run = True
    return store

"""Tests for G14 App Factory waves W132-W140."""
from __future__ import annotations

import json

import pytest

from src.app_factory.api_contract import build_api_contract
from src.app_factory.errors import PRDGenerationError
from src.app_factory.frontend_plan import build_frontend_plan
from src.app_factory.idea_store import IdeaStore
from src.app_factory.models import AppBlueprint, AppIdea, AppRequirement
from src.app_factory.openhands_mock import OpenHandsMockAdapter
from src.app_factory.package_export import build_package_export
from src.app_factory.planner import AppFactoryPlanner
from src.app_factory.prd_service import StoredIdeaPRDGenerator
from src.app_factory.repo_scaffold import generate_repo_scaffold
from src.app_factory.schema_planner import build_schema_plan
from src.app_factory.test_plan import build_test_plan


@pytest.fixture
def sample_idea() -> AppIdea:
    return AppIdea.new(
        title="Ops Dashboard",
        description="A web app with user login, admin dashboard, reports and search",
        target_audience="operators",
        features=["login", "admin dashboard", "reports", "search"],
        constraints=["offline-first dry-run"],
        domain="operations",
    )


@pytest.fixture
def sample_blueprint(sample_idea):
    req = AppRequirement.from_idea(sample_idea)
    return sample_idea, req, AppBlueprint.from_requirement(req)


def test_w132_generates_prd_from_stored_idea(app_factory_tmp_dir, sample_idea):
    store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
    store.save(sample_idea)
    result = StoredIdeaPRDGenerator(store=store).generate(sample_idea.idea_id, dry_run=True)
    assert result.idea_id == sample_idea.idea_id
    assert result.persisted is False
    assert "# PRD: Ops Dashboard" in result.artifact.prd_markdown


def test_w132_missing_idea_raises(app_factory_tmp_dir):
    store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
    with pytest.raises(PRDGenerationError):
        StoredIdeaPRDGenerator(store=store).generate("missing", dry_run=True)


def test_w132_non_dry_run_persists_prd_jsonl(app_factory_tmp_dir, sample_idea):
    store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
    store.save(sample_idea)
    output = app_factory_tmp_dir / "prds.jsonl"
    result = StoredIdeaPRDGenerator(store=store, output_path=output).generate(sample_idea.idea_id, dry_run=False)
    assert result.persisted is True
    record = json.loads(output.read_text(encoding="utf-8").strip())
    assert record["idea_id"] == sample_idea.idea_id


def test_w133_schema_plan_has_tables_fields_and_no_migrations(sample_blueprint):
    _, _, blueprint = sample_blueprint
    plan = build_schema_plan(blueprint)
    assert plan.dry_run is True
    assert plan.migrations_allowed is False
    assert plan.tables
    assert any(field.primary_key for field in plan.tables[0].fields)


def test_w134_api_contract_matches_schema_models(sample_blueprint):
    _, _, blueprint = sample_blueprint
    schema = build_schema_plan(blueprint)
    contract = build_api_contract(blueprint, schema)
    assert contract.endpoints
    assert any(endpoint.path == "/health" for endpoint in contract.endpoints)
    assert all(endpoint.errors for endpoint in contract.endpoints)


def test_w135_frontend_plan_generates_routes_and_components(sample_blueprint):
    _, _, blueprint = sample_blueprint
    schema = build_schema_plan(blueprint)
    contract = build_api_contract(blueprint, schema)
    plan = build_frontend_plan(blueprint, contract)
    assert {route["path"] for route in plan.routes}
    assert plan.components
    assert plan.user_flows


def test_w136_test_plan_covers_contracts_e2e_and_acceptance(sample_blueprint):
    _, _, blueprint = sample_blueprint
    schema = build_schema_plan(blueprint)
    contract = build_api_contract(blueprint, schema)
    frontend = build_frontend_plan(blueprint, contract)
    plan = build_test_plan(schema, contract, frontend)
    assert plan.unit_tests
    assert plan.integration_tests
    assert plan.contract_tests
    assert plan.e2e_smoke
    assert plan.acceptance_criteria


def test_w137_scaffold_dry_run_does_not_write(app_factory_tmp_dir, sample_idea):
    artifact = AppFactoryPlanner().plan(sample_idea, dry_run=True)
    out = app_factory_tmp_dir / "scaffold"
    manifest = generate_repo_scaffold(artifact, out, dry_run=True)
    assert manifest.dry_run is True
    assert manifest.written is False
    assert manifest.files
    assert not out.exists()


def test_w137_scaffold_refuses_overwrite(app_factory_tmp_dir, sample_idea):
    artifact = AppFactoryPlanner().plan(sample_idea, dry_run=True)
    out = app_factory_tmp_dir / "scaffold"
    manifest = generate_repo_scaffold(artifact, out, dry_run=False)
    assert manifest.written is True
    with pytest.raises(FileExistsError):
        generate_repo_scaffold(artifact, out, dry_run=False)


def test_w138_openhands_mock_success_and_failure(app_factory_tmp_dir, sample_idea):
    artifact = AppFactoryPlanner().plan(sample_idea, dry_run=True)
    manifest = generate_repo_scaffold(artifact, app_factory_tmp_dir / "scaffold", dry_run=True)
    adapter = OpenHandsMockAdapter()
    ok = adapter.execute(manifest, dry_run=True)
    failed = adapter.execute(manifest, dry_run=True, fail=True)
    assert ok.status == "dry_run"
    assert ok.planned_steps
    assert failed.status == "failed"
    assert failed.errors


def test_w139_package_export_contains_expected_files(app_factory_tmp_dir, sample_blueprint):
    idea, req, blueprint = sample_blueprint
    artifact = AppFactoryPlanner().plan(idea, dry_run=True)
    schema = build_schema_plan(blueprint)
    contract = build_api_contract(blueprint, schema)
    frontend = build_frontend_plan(blueprint, contract)
    tests = build_test_plan(schema, contract, frontend)
    scaffold = generate_repo_scaffold(artifact, app_factory_tmp_dir / "scaffold", dry_run=True)
    execution = OpenHandsMockAdapter().execute(scaffold)
    package = build_package_export(
        "pkg_test",
        artifact.prd_markdown,
        schema,
        contract,
        frontend,
        tests,
        scaffold,
        execution,
        app_factory_tmp_dir / "package",
        dry_run=True,
    )
    assert "PRD.md" in package.files
    assert "schema_plan.json" in package.files
    assert package.written is False


def test_w140_app_factory_e2e_flow(app_factory_tmp_dir, sample_idea):
    store = IdeaStore(data_dir=app_factory_tmp_dir / "ideas", dry_run=False)
    store.save(sample_idea)
    prd = StoredIdeaPRDGenerator(store=store).generate(sample_idea.idea_id, dry_run=True)
    req = AppRequirement.from_idea(sample_idea)
    blueprint = AppBlueprint.from_requirement(req)
    schema = build_schema_plan(blueprint)
    contract = build_api_contract(blueprint, schema)
    frontend = build_frontend_plan(blueprint, contract)
    tests = build_test_plan(schema, contract, frontend)
    scaffold = generate_repo_scaffold(prd.artifact, app_factory_tmp_dir / "scaffold", dry_run=True)
    execution = OpenHandsMockAdapter().execute(scaffold, dry_run=True)
    package = build_package_export(
        "pkg_e2e",
        prd.artifact.prd_markdown,
        schema,
        contract,
        frontend,
        tests,
        scaffold,
        execution,
        app_factory_tmp_dir / "package",
        dry_run=True,
    )
    assert prd.artifact.prd_markdown.startswith("# PRD:")
    assert schema.tables
    assert contract.endpoints
    assert frontend.routes
    assert tests.contract_tests
    assert scaffold.files
    assert execution.status == "dry_run"
    assert package.files

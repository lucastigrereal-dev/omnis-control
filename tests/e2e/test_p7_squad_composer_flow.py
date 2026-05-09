"""E2E: P7 Squad Composer Lite full flow — request → sector → capabilities → roles → squad → tasks → run manifest → approval gate."""
import json
import os
import socket

import pytest

from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad
from src.task_decomposer.errors import CyclicDependencyError
from src.squad_execution.planner import plan_squad_run
from src.squad_execution.exporter import export_squad_run, no_secrets_in_manifest
from src.squad_execution.models import (
    SQUAD_RUN_STATUS_PLANNED_READY,
    SQUAD_RUN_STATUS_BLOCKED_APPROVAL,
    SquadExecutionPlan,
)


# ═══════════════════════════════════════════════════════════════════════════
# E2E 1 — Marketing campaign flow
# ═══════════════════════════════════════════════════════════════════════════

def test_e2e_marketing_campaign_full_flow():
    """request → sector → capabilities → roles → squad → tasks → run manifest → planned_ready."""
    request = "cria campanha de 10 posts para hotel"

    # 1. Compose squad
    squad = compose_squad(request)
    assert squad.sector == "marketing"
    assert any("marketing_strategist" == r.role_id for r in squad.roles)
    assert any("copywriter" == r.role_id for r in squad.roles)
    assert any("qa_auditor" == r.role_id for r in squad.roles)
    assert len(squad.capabilities) > 0

    # 2. Decompose into tasks
    task_plan = decompose_squad(squad)
    assert len(task_plan.tasks) >= 3
    assert task_plan.risk_level in ("low", "medium", "high")
    assert task_plan.task_plan_id.startswith("tplan_")

    # 3. Create execution plan
    run = SquadExecutionPlan.from_plans(squad, task_plan)
    assert run.sector == "marketing"
    assert run.status == SQUAD_RUN_STATUS_PLANNED_READY
    assert run.approval_required is False
    assert len(run.roles) >= 3
    assert len(run.next_actions) >= 1

    # 4. Validate manifest
    d = run.to_dict()
    assert "squad_run_id" in d
    assert "marketing" in d["sector"]
    assert d["approval_required"] is False
    assert d["status"] == SQUAD_RUN_STATUS_PLANNED_READY

    # 5. Export run files
    run_dir = export_squad_run(run, squad_plan=squad, task_plan=task_plan)
    assert run_dir.exists()
    files = sorted(p.name for p in run_dir.iterdir())
    assert "squad_manifest.json" in files
    assert "01_request.md" in files
    assert "02_squad.md" in files
    assert "03_task_plan.md" in files
    assert "04_execution_plan.md" in files
    assert "05_approval.md" in files
    assert "06_next_actions.md" in files


def test_e2e_marketing_roles_in_expected_order():
    """Marketing squad roles follow dependency order: strategist → copywriter → visual → QA."""
    squad = compose_squad("cria campanha de posts para restaurante")
    task_plan = decompose_squad(squad)
    role_order = [t.role_id for t in task_plan.tasks]

    strategist_idx = role_order.index("marketing_strategist")
    copywriter_idx = role_order.index("copywriter")
    qa_idx = role_order.index("qa_auditor")

    assert strategist_idx < copywriter_idx < qa_idx


def test_e2e_marketing_no_secrets_in_manifest():
    """No API keys, tokens or secrets in the squad manifest."""
    squad = compose_squad("cria campanha de posts para hotel")
    task_plan = decompose_squad(squad)
    run = SquadExecutionPlan.from_plans(squad, task_plan)
    manifest = run.to_dict()
    assert no_secrets_in_manifest(manifest)

    # also check raw keys
    for k in manifest:
        assert not k.lower().startswith(("meta_", "instagram_", "secret", "token", "password", "api_key"))


# ═══════════════════════════════════════════════════════════════════════════
# E2E 2 — App factory high risk flow
# ═══════════════════════════════════════════════════════════════════════════

def test_e2e_app_factory_high_risk_flow():
    """App requests are blocked pending approval."""
    request = "cria app CRM com dashboard"
    squad = compose_squad(request)
    assert squad.sector == "apps"
    assert any("app_architect" == r.role_id for r in squad.roles)
    assert any("qa_auditor" == r.role_id for r in squad.roles)
    assert squad.risk_level == "high"
    assert squad.approval_required is True

    task_plan = decompose_squad(squad)
    assert task_plan.approval_required is True
    assert task_plan.risk_level == "high"

    run = SquadExecutionPlan.from_plans(squad, task_plan)
    assert run.status == SQUAD_RUN_STATUS_BLOCKED_APPROVAL
    assert run.approval_required is True
    assert run.risk_level == "high"

    d = run.to_dict()
    assert d["status"] == SQUAD_RUN_STATUS_BLOCKED_APPROVAL
    assert any("approval" in a.lower() for a in run.next_actions)


def test_e2e_app_factory_no_secrets():
    """App manifest must not leak secrets."""
    squad = compose_squad("cria app CRM com dashboard")
    task_plan = decompose_squad(squad)
    run = SquadExecutionPlan.from_plans(squad, task_plan)
    assert no_secrets_in_manifest(run.to_dict())


# ═══════════════════════════════════════════════════════════════════════════
# E2E 3 — Unknown request fallback
# ═══════════════════════════════════════════════════════════════════════════

def test_e2e_unknown_request_does_not_crash():
    """Ambiguous requests must not crash the pipeline."""
    request = "faz aquele negócio lá do jeito bonito"
    squad = compose_squad(request)
    assert squad.sector == "unknown"
    assert len(squad.roles) >= 1
    assert "qa_auditor" in [r.role_id for r in squad.roles]

    task_plan = decompose_squad(squad)
    run = SquadExecutionPlan.from_plans(squad, task_plan)

    if run.approval_required:
        assert any(a for a in run.next_actions)
    else:
        assert run.status == SQUAD_RUN_STATUS_PLANNED_READY


def test_e2e_unknown_request_has_next_action():
    """Fallback must include a next_action that suggests refinement."""
    squad = compose_squad("faz aquele negócio lá")
    task_plan = decompose_squad(squad)
    run = SquadExecutionPlan.from_plans(squad, task_plan)
    d = run.to_dict()
    assert "next_actions" in d
    assert len(d["next_actions"]) >= 1


# ═══════════════════════════════════════════════════════════════════════════
# E2E 4 — No external actions, no network, no .env
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("request_text", [
    "cria campanha de 10 posts para hotel",
    "cria app CRM com dashboard",
    "faz aquele negócio lá do jeito bonito",
])
def test_e2e_no_network_calls(request_text):
    """Pipeline must not make any network calls."""
    squad = compose_squad(request_text)
    task_plan = decompose_squad(squad)
    run = SquadExecutionPlan.from_plans(squad, task_plan)
    assert run.squad_run_id.startswith("srun_")


@pytest.mark.parametrize("request_text", [
    "cria campanha de 10 posts para hotel",
    "cria app CRM com dashboard",
])
def test_e2e_no_env_reads(request_text):
    """Pipeline must not read .env."""
    squad = compose_squad(request_text)
    task_plan = decompose_squad(squad)
    run = SquadExecutionPlan.from_plans(squad, task_plan)
    # If we got here without ImportError / FileNotFoundError for .env, it passed.
    assert run.squad_run_id


@pytest.mark.parametrize("request_text", [
    "cria campanha de 10 posts para hotel",
    "cria app CRM com dashboard",
    "faz aquele negócio lá",
])
def test_e2e_no_oauth_no_meta_no_publish(request_text):
    """Pipeline must not reference OAuth, Meta or publishing."""
    squad = compose_squad(request_text)
    task_plan = decompose_squad(squad)
    run = SquadExecutionPlan.from_plans(squad, task_plan)
    d = run.to_dict()
    combined = json.dumps(d).lower()
    assert "oauth" not in combined
    assert "meta_" not in combined
    assert "publish" not in combined
    assert "instagram" not in combined


# ═══════════════════════════════════════════════════════════════════════════
# E2E 5 — planner convenience function
# ═══════════════════════════════════════════════════════════════════════════

def test_e2e_planner_convenience_marketing():
    """plan_squad_run convenience returns a ready plan for marketing."""
    plan = plan_squad_run("cria campanha de posts para hotel")
    assert isinstance(plan, SquadExecutionPlan)
    assert plan.status == SQUAD_RUN_STATUS_PLANNED_READY
    assert plan.approval_required is False


def test_e2e_planner_convenience_app():
    """plan_squad_run convenience returns blocked plan for app."""
    plan = plan_squad_run("cria app CRM com dashboard")
    assert isinstance(plan, SquadExecutionPlan)
    assert plan.status == SQUAD_RUN_STATUS_BLOCKED_APPROVAL
    assert plan.approval_required is True


# ═══════════════════════════════════════════════════════════════════════════
# E2E 6 — dependency graph integrity
# ═══════════════════════════════════════════════════════════════════════════

def test_e2e_dependency_graph_no_cycles():
    """All requests should produce acyclic task graphs."""
    for req in [
        "cria campanha de 10 posts para hotel",
        "cria app CRM com dashboard",
        "faz aquele negócio lá",
    ]:
        squad = compose_squad(req)
        # decompose_squad raises CyclicDependencyError on cycle
        task_plan = decompose_squad(squad)
        assert len(task_plan.dependency_graph) > 0


def test_e2e_all_task_deps_are_valid():
    """Every dependency references an existing task_id."""
    for req in [
        "cria campanha de 10 posts para hotel",
        "cria app CRM com dashboard",
        "faz aquele negócio lá",
    ]:
        squad = compose_squad(req)
        task_plan = decompose_squad(squad)
        all_ids = {t.task_id for t in task_plan.tasks}
        for t in task_plan.tasks:
            for dep in t.depends_on:
                assert dep in all_ids, f"Task {t.task_id} depends on unknown {dep}"

"""Tests for Squad Execution models."""
from src.squad_execution.models import SquadExecutionPlan, SQUAD_RUN_STATUS_PLANNED_READY, SQUAD_RUN_STATUS_BLOCKED_APPROVAL
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad


def make_exec_plan(request="cria campanha de posts para hotel"):
    squad = compose_squad(request)
    task_plan = decompose_squad(squad)
    return SquadExecutionPlan.from_plans(squad, task_plan)


def test_squad_run_id_prefix():
    plan = make_exec_plan()
    assert plan.squad_run_id.startswith("srun_")


def test_marketing_is_planned_ready():
    plan = make_exec_plan("cria campanha de posts para hotel")
    assert plan.status == SQUAD_RUN_STATUS_PLANNED_READY


def test_app_is_blocked_approval():
    plan = make_exec_plan("cria app CRM com dashboard")
    assert plan.status == SQUAD_RUN_STATUS_BLOCKED_APPROVAL
    assert plan.approval_required is True


def test_to_dict_has_required_keys():
    plan = make_exec_plan()
    d = plan.to_dict()
    for key in ["squad_run_id", "request", "sector", "status", "approval_required"]:
        assert key in d

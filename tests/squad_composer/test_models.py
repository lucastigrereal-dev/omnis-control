"""Tests for Squad Composer models."""
from src.squad_composer.models import SquadPlan, SquadRoleAssignment


def _make_roles(risk="low"):
    return [SquadRoleAssignment("copywriter", "Copywriter", "test", ["caption"], risk)]


def test_squad_plan_id_prefix():
    plan = SquadPlan.new("test request", "marketing", _make_roles(), [])
    assert plan.squad_id.startswith("squad_")


def test_squad_plan_low_risk_no_approval():
    plan = SquadPlan.new("test request", "marketing", _make_roles("low"), [])
    assert plan.approval_required is False
    assert plan.risk_level == "low"


def test_squad_plan_high_risk_requires_approval():
    plan = SquadPlan.new("test request", "apps", _make_roles("high"), [])
    assert plan.approval_required is True
    assert plan.risk_level == "high"


def test_squad_plan_medium_risk_requires_approval():
    plan = SquadPlan.new("test request", "sales", _make_roles("medium"), [])
    assert plan.approval_required is True


def test_squad_plan_to_dict_round_trip():
    plan = SquadPlan.new("test", "marketing", _make_roles(), ["cap1"])
    d = plan.to_dict()
    assert d["squad_id"] == plan.squad_id
    assert d["sector"] == "marketing"
    assert isinstance(d["roles"], list)
    assert d["capabilities"] == ["cap1"]

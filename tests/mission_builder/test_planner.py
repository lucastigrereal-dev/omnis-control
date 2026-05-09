"""Tests for mission planner — build_plan, account extraction, slot count."""
import pytest
from pathlib import Path
from src.mission_builder.planner import build_plan, _extract_account, _extract_slot_count
from src.mission_builder.errors import IntentUnknownError
from src.mission_builder.models import MissionPlan

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "intents.yaml"


def test_build_plan_returns_mission_plan():
    plan = build_plan("cria um carrossel sobre praias de Natal", config_path=CONFIG_PATH)
    assert isinstance(plan, MissionPlan)
    assert plan.intent == "carousel"
    assert plan.deliverable == "carousel_package"


def test_build_plan_generates_steps():
    plan = build_plan("cria um carrossel de dicas de viagem", config_path=CONFIG_PATH)
    assert len(plan.steps) >= 4


def test_build_plan_extracts_account_from_option():
    plan = build_plan(
        "cria um reel",
        account_handle="oinatalrn",
        config_path=CONFIG_PATH,
    )
    assert plan.account_handle == "oinatalrn"


def test_build_plan_extracts_account_from_text():
    plan = build_plan(
        "cria um carrossel para @lucastigrereal sobre viagem",
        config_path=CONFIG_PATH,
    )
    assert plan.account_handle == "lucastigrereal"


def test_build_plan_default_account_fallback():
    plan = build_plan("cria um carrossel interessante", config_path=CONFIG_PATH)
    assert plan.account_handle == "afamiliatigrereal"


def test_build_plan_extracts_slot_count_from_text():
    plan = build_plan("cria uma campanha de 15 posts para hotel", config_path=CONFIG_PATH)
    assert plan.estimated_slots == 15


def test_build_plan_default_slot_for_carousel():
    plan = build_plan("cria um carrossel", config_path=CONFIG_PATH)
    assert plan.estimated_slots == 5


def test_build_plan_default_slot_for_reels():
    plan = build_plan("faz um reel", config_path=CONFIG_PATH)
    assert plan.estimated_slots == 1


def test_build_plan_caps_slot_at_100():
    plan = build_plan("cria uma campanha de 200 posts", config_path=CONFIG_PATH)
    assert plan.estimated_slots == 100


def test_build_plan_raises_on_unknown_intent():
    with pytest.raises(IntentUnknownError):
        build_plan("faça algo genérico incrível", config_path=CONFIG_PATH)


def test_build_plan_allow_unknown():
    plan = build_plan(
        "faça algo genérico incrível",
        allow_unknown=True,
        config_path=CONFIG_PATH,
    )
    assert plan.intent == "unknown"


def test_extract_account_regex():
    assert _extract_account("post para @oinatalrn") == "oinatalrn"
    assert _extract_account("conteudo para afamiliatigrereal") == "afamiliatigrereal"
    assert _extract_account("sem mencao de conta") == "afamiliatigrereal"


def test_extract_slot_count():
    assert _extract_slot_count("10 posts de viagem", "campaign") == 10
    assert _extract_slot_count("sem numero", "carousel") == 5
    assert _extract_slot_count("sem numero", "reels") == 1

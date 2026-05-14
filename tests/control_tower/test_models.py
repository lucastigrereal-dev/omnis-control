import uuid
import pytest
from src.control_tower.models import (
    Decision, RiskLevel, ActionType, BoundarySystem, BoundaryRule,
    TowerRequest, NextAction, _now_iso, _new_id, _short_id,
)


class TestBoundaryRule:
    def test_allows_matching_action(self):
        rule = BoundaryRule(
            source_system=BoundarySystem.OMNIS,
            target_system=BoundarySystem.SKILLS,
            allowed_actions=["call_skill", "list_skills"],
            forbidden_actions=[],
        )
        assert rule.allows("call_skill") is True

    def test_denies_forbidden_action(self):
        rule = BoundaryRule(
            source_system=BoundarySystem.OMNIS,
            target_system=BoundarySystem.KRATOS,
            allowed_actions=["read_status"],
            forbidden_actions=["write", "delete"],
        )
        assert rule.allows("delete") is False

    def test_denies_unknown_action(self):
        rule = BoundaryRule(
            source_system=BoundarySystem.OMNIS,
            target_system=BoundarySystem.AKASHA,
            allowed_actions=["read_memory"],
            forbidden_actions=[],
        )
        assert rule.allows("unknown_action") is False

    def test_to_dict(self):
        rule = BoundaryRule(
            source_system=BoundarySystem.OMNIS,
            target_system=BoundarySystem.KRATOS,
            allowed_actions=["read_status"],
            forbidden_actions=["write"],
        )
        d = rule.to_dict()
        assert d["source_system"] == "OMNIS"
        assert d["target_system"] == "KRATOS"


class TestDecision:
    def test_new_decision_generates_id(self):
        d = Decision(title="Test")
        assert d.decision_id.startswith("ctd_")
        assert d.title == "Test"

    def test_is_blocked(self):
        d = Decision(action_type=ActionType.BLOCK)
        assert d.is_blocked is True

    def test_is_not_blocked(self):
        d = Decision(action_type=ActionType.OBSERVE)
        assert d.is_blocked is False

    def test_is_safe_low(self):
        d = Decision(risk_level=RiskLevel.LOW)
        assert d.is_safe is True

    def test_is_safe_medium(self):
        d = Decision(risk_level=RiskLevel.MEDIUM)
        assert d.is_safe is True

    def test_is_not_safe_high(self):
        d = Decision(risk_level=RiskLevel.HIGH)
        assert d.is_safe is False

    def test_to_dict_roundtrip(self):
        d = Decision(
            title="Test Decision",
            risk_level=RiskLevel.HIGH,
            action_type=ActionType.EXECUTE_WITH_APPROVAL,
            requires_human_approval=True,
            rationale="Test rationale",
            do_not_do=["delete", "push"],
            next_step="Request approval",
        )
        data = d.to_dict()
        restored = Decision.from_dict(data)
        assert restored.title == d.title
        assert restored.risk_level == d.risk_level
        assert restored.action_type == d.action_type
        assert restored.requires_human_approval is True
        assert restored.do_not_do == ["delete", "push"]

    def test_requires_human_approval_default(self):
        d = Decision()
        assert d.requires_human_approval is False


class TestTowerRequest:
    def test_default_source_and_target_omnis(self):
        r = TowerRequest()
        assert r.source_system == BoundarySystem.OMNIS
        assert r.target_system == BoundarySystem.OMNIS

    def test_action_and_paths(self):
        r = TowerRequest(
            title="Test",
            action="read_status",
            paths_touched=["src/test.py"],
            is_external=True,
            is_destructive=False,
        )
        assert r.action == "read_status"
        assert r.paths_touched == ["src/test.py"]
        assert r.is_external is True
        assert r.is_destructive is False

    def test_to_dict(self):
        r = TowerRequest(title="Req", action="test")
        d = r.to_dict()
        assert d["title"] == "Req"
        assert d["action"] == "test"


class TestNextAction:
    def test_defaults(self):
        na = NextAction()
        assert na.action_id.startswith("ctn_")
        assert na.dry_run_required is True
        assert na.requires_approval is False

    def test_custom_values(self):
        na = NextAction(
            decision_id="ctd_test",
            title="Do X",
            target_system=BoundarySystem.SKILLS,
            action="call_skill",
            dry_run_required=True,
            requires_approval=True,
        )
        assert na.target_system == BoundarySystem.SKILLS
        assert na.requires_approval is True

    def test_to_dict(self):
        na = NextAction(title="Test", action="observe")
        d = na.to_dict()
        assert d["title"] == "Test"
        assert d["action"] == "observe"


class TestIDs:
    def test_new_id_prefix(self):
        id_ = _new_id("test")
        assert id_.startswith("test_")
        assert len(id_) > 6

    def test_short_id_prefix(self):
        id_ = _short_id("ts")
        assert id_.startswith("ts_")

    def test_now_iso_format(self):
        ts = _now_iso()
        assert "T" in ts

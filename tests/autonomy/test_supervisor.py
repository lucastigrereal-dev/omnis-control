"""Tests for AutonomySupervisor — N0-N7 levels, risk decisions, sector suggestions."""
from __future__ import annotations

import pytest

from src.autonomy.supervisor import (
    AutonomySupervisor,
    AutonomyDecision,
    AUTONOMY_LEVELS,
    AUTONOMY_LABELS,
    DEFAULT_LEVEL,
)
from src.governance.models import (
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_CRITICAL,
)


@pytest.fixture
def supervisor():
    return AutonomySupervisor()


# ── AutonomyDecision ───────────────────────────────────────────────────

class TestAutonomyDecision:
    def test_to_dict(self):
        d = AutonomyDecision(
            mission_id="MIS-001",
            level=3,
            level_label="N3",
            action_allowed=True,
            reason="ok",
            requires_approval=False,
        )
        dd = d.to_dict()
        assert dd["level"] == 3
        assert dd["action_allowed"] is True


# ── default level ──────────────────────────────────────────────────────

class TestDefaults:
    def test_default_is_n2(self):
        s = AutonomySupervisor()
        assert s.default_level == 2

    def test_rejects_invalid_level(self):
        with pytest.raises(ValueError):
            AutonomySupervisor(default_level=99)

    def test_custom_default(self):
        s = AutonomySupervisor(default_level=5)
        assert s.get_level("any") == 5


# ── get/set level ──────────────────────────────────────────────────────

class TestGetSetLevel:
    def test_set_valid_level(self, supervisor):
        supervisor.set_mission_level("MIS-001", 3)
        assert supervisor.get_level("MIS-001") == 3

    def test_set_invalid_raises(self, supervisor):
        with pytest.raises(ValueError):
            supervisor.set_mission_level("MIS-001", 99)

    def test_unset_uses_default(self, supervisor):
        assert supervisor.get_level("MIS-new") == DEFAULT_LEVEL

    def test_levels_are_per_mission(self, supervisor):
        supervisor.set_mission_level("MIS-A", 3)
        supervisor.set_mission_level("MIS-B", 5)
        assert supervisor.get_level("MIS-A") == 3
        assert supervisor.get_level("MIS-B") == 5

    def test_get_level_label(self, supervisor):
        supervisor.set_mission_level("MIS-001", 4)
        label = supervisor.get_level_label("MIS-001")
        assert "N4" in label or "Médio" in label

    def test_mission_levels_property(self, supervisor):
        supervisor.set_mission_level("MIS-X", 3)
        assert supervisor.mission_levels["MIS-X"] == 3


# ── can_execute ────────────────────────────────────────────────────────

class TestCanExecute:
    def test_n0_never_executes(self, supervisor):
        supervisor.set_mission_level("MIS-001", 0)
        d = supervisor.can_execute("MIS-001", RISK_LOW)
        assert d.action_allowed is False
        assert d.requires_approval is True

    def test_n1_never_executes(self, supervisor):
        supervisor.set_mission_level("MIS-001", 1)
        d = supervisor.can_execute("MIS-001", RISK_LOW)
        assert d.action_allowed is False

    def test_n2_never_executes(self, supervisor):
        supervisor.set_mission_level("MIS-001", 2)
        d = supervisor.can_execute("MIS-001", RISK_LOW)
        assert d.action_allowed is False

    def test_n3_allows_low(self, supervisor):
        supervisor.set_mission_level("MIS-001", 3)
        d = supervisor.can_execute("MIS-001", RISK_LOW)
        assert d.action_allowed is True
        assert d.requires_approval is False

    def test_n3_blocks_medium(self, supervisor):
        supervisor.set_mission_level("MIS-001", 3)
        d = supervisor.can_execute("MIS-001", RISK_MEDIUM)
        assert d.action_allowed is False
        assert d.requires_approval is True

    def test_n4_allows_medium(self, supervisor):
        supervisor.set_mission_level("MIS-001", 4)
        assert supervisor.can_execute("MIS-001", RISK_MEDIUM).action_allowed is True
        assert supervisor.can_execute("MIS-001", RISK_HIGH).action_allowed is False

    def test_n5_allows_high(self, supervisor):
        supervisor.set_mission_level("MIS-001", 5)
        assert supervisor.can_execute("MIS-001", RISK_HIGH).action_allowed is True
        assert supervisor.can_execute("MIS-001", RISK_CRITICAL).action_allowed is False

    def test_n6_allows_critical(self, supervisor):
        supervisor.set_mission_level("MIS-001", 6)
        assert supervisor.can_execute("MIS-001", RISK_CRITICAL).action_allowed is True
        assert supervisor.can_execute("MIS-001", RISK_CRITICAL).requires_approval is False

    def test_n7_allows_everything(self, supervisor):
        supervisor.set_mission_level("MIS-001", 7)
        for risk in [RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL]:
            assert supervisor.can_execute("MIS-001", risk).action_allowed is True


# ── suggest_level ──────────────────────────────────────────────────────

class TestSuggestLevel:
    def test_marketing_suggests_n3(self, supervisor):
        assert supervisor.suggest_level("marketing") == 3

    def test_sales_suggests_n2(self, supervisor):
        assert supervisor.suggest_level("sales") == 2

    def test_app_factory_suggests_n4(self, supervisor):
        assert supervisor.suggest_level("app_factory") == 4

    def test_computer_ops_suggests_n3(self, supervisor):
        assert supervisor.suggest_level("computer_ops") == 3

    def test_finance_suggests_n1(self, supervisor):
        assert supervisor.suggest_level("finance") == 1

    def test_general_suggests_default(self, supervisor):
        assert supervisor.suggest_level("general") == DEFAULT_LEVEL

    def test_unknown_suggests_default(self, supervisor):
        assert supervisor.suggest_level("unknown_sector") == DEFAULT_LEVEL


# ── constants ──────────────────────────────────────────────────────────

def test_all_8_levels_defined():
    for n in range(8):
        assert n in AUTONOMY_LEVELS
        assert n in AUTONOMY_LABELS


def test_default_is_valid():
    assert DEFAULT_LEVEL in AUTONOMY_LEVELS

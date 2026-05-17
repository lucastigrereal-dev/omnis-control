"""W169 — Tests for KratosPermissionGate."""
import pytest
from src.kratos_bridge.permission_gate import (
    GateResult,
    KratosPermissionGate,
    Permission,
    PermissionRule,
)
from src.kratos_bridge.models import KratosPayload, PayloadType


def _p(module: str = "omnis", ptype: PayloadType = PayloadType.STATUS_UPDATE) -> KratosPayload:
    return KratosPayload(source_module=module, payload_type=ptype)


# ---------------------------------------------------------------------------
# PermissionRule
# ---------------------------------------------------------------------------

def test_rule_allow_factory():
    r = PermissionRule.allow("omnis", ["STATUS_UPDATE"])
    assert r.permission == Permission.ALLOW
    assert r.source_module == "omnis"


def test_rule_deny_factory():
    r = PermissionRule.deny("kratos", reason="anti-loop")
    assert r.permission == Permission.DENY
    assert r.reason == "anti-loop"


def test_rule_audit_only_factory():
    r = PermissionRule.audit_only("external")
    assert r.permission == Permission.AUDIT_ONLY


def test_rule_wildcard_matches_any():
    r = PermissionRule.allow("*")
    assert r.matches(_p("omnis"))
    assert r.matches(_p("kratos"))
    assert r.matches(_p("aurora"))


def test_rule_specific_module_match():
    r = PermissionRule.allow("omnis")
    assert r.matches(_p("omnis"))
    assert not r.matches(_p("kratos"))


def test_rule_type_filter():
    r = PermissionRule.deny("kratos", payload_types=["ALERT"])
    assert r.matches(_p("kratos", PayloadType.ALERT))
    assert not r.matches(_p("kratos", PayloadType.STATUS_UPDATE))


def test_rule_round_trip():
    r = PermissionRule.deny("mod", ["ALERT"], reason="blocked")
    r2 = PermissionRule.from_dict(r.to_dict())
    assert r2.source_module == "mod"
    assert r2.permission == Permission.DENY
    assert r2.reason == "blocked"


# ---------------------------------------------------------------------------
# GateResult
# ---------------------------------------------------------------------------

def test_gate_result_allowed():
    gr = GateResult(permission=Permission.ALLOW)
    assert gr.allowed
    assert not gr.audit_only


def test_gate_result_denied():
    gr = GateResult(permission=Permission.DENY)
    assert not gr.allowed


def test_gate_result_audit_only():
    gr = GateResult(permission=Permission.AUDIT_ONLY)
    assert not gr.allowed
    assert gr.audit_only


def test_gate_result_to_dict():
    gr = GateResult(payload_id="p1", permission=Permission.ALLOW)
    d = gr.to_dict()
    assert d["allowed"] is True
    assert d["payload_id"] == "p1"


# ---------------------------------------------------------------------------
# Default gate behavior
# ---------------------------------------------------------------------------

def test_default_gate_allows_omnis():
    gate = KratosPermissionGate()
    result = gate.check(_p("omnis", PayloadType.STATUS_UPDATE))
    assert result.allowed


def test_default_gate_blocks_kratos_alert():
    gate = KratosPermissionGate()
    result = gate.check(_p("kratos", PayloadType.ALERT))
    assert not result.allowed
    assert result.permission == Permission.DENY


def test_default_gate_allows_kratos_non_alert():
    gate = KratosPermissionGate()
    result = gate.check(_p("kratos", PayloadType.STATUS_UPDATE))
    assert result.allowed


# ---------------------------------------------------------------------------
# Custom rules
# ---------------------------------------------------------------------------

def test_deny_all_from_module():
    gate = KratosPermissionGate(rules=[PermissionRule.deny("external")])
    result = gate.check(_p("external"))
    assert not result.allowed


def test_first_match_wins():
    rules = [
        PermissionRule.deny("omnis", payload_types=["ALERT"]),
        PermissionRule.allow("omnis"),
    ]
    gate = KratosPermissionGate(rules=rules)
    result = gate.check(_p("omnis", PayloadType.ALERT))
    assert not result.allowed

    result2 = gate.check(_p("omnis", PayloadType.STATUS_UPDATE))
    assert result2.allowed


def test_audit_only_not_allowed():
    gate = KratosPermissionGate(rules=[PermissionRule.audit_only("omnis")])
    result = gate.check(_p("omnis"))
    assert result.audit_only
    assert not result.allowed


# ---------------------------------------------------------------------------
# Add/remove rules
# ---------------------------------------------------------------------------

def test_add_rule_at_front():
    gate = KratosPermissionGate(rules=[PermissionRule.allow("*")])
    deny = PermissionRule.deny("blocked")
    gate.add_rule(deny, position=0)
    result = gate.check(_p("blocked"))
    assert not result.allowed


def test_remove_rule():
    r = PermissionRule.allow("omnis")
    gate = KratosPermissionGate(rules=[r, PermissionRule.deny("*")])
    removed = gate.remove_rule(r.rule_id)
    assert removed
    result = gate.check(_p("omnis"))
    assert not result.allowed  # only deny rule remains


def test_remove_nonexistent_rule():
    gate = KratosPermissionGate()
    assert not gate.remove_rule("fake_id")


# ---------------------------------------------------------------------------
# check_many
# ---------------------------------------------------------------------------

def test_check_many():
    gate = KratosPermissionGate()
    payloads = [_p("omnis"), _p("omnis"), _p("kratos", PayloadType.ALERT)]
    results = gate.check_many(payloads)
    assert len(results) == 3
    allowed = [r for r in results if r.allowed]
    denied = [r for r in results if not r.allowed]
    assert len(allowed) == 2
    assert len(denied) == 1


# ---------------------------------------------------------------------------
# Default permission
# ---------------------------------------------------------------------------

def test_default_deny_blocks_unknown():
    gate = KratosPermissionGate(rules=[], default_permission=Permission.DENY)
    result = gate.check(_p("omnis"))
    assert not result.allowed
    assert result.reason == "default"


def test_default_allow_passes_unknown():
    gate = KratosPermissionGate(rules=[], default_permission=Permission.ALLOW)
    result = gate.check(_p("omnis"))
    assert result.allowed


# ---------------------------------------------------------------------------
# Audit log & stats
# ---------------------------------------------------------------------------

def test_audit_log_recorded():
    gate = KratosPermissionGate()
    gate.check(_p("omnis"))
    gate.check(_p("omnis"))
    assert len(gate.audit_log()) == 2


def test_stats():
    gate = KratosPermissionGate()
    gate.check(_p("omnis"))
    gate.check(_p("kratos", PayloadType.ALERT))
    s = gate.stats()
    assert s["total_checks"] == 2
    assert s["allowed"] == 1
    assert s["denied"] == 1

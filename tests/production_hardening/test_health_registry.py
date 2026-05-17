"""W174 — Tests for HealthCheckRegistry."""
import pytest
from src.production_hardening.health_registry import (
    CheckResult,
    CheckStatus,
    HealthCheckDef,
    HealthCheckRegistry,
    RegistryReport,
)


def _reg() -> HealthCheckRegistry:
    return HealthCheckRegistry()


# ---------------------------------------------------------------------------
# HealthCheckDef
# ---------------------------------------------------------------------------

def test_check_def_defaults():
    c = HealthCheckDef(name="db", module="core")
    assert c.enabled is True
    assert c.critical is False


def test_check_def_to_dict():
    c = HealthCheckDef(name="db", module="core", critical=True)
    d = c.to_dict()
    assert d["name"] == "db"
    assert d["critical"] is True


# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------

def test_check_result_to_dict():
    r = CheckResult(name="ping", module="net", status=CheckStatus.PASS)
    d = r.to_dict()
    assert d["status"] == "PASS"
    assert d["name"] == "ping"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_register_check():
    reg = _reg()
    c = HealthCheckDef(name="db", module="core", fn=lambda: True)
    reg.register(c)
    assert len(reg.checks()) == 1


def test_register_fn():
    reg = _reg()
    chk = reg.register_fn("ping", lambda: True, module="net")
    assert chk.name == "ping"
    assert chk.module == "net"
    assert len(reg.checks()) == 1


def test_unregister():
    reg = _reg()
    c = reg.register_fn("x", lambda: True)
    assert reg.unregister(c.check_id)
    assert len(reg.checks()) == 0


def test_unregister_missing():
    reg = _reg()
    assert not reg.unregister("nonexistent")


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------

def test_run_all_pass():
    reg = _reg()
    reg.register_fn("a", lambda: True, module="m1")
    reg.register_fn("b", lambda: True, module="m2")
    report = reg.run()
    assert report.overall == CheckStatus.PASS
    assert all(r.status == CheckStatus.PASS for r in report.results)


def test_run_one_fail():
    reg = _reg()
    reg.register_fn("ok", lambda: True)
    reg.register_fn("fail", lambda: False)
    report = reg.run()
    assert report.overall == CheckStatus.FAIL


def test_run_exception_is_fail():
    reg = _reg()
    reg.register_fn("boom", lambda: (_ for _ in ()).throw(RuntimeError("db error")))
    report = reg.run()
    assert report.results[0].status == CheckStatus.FAIL
    assert "db error" in report.results[0].message


def test_run_disabled_check_skipped():
    reg = _reg()
    chk = HealthCheckDef(name="skip_me", module="x", fn=lambda: False, enabled=False)
    reg.register(chk)
    report = reg.run()
    assert report.results[0].status == CheckStatus.SKIP


def test_run_no_fn_skipped():
    reg = _reg()
    chk = HealthCheckDef(name="no_fn", module="x")
    reg.register(chk)
    report = reg.run()
    assert report.results[0].status == CheckStatus.SKIP


def test_run_empty_registry():
    reg = _reg()
    report = reg.run()
    assert report.overall == CheckStatus.SKIP
    assert report.results == []


# ---------------------------------------------------------------------------
# Module filter
# ---------------------------------------------------------------------------

def test_run_module_filter():
    reg = _reg()
    reg.register_fn("a", lambda: True, module="core")
    reg.register_fn("b", lambda: False, module="net")
    report = reg.run(module="core")
    assert len(report.results) == 1
    assert report.results[0].name == "a"
    assert report.overall == CheckStatus.PASS


# ---------------------------------------------------------------------------
# Overall status logic
# ---------------------------------------------------------------------------

def test_critical_fail_makes_overall_fail():
    reg = _reg()
    reg.register_fn("ok", lambda: True)
    reg.register_fn("critical_fail", lambda: False, critical=True)
    report = reg.run()
    assert report.overall == CheckStatus.FAIL


def test_non_critical_fail_still_fails():
    reg = _reg()
    reg.register_fn("fail", lambda: False, critical=False)
    report = reg.run()
    assert report.overall == CheckStatus.FAIL


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def test_report_to_dict_summary():
    reg = _reg()
    reg.register_fn("a", lambda: True)
    reg.register_fn("b", lambda: False)
    report = reg.run()
    d = report.to_dict()
    assert d["summary"]["pass"] == 1
    assert d["summary"]["fail"] == 1
    assert "report_id" in d


def test_report_to_dict_results():
    reg = _reg()
    reg.register_fn("x", lambda: True)
    report = reg.run()
    assert len(report.to_dict()["results"]) == 1


# ---------------------------------------------------------------------------
# run_one
# ---------------------------------------------------------------------------

def test_run_one():
    reg = _reg()
    chk = reg.register_fn("ping", lambda: True, module="net")
    result = reg.run_one(chk.check_id)
    assert result is not None
    assert result.status == CheckStatus.PASS


def test_run_one_missing():
    reg = _reg()
    assert reg.run_one("fake") is None


# ---------------------------------------------------------------------------
# History and stats
# ---------------------------------------------------------------------------

def test_history_recorded():
    reg = _reg()
    reg.register_fn("x", lambda: True)
    reg.run()
    reg.run()
    assert len(reg.history()) == 2


def test_latest_report():
    reg = _reg()
    reg.register_fn("x", lambda: True)
    reg.run()
    assert reg.latest_report() is not None


def test_latest_report_empty():
    reg = _reg()
    assert reg.latest_report() is None


def test_stats():
    reg = _reg()
    reg.register_fn("a", lambda: True, critical=True)
    reg.register_fn("b", lambda: True, critical=False)
    chk = HealthCheckDef(name="off", module="x", enabled=False)
    reg.register(chk)
    s = reg.stats()
    assert s["registered"] == 3
    assert s["enabled"] == 2
    assert s["critical"] == 1

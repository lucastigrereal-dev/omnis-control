"""W179 — Tests for ShutdownManager."""
import pytest
from src.production_hardening.shutdown_manager import (
    ModuleShutdownResult,
    ShutdownManager,
    ShutdownModule,
    ShutdownPhase,
    ShutdownReport,
)


def _mgr(dry_run: bool = True) -> ShutdownManager:
    return ShutdownManager(dry_run=dry_run)


# ---------------------------------------------------------------------------
# ShutdownModule
# ---------------------------------------------------------------------------

def test_module_defaults():
    m = ShutdownModule(name="bridge")
    assert m.phase == 0
    assert m.timeout_seconds == 5.0
    assert m.dry_run is True


def test_module_to_dict():
    m = ShutdownModule(name="bridge", phase=5)
    d = m.to_dict()
    assert d["name"] == "bridge"
    assert d["phase"] == 5


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_register_module():
    mgr = _mgr()
    mgr.register(ShutdownModule(name="a"))
    assert "a" in mgr.modules()


def test_register_hook():
    mgr = _mgr()
    called = []
    mod = mgr.register_hook("bridge", lambda: called.append("bridge"), phase=5)
    assert mod.name == "bridge"
    assert "bridge" in mgr.modules()


# ---------------------------------------------------------------------------
# Dry-run shutdown
# ---------------------------------------------------------------------------

def test_dry_run_shutdown_ok():
    mgr = _mgr(dry_run=True)
    mgr.register(ShutdownModule(name="a"))
    mgr.register(ShutdownModule(name="b"))
    report = mgr.shutdown()
    assert report.ok
    assert len(report.results) == 2
    assert all(r.status == ShutdownPhase.STOPPED for r in report.results)


def test_dry_run_no_hooks_called():
    mgr = _mgr(dry_run=True)
    called = []
    mgr.register_hook("a", lambda: called.append("a"))
    mgr.shutdown()
    assert called == []  # dry_run: no real execution


def test_dry_run_marks_stopped():
    mgr = _mgr(dry_run=True)
    mgr.register(ShutdownModule(name="core"))
    report = mgr.shutdown()
    assert report.results[0].status == ShutdownPhase.STOPPED
    assert report.results[0].dry_run is True


# ---------------------------------------------------------------------------
# Phase ordering
# ---------------------------------------------------------------------------

def test_phase_order_highest_first():
    """Modules with higher phase stop first."""
    mgr = _mgr(dry_run=True)
    order = []
    mgr.register(ShutdownModule(name="core", phase=0))
    mgr.register(ShutdownModule(name="edge", phase=10))
    mgr.register(ShutdownModule(name="mid", phase=5))
    report = mgr.shutdown()
    names = [r.name for r in report.results]
    assert names.index("edge") < names.index("mid")
    assert names.index("mid") < names.index("core")


def test_same_phase_all_stop():
    mgr = _mgr(dry_run=True)
    for i in range(3):
        mgr.register(ShutdownModule(name=f"m{i}", phase=3))
    report = mgr.shutdown()
    assert len(report.results) == 3


# ---------------------------------------------------------------------------
# Real execution (non-dry-run)
# ---------------------------------------------------------------------------

def test_real_shutdown_calls_hooks():
    mgr = _mgr(dry_run=False)
    called = []
    mgr.register_hook("a", lambda: called.append("a"))
    mgr.register_hook("b", lambda: called.append("b"))
    report = mgr.shutdown()
    assert report.ok
    assert "a" in called and "b" in called


def test_real_shutdown_hook_failure():
    mgr = _mgr(dry_run=False)
    mgr.register_hook("failing", lambda: (_ for _ in ()).throw(RuntimeError("crash")))
    report = mgr.shutdown()
    assert not report.ok
    failed = [r for r in report.results if r.status == ShutdownPhase.FAILED]
    assert len(failed) == 1
    assert "crash" in failed[0].error


def test_real_shutdown_no_hook():
    mgr = _mgr(dry_run=False)
    mgr.register(ShutdownModule(name="no_hook", hook=None))
    report = mgr.shutdown()
    assert report.ok


# ---------------------------------------------------------------------------
# Phase tracking
# ---------------------------------------------------------------------------

def test_phase_transitions():
    mgr = _mgr(dry_run=True)
    assert mgr.phase == ShutdownPhase.PENDING
    mgr.register(ShutdownModule(name="a"))
    mgr.shutdown()
    assert mgr.phase == ShutdownPhase.STOPPED


def test_phase_failed_on_error():
    mgr = _mgr(dry_run=False)
    mgr.register_hook("bad", lambda: (_ for _ in ()).throw(RuntimeError()))
    mgr.shutdown()
    assert mgr.phase == ShutdownPhase.FAILED


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def test_report_to_dict():
    mgr = _mgr(dry_run=True)
    mgr.register(ShutdownModule(name="a"))
    report = mgr.shutdown()
    d = report.to_dict()
    assert d["ok"] is True
    assert "results" in d
    assert "summary" in d
    assert d["summary"]["stopped"] == 1


def test_report_total_duration():
    mgr = _mgr(dry_run=True)
    mgr.register(ShutdownModule(name="a"))
    report = mgr.shutdown()
    assert report.total_duration_ms >= 0


def test_report_completed_at():
    mgr = _mgr(dry_run=True)
    report = mgr.shutdown()
    assert report.completed_at != ""


# ---------------------------------------------------------------------------
# History and stats
# ---------------------------------------------------------------------------

def test_history_recorded():
    mgr = _mgr(dry_run=True)
    mgr.register(ShutdownModule(name="a"))
    mgr.shutdown()
    mgr.shutdown()
    assert len(mgr.history()) == 2


def test_stats():
    mgr = _mgr(dry_run=True)
    mgr.register(ShutdownModule(name="a"))
    s = mgr.stats()
    assert s["registered"] == 1
    assert s["dry_run"] is True
    assert s["current_phase"] == "PENDING"

"""W168 — Tests for CockpitSnapshot & SnapshotBuilder."""
import json
import pytest
from src.kratos_bridge.snapshot import (
    CockpitSnapshot,
    SnapshotBuilder,
    SystemSection,
    TestSuiteSection,
    WaveProgressSection,
)


# ---------------------------------------------------------------------------
# WaveProgressSection
# ---------------------------------------------------------------------------

def test_wave_progress_defaults():
    s = WaveProgressSection()
    assert s.total_waves == 210
    assert s.pct == 0.0


def test_wave_progress_round_trip():
    s = WaveProgressSection(current_wave="W168", completed_waves=168, pct=80.0, current_group="G18")
    s2 = WaveProgressSection.from_dict(s.to_dict())
    assert s2.current_wave == "W168"
    assert s2.completed_waves == 168


# ---------------------------------------------------------------------------
# TestSuiteSection
# ---------------------------------------------------------------------------

def test_pass_rate_zero_total():
    s = TestSuiteSection()
    assert s.pass_rate == 0.0


def test_pass_rate_calculated():
    s = TestSuiteSection(total=200, passed=190)
    assert s.pass_rate == 95.0


def test_test_suite_round_trip():
    s = TestSuiteSection(total=100, passed=99, failed=1, skipped=0)
    s2 = TestSuiteSection.from_dict(s.to_dict())
    assert s2.passed == 99
    assert s2.pass_rate == 99.0


# ---------------------------------------------------------------------------
# SystemSection
# ---------------------------------------------------------------------------

def test_system_defaults():
    s = SystemSection()
    assert s.healthy is True
    assert s.dry_run is True


def test_system_round_trip():
    s = SystemSection(healthy=False, dry_run=True, active_modules=["a", "b"])
    s2 = SystemSection.from_dict(s.to_dict())
    assert not s2.healthy
    assert s2.active_modules == ["a", "b"]


# ---------------------------------------------------------------------------
# CockpitSnapshot
# ---------------------------------------------------------------------------

def test_snapshot_defaults():
    snap = CockpitSnapshot()
    assert snap.snapshot_id.startswith("snap_")
    assert snap.alerts == []


def test_snapshot_to_dict():
    snap = CockpitSnapshot()
    d = snap.to_dict()
    for key in ["snapshot_id", "wave_progress", "test_suite", "system", "alerts", "captured_at"]:
        assert key in d


def test_snapshot_round_trip_dict():
    snap = CockpitSnapshot(
        wave_progress=WaveProgressSection(current_wave="W168", completed_waves=168),
        test_suite=TestSuiteSection(total=500, passed=498),
    )
    snap2 = CockpitSnapshot.from_dict(snap.to_dict())
    assert snap2.wave_progress.current_wave == "W168"
    assert snap2.test_suite.passed == 498


def test_snapshot_json_round_trip():
    snap = CockpitSnapshot(system=SystemSection(healthy=True, dry_run=True))
    raw = snap.to_json()
    snap2 = CockpitSnapshot.from_json(raw)
    assert snap2.snapshot_id == snap.snapshot_id
    assert snap2.system.healthy is True


def test_snapshot_json_is_valid():
    snap = CockpitSnapshot()
    raw = snap.to_json()
    parsed = json.loads(raw)
    assert "snapshot_id" in parsed


def test_snapshot_unique_ids():
    s1 = CockpitSnapshot()
    s2 = CockpitSnapshot()
    assert s1.snapshot_id != s2.snapshot_id


# ---------------------------------------------------------------------------
# SnapshotBuilder
# ---------------------------------------------------------------------------

def test_builder_basic():
    b = SnapshotBuilder()
    snap = b.build(wave="W168", completed=168, tests_passed=500, tests_total=500)
    assert snap.wave_progress.current_wave == "W168"
    assert snap.wave_progress.pct == 80.0
    assert snap.test_suite.pass_rate == 100.0
    assert snap.system.dry_run is True


def test_builder_pct_calculation():
    b = SnapshotBuilder()
    snap = b.build(completed=105, total_waves=210)
    assert snap.wave_progress.pct == 50.0


def test_builder_pct_zero_total():
    b = SnapshotBuilder()
    snap = b.build(completed=5, total_waves=0)
    assert snap.wave_progress.pct == 0.0


def test_builder_latest():
    b = SnapshotBuilder()
    b.build(wave="W166")
    b.build(wave="W168")
    assert b.latest().wave_progress.current_wave == "W168"


def test_builder_latest_empty():
    b = SnapshotBuilder()
    assert b.latest() is None


def test_builder_history():
    b = SnapshotBuilder()
    b.build()
    b.build()
    assert len(b.history()) == 2


def test_builder_with_alerts():
    b = SnapshotBuilder()
    snap = b.build(alerts=[{"level": "HIGH", "message": "Disk full"}])
    assert len(snap.alerts) == 1


def test_builder_with_modules():
    b = SnapshotBuilder()
    snap = b.build(active_modules=["kratos_bridge", "remote_control"])
    assert "kratos_bridge" in snap.system.active_modules


def test_builder_healthy_flag():
    b = SnapshotBuilder()
    snap = b.build(healthy=False)
    assert not snap.system.healthy


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_builder_persists_to_dir(tmp_path):
    b = SnapshotBuilder(snapshot_dir=tmp_path)
    snap = b.build(wave="W168")
    saved = list(tmp_path.glob("*.json"))
    assert len(saved) == 1
    data = json.loads(saved[0].read_text())
    assert data["snapshot_id"] == snap.snapshot_id


def test_builder_multiple_snapshots_persisted(tmp_path):
    b = SnapshotBuilder(snapshot_dir=tmp_path)
    b.build(wave="W167")
    b.build(wave="W168")
    assert len(list(tmp_path.glob("*.json"))) == 2


def test_builder_no_persistence():
    b = SnapshotBuilder()
    snap = b.build(wave="W168")
    assert snap is not None  # no crash, no file written

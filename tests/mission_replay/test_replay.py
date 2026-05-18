"""Tests for mission replay engine."""

import tempfile
from pathlib import Path

import pytest

from src.mission_replay.replay import MissionReplay


@pytest.fixture
def fixture_missions_dir():
    """Create a minimal missions directory with two missions."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # Mission 1: full structure
        m1 = root / "MIS-001"
        m1.mkdir(parents=True)
        (m1 / "mission_contract.json").write_text(
            '{"mission_id": "MIS-001", "objetivo": "campanha nordeste", "status": "completed"}',
            encoding="utf-8")
        (m1 / "01_mission_brief.md").write_text("# Brief: Campanha Nordeste\n\nCriar carrossel para hoteis no nordeste.", encoding="utf-8")
        (m1 / "03_execution_plan.md").write_text("# Execution Plan\n\n1. Criar copy\n2. Criar design\n3. Exportar", encoding="utf-8")

        outputs1 = m1 / "05_outputs"
        outputs1.mkdir()
        (outputs1 / "carrossel.md").write_text("# Carrossel Nordeste\n\n10 slides.", encoding="utf-8")
        (outputs1 / "caption.txt").write_text("Descubra os melhores hoteis do nordeste!", encoding="utf-8")

        exports1 = m1 / "06_exports"
        exports1.mkdir()
        (exports1 / "final_package.zip").write_bytes(b"fake zip content")

        # Mission 2: sparse (minimal)
        m2 = root / "MIS-002"
        m2.mkdir(parents=True)
        (m2 / "mission_contract.json").write_text(
            '{"mission_id": "MIS-002", "objetivo": "reels instagram", "status": "open"}',
            encoding="utf-8")

        yield root


class TestMissionReplayList:
    def test_list_missions(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        missions = r.list_missions()
        assert len(missions) == 2
        assert "MIS-001" in missions
        assert "MIS-002" in missions

    def test_mission_exists(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        assert r.mission_exists("MIS-001")
        assert not r.mission_exists("MIS-999")


class TestMissionReplaySnapshot:
    def test_snapshot(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        snap = r.snapshot("MIS-001")
        assert snap["mission_id"] == "MIS-001"
        assert "contract" in snap
        assert "files" in snap
        assert len(snap["files"]) >= 4  # contract + brief + plan + 2 outputs + 1 export - wait, export
        # Actually: contract, brief, plan, carrossel.md, caption.txt, final_package.zip = 6

    def test_snapshot_files_have_hash(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        snap = r.snapshot("MIS-001")
        for f in snap["files"]:
            assert "hash" in f
            assert "size" in f
            assert len(f["hash"]) == 16  # SHA256[:16]

    def test_snapshot_missing_mission(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        with pytest.raises(FileNotFoundError):
            r.snapshot("MIS-999")


class TestMissionReplayCreate:
    def test_create_dry_run(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        session = r.create_replay("MIS-001", "v2", dry_run=True)
        assert session.session_id == "REPLAY-MIS-001-v2"
        assert session.status == "created"
        assert session.replay_path is None

    def test_create_with_variant(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        session = r.create_replay(
            "MIS-001", "Brotas",
            variant_changes={"objetivo": "hoteis Brotas SP"},
            dry_run=True,
        )
        assert session.variant_name == "Brotas"
        assert session.variant_changes == {"objetivo": "hoteis Brotas SP"}

    def test_create_missing_mission(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        with pytest.raises(FileNotFoundError):
            r.create_replay("MIS-999", "v2", dry_run=True)

    def test_create_execute(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        session = r.create_replay("MIS-001", "v3", dry_run=False)
        assert session.status == "completed"
        assert session.replay_path is not None
        assert Path(session.replay_path).is_dir()


class TestMissionReplayDiff:
    def test_diff_dry_run_no_changes(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        session = r.create_replay("MIS-001", "v2", dry_run=True)
        report = r.diff(session.session_id)
        assert report.original_mission_id == "MIS-001"
        assert not report.has_changes

    def test_diff_execute_detects_modified(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        session = r.create_replay(
            "MIS-001", "Brotas",
            variant_changes={"objetivo": "hoteis Brotas SP"},
            dry_run=False,
        )
        report = r.diff(session.session_id)
        assert report.total_files > 0
        # mission_contract.json should be modified
        modified = [e for e in report.entries if e.change_type == "modified"]
        assert len(modified) >= 1
        assert any("mission_contract.json" in e.file_path for e in modified)

    def test_diff_missing_session(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        with pytest.raises(FileNotFoundError):
            r.diff("REPLAY-nonexistent")


class TestMissionReplaySessions:
    def test_list_sessions_empty(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        sessions = r.list_sessions()
        assert sessions == []

    def test_list_sessions_after_replay(self, fixture_missions_dir):
        r = MissionReplay(missions_dir=fixture_missions_dir)
        r.create_replay("MIS-001", "v2", dry_run=False)
        sessions = r.list_sessions()
        assert len(sessions) >= 1

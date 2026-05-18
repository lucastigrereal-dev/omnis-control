"""Tests for mission replay models."""

from src.mission_replay.models import ReplaySession, DiffReport, DiffEntry


class TestReplaySession:
    def test_construction(self):
        s = ReplaySession(
            session_id="REPLAY-MIS-001-v2",
            original_mission_id="MIS-001",
            variant_name="v2",
        )
        assert s.session_id == "REPLAY-MIS-001-v2"
        assert s.original_mission_id == "MIS-001"
        assert s.variant_name == "v2"
        assert s.status == "created"
        assert s.variant_changes == {}

    def test_with_changes(self):
        s = ReplaySession(
            session_id="R1",
            original_mission_id="M1",
            variant_name="Brotas",
            variant_changes={"objetivo": "hoteis Brotas", "setor": "marketing"},
        )
        assert s.variant_changes["objetivo"] == "hoteis Brotas"
        assert len(s.variant_changes) == 2

    def test_to_dict_roundtrip(self):
        s = ReplaySession(
            session_id="R1",
            original_mission_id="M1",
            variant_name="v2",
            variant_changes={"key": "val"},
            status="completed",
            output_count=5,
        )
        d = s.to_dict()
        restored = ReplaySession.from_dict(d)
        assert restored.session_id == s.session_id
        assert restored.variant_name == s.variant_name
        assert restored.output_count == 5


class TestDiffEntry:
    def test_added(self):
        e = DiffEntry(file_path="new_file.md", change_type="added", replay_size=100)
        assert e.change_type == "added"
        assert e.replay_size == 100

    def test_modified(self):
        e = DiffEntry(
            file_path="contract.json",
            change_type="modified",
            original_size=50,
            replay_size=55,
            summary="Size: 50 → 55 bytes",
        )
        assert e.change_type == "modified"
        assert e.summary == "Size: 50 → 55 bytes"


class TestDiffReport:
    def test_empty(self):
        r = DiffReport(session_id="R1", original_mission_id="M1", variant_name="v2")
        assert r.total_files == 0
        assert not r.has_changes

    def test_with_changes(self):
        r = DiffReport(
            session_id="R1",
            original_mission_id="M1",
            variant_name="v2",
            files_modified=3,
            files_added=1,
            files_unchanged=10,
        )
        assert r.has_changes
        assert r.total_files == 0  # explicit, not computed

    def test_to_dict(self):
        r = DiffReport(
            session_id="R1",
            original_mission_id="M1",
            variant_name="v2",
            entries=[DiffEntry(file_path="f.md", change_type="modified")],
            total_files=1,
            files_modified=1,
        )
        d = r.to_dict()
        assert d["session_id"] == "R1"
        assert len(d["entries"]) == 1
        assert d["entries"][0]["file_path"] == "f.md"

    def test_from_dict(self):
        d = {
            "session_id": "R1",
            "original_mission_id": "M1",
            "variant_name": "v2",
            "entries": [{"file_path": "f.md", "change_type": "added", "replay_size": 42}],
            "total_files": 1,
            "files_added": 1,
            "files_removed": 0,
            "files_modified": 0,
            "files_unchanged": 0,
            "total_lines_added": 0,
            "total_lines_removed": 0,
            "generated_at": "2026-05-18T00:00:00Z",
        }
        r = DiffReport.from_dict(d)
        assert r.total_files == 1
        assert len(r.entries) == 1
        assert r.entries[0].change_type == "added"

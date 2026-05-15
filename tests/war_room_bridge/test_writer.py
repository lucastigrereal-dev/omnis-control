import pytest
from pathlib import Path

from src.war_room_bridge.writer import WarRoomWriter
from src.war_room_bridge.models import WarRoomReport
from src.war_room_bridge.errors import ForbiddenPathError


class TestWarRoomWriter:
    def test_dry_run_does_not_write(self, tmp_path):
        writer = WarRoomWriter(str(tmp_path), dry_run=True)
        report = WarRoomReport(
            order_id="wro_test",
            title="Test",
            status="COMPLETED",
            summary="ok",
        )
        path = writer.write_report(report)
        assert path.endswith(".md")
        assert not Path(path).exists()

    def test_real_write_creates_file(self, tmp_path):
        writer = WarRoomWriter(str(tmp_path), dry_run=False)
        report = WarRoomReport(
            order_id="wro_test",
            title="Real Write",
            status="COMPLETED",
            summary="Written to disk.",
            tests_run=5,
            tests_passed=5,
        )
        path = writer.write_report(report)
        assert Path(path).exists()
        content = Path(path).read_text(encoding="utf-8")
        assert "# War Room Report: Real Write" in content
        assert "Written to disk." in content
        assert "- Run: 5" in content

    def test_writes_multiple_reports(self, tmp_path):
        writer = WarRoomWriter(str(tmp_path), dry_run=False)
        for i in range(3):
            report = WarRoomReport(
                title=f"Report {i}",
                status="COMPLETED",
                summary=f"Summary {i}",
            )
            writer.write_report(report)
        files = list(tmp_path.glob("*.md"))
        assert len(files) == 3

    def test_blocks_forbidden_status_dir(self, tmp_path):
        forbidden = tmp_path / "status"
        forbidden.mkdir()
        writer = WarRoomWriter(str(forbidden), dry_run=False)
        report = WarRoomReport(title="X", status="X", summary="x")
        with pytest.raises(ForbiddenPathError):
            writer.write_report(report)

    def test_blocks_forbidden_canon_dir(self, tmp_path):
        forbidden = tmp_path / "canon"
        forbidden.mkdir()
        writer = WarRoomWriter(str(forbidden), dry_run=False)
        report = WarRoomReport(title="X", status="X", summary="x")
        with pytest.raises(ForbiddenPathError):
            writer.write_report(report)

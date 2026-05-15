from pathlib import Path

from src.war_room_bridge.models import WarRoomReport
from src.war_room_bridge.errors import ReportWriteError, ForbiddenPathError

FORBIDDEN_DIRS = {"status", "canon"}


class WarRoomWriter:
    def __init__(self, reports_dir: str, dry_run: bool = True):
        self.reports_dir = Path(reports_dir)
        self.dry_run = dry_run

    def write_report(self, report: WarRoomReport) -> str:
        self._validate_path()
        if self.dry_run:
            return str(self.reports_dir / f"{report.report_id}.md")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.reports_dir / f"{report.report_id}.md"
        markdown = report.to_markdown()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        return str(output_path)

    def _validate_path(self) -> None:
        resolved = self.reports_dir.resolve()
        for forbidden in FORBIDDEN_DIRS:
            forbidden_path = resolved.parent / forbidden
            if str(resolved).startswith(str(forbidden_path)):
                raise ForbiddenPathError(str(resolved))

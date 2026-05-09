"""Mission Report Service — close a mission package and record outcome.

NUNCA publica. NUNCA chama Meta. NUNCA aciona OAuth.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.mission_report.models import MissionReport
from src.mission_report.errors import (
    MissionNotFoundError,
    MissionReportError,
    InvalidOutcomeError,
)

BASE = Path(__file__).resolve().parent.parent.parent
PACKAGES_ROOT = BASE / "exports" / "mission_packages"
REPORTS_LOG = BASE / "data" / "mission_reports.jsonl"

VALID_OUTCOMES = {"completed", "cancelled", "deferred"}


def close_mission(
    mission_id: str,
    outcome: str,
    notes: str = "",
    published_url: str = "",
    packages_root: Path = PACKAGES_ROOT,
    reports_log: Path = REPORTS_LOG,
) -> MissionReport:
    """Close a mission: write report file + append to log.

    Args:
        mission_id: ID of mission to close (must have existing package).
        outcome: 'completed' | 'cancelled' | 'deferred'
        notes: Free-text outcome notes.
        published_url: URL of published post (if any).

    Returns:
        MissionReport

    Raises:
        MissionNotFoundError: Package dir doesn't exist.
        InvalidOutcomeError: outcome not in VALID_OUTCOMES.
    """
    if outcome not in VALID_OUTCOMES:
        raise InvalidOutcomeError(
            f"Outcome '{outcome}' invalido. Use: {sorted(VALID_OUTCOMES)}"
        )

    pkg_dir = packages_root / mission_id
    if not pkg_dir.is_dir():
        raise MissionNotFoundError(
            f"Mission package nao encontrado: {pkg_dir}"
        )

    manifest_path = pkg_dir / "mission_manifest.json"
    if not manifest_path.exists():
        raise MissionNotFoundError(
            f"mission_manifest.json ausente em: {pkg_dir}"
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    intent = manifest.get("intent", "unknown")
    account_handle = manifest.get("account_handle", "unknown")

    report = MissionReport.new(
        mission_id=mission_id,
        intent=intent,
        account_handle=account_handle,
        outcome=outcome,
        notes=notes,
        published_url=published_url,
    )

    _write_report_file(pkg_dir, report, manifest)
    _append_report(report, reports_log)
    return report


def get_report(mission_id: str, reports_log: Path = REPORTS_LOG) -> Optional[MissionReport]:
    """Return the most recent report for a mission_id, or None."""
    if not reports_log.exists():
        return None
    found = None
    for line in reports_log.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get("mission_id") == mission_id:
                found = MissionReport.from_dict(data)
        except json.JSONDecodeError:
            continue
    return found


def list_reports(reports_log: Path = REPORTS_LOG) -> list[MissionReport]:
    """Return all mission reports, newest first."""
    if not reports_log.exists():
        return []
    reports = []
    for line in reports_log.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            reports.append(MissionReport.from_dict(json.loads(line)))
        except (json.JSONDecodeError, TypeError):
            continue
    return list(reversed(reports))


def _write_report_file(pkg_dir: Path, report: MissionReport, manifest: dict) -> None:
    content = _build_report_md(report, manifest)
    try:
        (pkg_dir / "07_mission_report.md").write_text(content, encoding="utf-8")
    except Exception as exc:
        raise MissionReportError(f"Cannot write report file: {exc}") from exc


def _append_report(report: MissionReport, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(report.to_dict(), ensure_ascii=False) + "\n")


def _build_report_md(report: MissionReport, manifest: dict) -> str:
    url_line = f"**URL publicado:** {report.published_url}" if report.published_url else "**URL publicado:** —"
    notes_section = report.notes or "(sem notas)"
    return f"""# Mission Report — {report.mission_id}

**Status:** {report.outcome.upper()}
**Missão:** {report.mission_id}
**Intent:** {report.intent}
**Conta:** @{report.account_handle}
**Fechado em:** {report.closed_at}
{url_line}

---

## Notas de fechamento

{notes_section}

---

## Entregável original

- **Pedido:** {manifest.get("request_text", "—")}
- **Entregável:** {manifest.get("deliverable", "—")}
- **Criado em:** {manifest.get("created_at", "—")}

---

> NUNCA publicar sem aprovacao humana.
> OAuth gate: congelado ate 5 READY validados.
"""

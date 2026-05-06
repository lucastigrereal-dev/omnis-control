"""Export creative packages — produces files for the creative team."""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import CreativeBrief
from .briefs import get_brief

BASE = Path(__file__).resolve().parent.parent.parent
EXPORT_DIR = BASE / "data" / "exports" / "creative_packages"


def _safe_write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def export_package(brief_id: str) -> Optional[Path]:
    """Export a creative brief as a full creative package (files on disk)."""
    brief = get_brief(brief_id)
    if not brief:
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_dir = EXPORT_DIR / f"{brief.queue_id}_{ts}"
    package_dir.mkdir(parents=True, exist_ok=True)

    _safe_write(package_dir / "brief.md", (
        f"# Creative Brief: {brief.creative_brief_id}\n\n"
        f"**Queue:** {brief.queue_id}\n"
        f"**Account:** {brief.account_handle}\n"
        f"**Format:** {brief.format}\n"
        f"**Objective:** {brief.objective}\n"
        f"**Visual Direction:** {brief.visual_direction}\n"
        f"**Status:** {brief.status}\n"
        f"**Created:** {brief.created_at}\n"
    ))

    _safe_write(package_dir / "caption.txt", brief.script)

    _safe_write(package_dir / "hashtags.txt", "# TODO: extract from SEOgram caption")

    _safe_write(package_dir / "script.md", brief.script or "# Script\n\n(No script provided)")

    _safe_write(package_dir / "shot_list.md", brief.shot_list or "# Shot List\n\n(No shot list provided)")

    _safe_write(package_dir / "design_notes.md", brief.design_notes or "# Design Notes\n\n(No design notes provided)")

    _safe_write(package_dir / "editing_notes.md", brief.editing_notes or "# Editing Notes\n\n(No editing notes provided)")

    _safe_write(package_dir / "asset_requirements.json",
                json.dumps(brief.asset_requirements, indent=2, ensure_ascii=False))

    _safe_write(package_dir / "tool_suggestions.md",
                "\n".join(f"- {t}" for t in (brief.tool_suggestions or ["manual"])))

    _safe_write(package_dir / "production_checklist.md", (
        "# Production Checklist\n\n"
        "- [ ] Assets gathered\n"
        "- [ ] Design brief reviewed\n"
        "- [ ] Editing notes followed\n"
        "- [ ] Review requested\n"
        "- [ ] Final approval\n"
    ))

    return package_dir


def list_packages() -> list:
    """List exported packages on disk."""
    if not EXPORT_DIR.exists():
        return []
    packages = []
    for d in sorted(EXPORT_DIR.iterdir()):
        if d.is_dir():
            files = [f.name for f in d.iterdir()]
            packages.append({
                "path": str(d),
                "name": d.name,
                "files": files,
                "file_count": len(files),
            })
    return packages

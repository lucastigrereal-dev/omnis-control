"""Export creative packages — produces up to 13 files for the creative team.

Generates:
  - 10 textual files (.md, .txt, .json)
  - 1 HTML preview (preview.html)
  - 1 mock image (mock_image.png via Pillow)
  - 1 WARNINGS.md (if fields are missing)

NEVER calls external APIs. NEVER publishes anywhere.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import CreativeBrief
from .briefs import get_brief
from .html_renderer import render_preview_html
from .mock_image_generator import generate_mock_image

BASE = Path(__file__).resolve().parent.parent.parent
EXPORT_DIR = BASE / "data" / "exports" / "creative_packages"

REQUIRED_FIELDS = [
    ("script", "caption.txt", "Legenda"),
    ("shot_list", "shot_list.md", "Shot list / lista de cenas"),
    ("design_notes", "design_notes.md", "Notas de design"),
    ("editing_notes", "editing_notes.md", "Notas de edição"),
    ("asset_requirements", "asset_requirements.json", "Requisitos de asset"),
]


@dataclass
class ExportPackageResult:
    """Result of an export package generation."""
    package_id: str
    package_path: Path
    files_generated: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    success: bool = True


def _safe_write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_export_package(
    brief_id: str,
    output_dir: Path = EXPORT_DIR,
    include_html: bool = True,
    include_mock_image: bool = True,
) -> Optional[ExportPackageResult]:
    """Generate a complete export package for a creative brief.

    Args:
        brief_id: ID of the creative brief to export.
        output_dir: Root output directory for packages.
        include_html: Generate preview.html.
        include_mock_image: Generate mock_image.png.

    Returns:
        ExportPackageResult or None if brief not found.

    NEVER calls external APIs. NEVER publishes anywhere.
    NEVER mutates brief or queue state.
    """
    brief = get_brief(brief_id)
    if not brief:
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_id = f"brief_{brief.creative_brief_id}_{ts}"
    package_dir = output_dir / package_id
    package_dir.mkdir(parents=True, exist_ok=True)

    warnings = []
    files_generated = []

    # Detect missing fields
    for field_name, filename, label in REQUIRED_FIELDS:
        value = getattr(brief, field_name, None)
        if not value or (isinstance(value, (dict, list)) and not value):
            warnings.append(f"{label} ausente — arquivo gerado com placeholder")

    if not brief.tool_suggestions:
        warnings.append("Tool suggestions vazias — usando fallback 'manual'")

    # 1. brief.md
    _safe_write(package_dir / "brief.md", (
        f"# Creative Brief: {brief.creative_brief_id}\n\n"
        f"**Queue:** {brief.queue_id}\n"
        f"**Account:** {brief.account_handle}\n"
        f"**Format:** {brief.format}\n"
        f"**Objective:** {brief.objective}\n"
        f"**Visual Direction:** {brief.visual_direction}\n"
        f"**Status:** {brief.status}\n"
        f"**Created:** {brief.created_at}\n"
        f"**Updated:** {brief.updated_at}\n"
    ))
    files_generated.append("brief.md")

    # 2. caption.txt
    caption = brief.script or "(Conteúdo da legenda não disponível)"
    _safe_write(package_dir / "caption.txt", caption)
    files_generated.append("caption.txt")

    # 3. hashtags.txt
    _safe_write(package_dir / "hashtags.txt",
                _extract_hashtags_text(brief.script))
    files_generated.append("hashtags.txt")

    # 4. script.md
    _safe_write(package_dir / "script.md",
                brief.script or "# Script\n\n(No script provided)")
    files_generated.append("script.md")

    # 5. shot_list.md
    _safe_write(package_dir / "shot_list.md",
                brief.shot_list or "# Shot List\n\n(No shot list provided)")
    files_generated.append("shot_list.md")

    # 6. design_notes.md
    _safe_write(package_dir / "design_notes.md",
                brief.design_notes or "# Design Notes\n\n(No design notes provided)")
    files_generated.append("design_notes.md")

    # 7. editing_notes.md
    _safe_write(package_dir / "editing_notes.md",
                brief.editing_notes or "# Editing Notes\n\n(No editing notes provided)")
    files_generated.append("editing_notes.md")

    # 8. asset_requirements.json
    _safe_write(package_dir / "asset_requirements.json",
                json.dumps(brief.asset_requirements or {}, indent=2, ensure_ascii=False))
    files_generated.append("asset_requirements.json")

    # 9. tool_suggestions.md
    tools = brief.tool_suggestions or ["manual"]
    _safe_write(package_dir / "tool_suggestions.md",
                "\n".join(f"- {t}" for t in tools))
    files_generated.append("tool_suggestions.md")

    # 10. production_checklist.md
    checklist_items = [
        "[ ] Assets gathered",
        "[ ] Design brief reviewed",
        "[ ] Editing notes followed",
        "[ ] Review requested",
        "[ ] Final approval",
    ]
    if warnings:
        checklist_items.insert(0, f"[ ] {len(warnings)} warnings reviewed (see WARNINGS.md)")
    _safe_write(package_dir / "production_checklist.md",
                "# Production Checklist\n\n" + "\n".join(f"- {item}" for item in checklist_items))
    files_generated.append("production_checklist.md")

    # 11. preview.html (optional)
    if include_html:
        try:
            mock_path = package_dir / "mock_image.png"
            html = render_preview_html(brief, package_id, mock_path if mock_path.exists() else None)
            _safe_write(package_dir / "preview.html", html)
            files_generated.append("preview.html")
        except Exception as e:
            warnings.append(f"preview.html generation failed: {e}")

    # 12. mock_image.png (optional)
    if include_mock_image:
        try:
            generate_mock_image(brief, package_dir / "mock_image.png", package_id)
            files_generated.append("mock_image.png")
        except Exception as e:
            warnings.append(f"mock_image.png generation failed: {e}")

    # 13. WARNINGS.md (only if warnings exist)
    if warnings:
        warnings_md = "# Warnings\n\n"
        warnings_md += f"**Package:** {package_id}\n\n"
        warnings_md += "## Issues Found\n\n"
        for i, w in enumerate(warnings, 1):
            warnings_md += f"{i}. {w}\n"
        _safe_write(package_dir / "WARNINGS.md", warnings_md)
        files_generated.append("WARNINGS.md")

    return ExportPackageResult(
        package_id=package_id,
        package_path=package_dir,
        files_generated=files_generated,
        warnings=warnings,
        success=True,
    )


def export_package(brief_id: str) -> Optional[Path]:
    """Backward-compatible wrapper — calls generate_export_package.

    Returns the package Path or None if brief not found.
    """
    result = generate_export_package(brief_id)
    return result.package_path if result else None


def list_packages() -> list:
    """List exported packages on disk."""
    if not EXPORT_DIR.exists():
        return []
    packages = []
    for d in sorted(EXPORT_DIR.iterdir()):
        if d.is_dir():
            files = [f.name for f in d.iterdir()]
            has_warnings = "WARNINGS.md" in files
            packages.append({
                "path": str(d),
                "name": d.name,
                "files": files,
                "file_count": len(files),
                "has_warnings": has_warnings,
            })
    return packages


def _extract_hashtags_text(text: str) -> str:
    """Extract hashtags from text into a hashtag-per-line format."""
    if not text:
        return "# TODO: extract from SEOgram caption"
    hashtags = [word for word in text.split() if word.startswith("#")]
    if not hashtags:
        return "# TODO: extract from SEOgram caption"
    return "\n".join(hashtags)

"""Render engine service — orchestrates HTML generation for packages."""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.render_engine.errors import PackageNotFoundError, RenderFailedError
from src.render_engine.html_renderer import render_html
from src.render_engine.models import RenderResult, RenderStatus

EXPORT_ROOT = Path("exports/offline_factory")
RENDER_ROOT = Path("exports/rendered")


def _find_package_dir(package_id: str, export_root: Path = EXPORT_ROOT) -> Optional[Path]:
    if not export_root.exists():
        return None
    for d in export_root.iterdir():
        if d.is_dir() and d.name.startswith(package_id):
            return d
    return None


def render_package(
    package_id: str,
    export_root: Path = EXPORT_ROOT,
    render_root: Path = RENDER_ROOT,
) -> RenderResult:
    pkg_dir = _find_package_dir(package_id, export_root)
    if not pkg_dir:
        raise PackageNotFoundError(f"Package '{package_id}' not found in {export_root}")

    render_id = f"render_{uuid.uuid4().hex[:8]}"
    out_dir = render_root / pkg_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)

    warnings = []
    errors = []
    files_generated = []

    try:
        html_content = render_html(pkg_dir)
        html_path = out_dir / "preview.html"
        html_path.write_text(html_content, encoding="utf-8")
        files_generated.append("preview.html")
    except Exception as exc:
        errors.append(f"HTML generation failed: {exc}")
        return RenderResult(
            render_id=render_id,
            package_id=pkg_dir.name,
            status=RenderStatus.FAILED,
            errors=errors,
        )

    manifest = {
        "render_id": render_id,
        "package_id": pkg_dir.name,
        "source_package_dir": str(pkg_dir),
        "html_path": str(html_path),
        "status": "ok",
        "rendered_at": datetime.now(timezone.utc).isoformat(),
        "files": files_generated,
    }
    manifest_path = out_dir / "render_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    files_generated.append("render_manifest.json")

    return RenderResult(
        render_id=render_id,
        package_id=pkg_dir.name,
        status=RenderStatus.OK,
        html_path=str(html_path),
        render_manifest_path=str(manifest_path),
        files_generated=files_generated,
        warnings=warnings,
        errors=errors,
    )


def list_renders(render_root: Path = RENDER_ROOT) -> list[dict]:
    if not render_root.exists():
        return []
    results = []
    for d in render_root.iterdir():
        if not d.is_dir():
            continue
        manifest_path = d / "render_manifest.json"
        if not manifest_path.exists():
            continue
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            results.append(data)
        except Exception:
            continue
    return results


def get_render(render_id_prefix: str, render_root: Path = RENDER_ROOT) -> Optional[dict]:
    for entry in list_renders(render_root):
        if entry.get("render_id", "").startswith(render_id_prefix):
            return entry
    return None

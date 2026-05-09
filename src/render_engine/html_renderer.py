"""HTML renderer — generates local preview HTML from package files."""
from pathlib import Path
from typing import Optional


_CSS = """
body{font-family:sans-serif;max-width:720px;margin:40px auto;padding:0 20px;background:#f9f9f9;color:#222}
h1{font-size:1.4em;border-bottom:2px solid #e76f00;padding-bottom:8px;color:#e76f00}
h2{font-size:1.1em;margin-top:24px;color:#333}
pre{background:#fff;border:1px solid #ddd;padding:12px;border-radius:4px;white-space:pre-wrap;word-break:break-word}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:.8em;font-weight:bold}
.badge-ready{background:#d4edda;color:#155724}
.badge-partial{background:#fff3cd;color:#856404}
.badge-blocked{background:#f8d7da;color:#721c24}
.badge-exported{background:#cce5ff;color:#004085}
.meta{font-size:.85em;color:#666;margin-bottom:16px}
.section{background:#fff;border:1px solid #e0e0e0;border-radius:6px;padding:16px;margin-bottom:16px}
"""


def _badge(status: str) -> str:
    cls = {"ready": "badge-ready", "partial": "badge-partial",
           "blocked": "badge-blocked", "exported": "badge-exported"}.get(status.lower(), "badge-partial")
    return f'<span class="badge {cls}">{status.upper()}</span>'


def _read_file(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def render_html(package_dir: Path) -> str:
    """Generate HTML string for a package directory."""
    manifest_path = package_dir / "manifest.json"
    caption_path = package_dir / "caption.md"
    slides_path = package_dir / "slides_outline.md"
    script_path = package_dir / "script.md"
    checklist_path = package_dir / "publishing_checklist.md"

    import json
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    pkg_id = manifest.get("package_id", package_dir.name)
    pkg_type = manifest.get("package_type", "unknown")
    status = manifest.get("status", "unknown")
    account = manifest.get("account_handle", "")
    created = manifest.get("created_at", "")

    sections = []

    caption_text = _read_file(caption_path)
    if caption_text:
        sections.append(f'<div class="section"><h2>Caption</h2><pre>{_escape(caption_text)}</pre></div>')

    slides_text = _read_file(slides_path)
    if slides_text:
        sections.append(f'<div class="section"><h2>Slides Outline</h2><pre>{_escape(slides_text)}</pre></div>')

    script_text = _read_file(script_path)
    if script_text:
        sections.append(f'<div class="section"><h2>Script</h2><pre>{_escape(script_text)}</pre></div>')

    checklist_text = _read_file(checklist_path)
    if checklist_text:
        sections.append(f'<div class="section"><h2>Publishing Checklist</h2><pre>{_escape(checklist_text)}</pre></div>')

    body = "\n".join(sections) or "<p>No content files found.</p>"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OMNIS Preview — {_escape(pkg_id)}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>OMNIS Package Preview</h1>
<p class="meta">
  <strong>ID:</strong> {_escape(pkg_id)} &nbsp;|&nbsp;
  <strong>Tipo:</strong> {_escape(pkg_type)} &nbsp;|&nbsp;
  <strong>Conta:</strong> {_escape(account)} &nbsp;|&nbsp;
  <strong>Criado:</strong> {_escape(created)} &nbsp;
  {_badge(status)}
</p>
{body}
</body>
</html>"""


def _escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))

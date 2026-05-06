"""HTML preview renderer for creative export packages."""
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import CreativeBrief

TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Preview — {account_handle}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; display: flex; justify-content: center; padding: 20px; }}
.card {{ max-width: 480px; width: 100%; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.12); }}
.header {{ display: flex; align-items: center; padding: 14px 16px; }}
.avatar {{ width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #833ab4, #fd1d1d, #fcb045); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px; margin-right: 10px; }}
.header-text {{ flex: 1; }}
.header-text .name {{ font-weight: 600; font-size: 14px; }}
.header-text .meta {{ font-size: 11px; color: #8e8e8e; }}
.image-placeholder {{ width: 100%; aspect-ratio: 1/1; background: linear-gradient(135deg, #1a1a2e, #16213e); display: flex; align-items: center; justify-content: center; color: white; font-size: 18px; text-align: center; padding: 20px; position: relative; overflow: hidden; }}
.image-placeholder .watermark {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-30deg); font-size: 14px; color: rgba(255,255,255,0.15); white-space: nowrap; font-weight: bold; letter-spacing: 2px; }}
.image-placeholder img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
.caption {{ padding: 12px 16px; font-size: 14px; line-height: 1.5; }}
.caption .username {{ font-weight: 600; margin-right: 6px; }}
.caption .hashtags {{ color: #00376b; margin-top: 6px; }}
.footer {{ padding: 10px 16px; border-top: 1px solid #efefef; font-size: 11px; color: #8e8e8e; }}
.footer .meta-item {{ margin-bottom: 2px; }}
</style>
</head>
<body>
<div class="card">
<div class="header">
<div class="avatar">{avatar_letter}</div>
<div class="header-text">
<div class="name">{account_handle}</div>
<div class="meta">{format} &middot; {objective}</div>
</div>
</div>
<div class="image-placeholder">
<img src="{image_src}" alt="Post preview">
<div class="watermark">MOCK PREVIEW — NOT FOR PUBLISHING</div>
</div>
<div class="caption">
<span class="username">{account_handle}</span>
{caption_html}
<div class="hashtags">{hashtags_html}</div>
</div>
<div class="footer">
<div class="meta-item"><strong>Brief:</strong> {brief_id}</div>
<div class="meta-item"><strong>Package:</strong> {package_id}</div>
<div class="meta-item"><strong>Gerado em:</strong> {generated_at}</div>
</div>
</div>
</body>
</html>"""


def render_preview_html(
    brief: CreativeBrief,
    package_id: str,
    image_path: Optional[Path] = None,
) -> str:
    """Render HTML preview for a creative brief.

    Returns self-contained HTML string (no external dependencies).
    NEVER calls external APIs.
    """
    account = brief.account_handle or "@conta"
    avatar_letter = account[1].upper() if len(account) > 1 else "?"

    caption_text = brief.script or "(Conteúdo da legenda não disponível)"
    caption_html = _text_to_html(caption_text)

    hashtags = _extract_hashtags(caption_text)
    hashtags_html = " ".join(hashtags) if hashtags else "(Sem hashtags)"

    image_src = image_path.name if image_path else ""
    if not image_src:
        image_src = "mock_image.png"

    return TEMPLATE.format(
        account_handle=account,
        avatar_letter=avatar_letter,
        format=brief.format.capitalize() if brief.format else "Post",
        objective=brief.objective.capitalize() if brief.objective else "—",
        image_src=image_src,
        caption_html=caption_html,
        hashtags_html=hashtags_html,
        brief_id=brief.creative_brief_id,
        package_id=package_id,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )


def _text_to_html(text: str) -> str:
    """Convert plain text to safe HTML paragraphs."""
    import html as html_mod
    safe = html_mod.escape(text)
    paragraphs = [f"<p>{p.strip()}</p>" for p in safe.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [f"<p>{safe}</p>"]
    return "\n".join(paragraphs)


def _extract_hashtags(text: str) -> list:
    """Extract hashtags from text, preserving # symbol."""
    if not text:
        return []
    return [f"#{tag}" for tag in text.split() if tag.startswith("#")]

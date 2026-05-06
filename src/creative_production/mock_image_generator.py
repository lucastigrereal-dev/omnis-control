"""Mock image generator for creative export packages.

Generates a placeholder 1080x1080 PNG image using Pillow only.
NEVER calls external APIs. NEVER downloads images from the internet.
"""
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from .models import CreativeBrief

CANVAS_SIZE = (1080, 1080)
BG_TOP = "#1a1a2e"
BG_BOTTOM = "#16213e"
WATERMARK_TEXT = "MOCK PREVIEW — NOT FOR PUBLISHING"
WATERMARK_OPACITY = 100  # out of 255


def generate_mock_image(
    brief: CreativeBrief,
    output_path: Path,
    package_id: str,
) -> Path:
    """Generate a 1080x1080 placeholder PNG image.

    Uses ONLY Pillow for generation. No external APIs.

    Returns the output Path.
    """
    img = Image.new("RGB", CANVAS_SIZE, BG_TOP)
    draw = ImageDraw.Draw(img)

    # Gradient background
    _draw_gradient(draw, img.size, BG_TOP, BG_BOTTOM)

    # Try to load a font, fall back to default
    font_large = _get_font(48)
    font_small = _get_font(20)
    font_watermark = _get_font(28)

    # Main text: first 60 chars of caption
    caption = brief.script or "MOCK PREVIEW"
    display_text = caption[:60] + ("..." if len(caption) > 60 else "")
    lines = _wrap_text(display_text, font_large, 900)
    y_start = 400
    for line in lines:
        text_bbox = draw.textbbox((0, 0), line, font=font_large)
        text_w = text_bbox[2] - text_bbox[0]
        draw.text(
            ((CANVAS_SIZE[0] - text_w) // 2, y_start),
            line,
            fill="white",
            font=font_large,
        )
        y_start += text_bbox[3] - text_bbox[1] + 10

    # Subtitle: account handle + format
    subtitle = f"{brief.account_handle or '@conta'} · {brief.format or 'post'}"
    sub_bbox = draw.textbbox((0, 0), subtitle, font=font_small)
    draw.text(
        ((CANVAS_SIZE[0] - (sub_bbox[2] - sub_bbox[0])) // 2, y_start + 20),
        subtitle,
        fill="#a0a0a0",
        font=font_small,
    )

    # Watermark (diagonal, 40% opacity)
    _draw_watermark(draw, img.size, font_watermark)

    # Footer: package_id
    draw.text(
        (16, CANVAS_SIZE[1] - 40),
        package_id,
        fill=(255, 255, 255, 60),
        font=font_small,
    )

    img.save(output_path, "PNG")
    return output_path


def _draw_gradient(draw, size: tuple, color_top: str, color_bottom: str):
    """Draw vertical gradient background."""
    width, height = size
    top_rgb = _hex_to_rgb(color_top)
    bot_rgb = _hex_to_rgb(color_bottom)
    for y in range(height):
        ratio = y / height
        r = int(top_rgb[0] * (1 - ratio) + bot_rgb[0] * ratio)
        g = int(top_rgb[1] * (1 - ratio) + bot_rgb[1] * ratio)
        b = int(top_rgb[2] * (1 - ratio) + bot_rgb[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def _draw_watermark(draw, size: tuple, font):
    """Draw diagonal watermark text at 40% opacity."""
    from PIL import ImageFont

    width, height = size
    alpha_img = Image.new("RGBA", size, (0, 0, 0, 0))
    alpha_draw = ImageDraw.Draw(alpha_img)

    bbox = alpha_draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    cx = width // 2 - tw // 2
    cy = height // 2 - th // 2

    alpha_draw.text((cx, cy), WATERMARK_TEXT, fill=(255, 255, 255, WATERMARK_OPACITY), font=font)
    rotated = alpha_img.rotate(-30, expand=False, center=(width // 2, height // 2))
    img_rgba = Image.new("RGBA", size, (0, 0, 0, 0))
    img_rgba.paste(rotated, (0, 0), rotated)
    base = Image.new("RGBA", size, (0, 0, 0, 0))
    draw._image.paste(img_rgba, (0, 0), img_rgba)


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _get_font(size: int):
    """Try to load a TTF font, fall back to default bitmap."""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except (IOError, OSError):
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except (IOError, OSError):
            return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int) -> list:
    """Wrap text to fit within max_width pixels."""
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            continue
        words = paragraph.split()
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox(
                (0, 0), test_line, font=font
            )
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
    return lines if lines else [text[:60]]

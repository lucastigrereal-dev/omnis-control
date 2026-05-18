"""Tests for CarouselPreviewGenerator."""
from pathlib import Path

import pytest

from src.preview.carousel_preview import CarouselPreviewGenerator

MISSION_DIR = Path(__file__).parents[2] / "missions" / "MIS-20260518-003"
MD_PATH = MISSION_DIR / "05_outputs" / "estrutura_slide_a_slide.md"


@pytest.fixture
def generator():
    return CarouselPreviewGenerator()


@pytest.fixture
def slides(generator):
    return generator.parse(MD_PATH)


# ---- 1. parse returns list of dicts with expected keys ----
def test_parse_returns_list_of_dicts_with_keys(slides):
    assert isinstance(slides, list)
    assert len(slides) > 0
    for slide in slides:
        for key in ("number", "title", "body", "notes"):
            assert key in slide, f"Key '{key}' missing in slide {slide}"


# ---- 2. parse extracts correct slide count (10 slides) ----
def test_parse_slide_count(slides):
    assert len(slides) == 10


# ---- 3. generate_html writes valid HTML file ----
def test_generate_html_writes_file(generator, slides, tmp_path):
    out = tmp_path / "preview.html"
    result = generator.generate_html(slides, out)
    assert result == out
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "<html" in content


# ---- 4. HTML contains slide count ----
def test_html_contains_slide_count(generator, slides, tmp_path):
    out = tmp_path / "preview.html"
    generator.generate_html(slides, out)
    content = out.read_text(encoding="utf-8")
    total = len(slides)
    # counter label shows "1 / N" and JS var total = N
    assert f"/ {total}" in content


# ---- 5. HTML contains navigation buttons (prev/next) ----
def test_html_contains_nav_buttons(generator, slides, tmp_path):
    out = tmp_path / "preview.html"
    generator.generate_html(slides, out)
    content = out.read_text(encoding="utf-8")
    assert "prevBtn" in content
    assert "nextBtn" in content
    assert "navigate(" in content


# ---- 6. run() on real mission dir produces file ----
def test_run_on_real_mission_dir_produces_file(generator, tmp_path):
    out = tmp_path / "carousel_preview.html"
    result = generator.run(MISSION_DIR, output_path=out)
    assert result == out
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "CAPA" in content or "Slide 1" in content


# ---- 7. each slide has non-empty title ----
def test_slides_have_titles(slides):
    for slide in slides:
        assert slide["title"], f"Empty title on slide {slide['number']}"


# ---- 8. slide numbers are sequential starting at 1 ----
def test_slide_numbers_sequential(slides):
    for i, slide in enumerate(slides):
        assert slide["number"] == i + 1


# ---- 9. HTML has print-friendly style ----
def test_html_has_print_style(generator, slides, tmp_path):
    out = tmp_path / "preview.html"
    generator.generate_html(slides, out)
    content = out.read_text(encoding="utf-8")
    assert "@media print" in content


# ---- 10. missing md raises FileNotFoundError ----
def test_run_missing_md_raises(generator, tmp_path):
    with pytest.raises(FileNotFoundError):
        generator.run(tmp_path)

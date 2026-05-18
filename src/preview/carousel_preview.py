"""CarouselPreviewGenerator — parses estrutura_slide_a_slide.md and renders self-contained HTML."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


class CarouselPreviewGenerator:
    """Generates a navigable HTML carousel from OMNIS Design Engine outputs."""

    # ------------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------------

    def parse(self, md_path: Path) -> list[dict]:
        """Parse estrutura_slide_a_slide.md into a list of slide dicts.

        Each dict has keys: number (int), title (str), body (str), notes (str).
        """
        text = Path(md_path).read_text(encoding="utf-8")

        # Split on slide headers: ## SLIDE N — ...
        slide_pattern = re.compile(
            r"^## SLIDE (\d+)\s*[—–-]+\s*(.+?)$", re.MULTILINE
        )
        matches = list(slide_pattern.finditer(text))

        slides: list[dict] = []

        for i, match in enumerate(matches):
            number = int(match.group(1))
            title = match.group(2).strip()

            # Body = text between this match end and next match start (or EOF)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block = text[start:end].strip()

            # Extract table rows as key-value pairs for the body
            body_lines: list[str] = []
            notes_lines: list[str] = []

            for line in block.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("|---|") or stripped.startswith("| ---"):
                    continue
                if stripped.startswith("|"):
                    # Parse table row: | key | value |
                    cells = [c.strip() for c in stripped.strip("|").split("|")]
                    if len(cells) >= 2:
                        key = re.sub(r"\*\*(.+?)\*\*", r"\1", cells[0]).strip()
                        val = cells[1].strip()
                        if key.lower() in ("nota legal", "fonte dos dados", "tempo de leitura", "emoção alvo"):
                            notes_lines.append(f"{key}: {val}")
                        else:
                            if key and val:
                                body_lines.append(f"{key}: {val}")
                            elif val:
                                body_lines.append(val)

            slides.append(
                {
                    "number": number,
                    "title": title,
                    "body": "\n".join(body_lines),
                    "notes": "\n".join(notes_lines),
                }
            )

        return slides

    # ------------------------------------------------------------------
    # Generate HTML
    # ------------------------------------------------------------------

    def generate_html(self, slides: list[dict], output_path: Path) -> Path:
        """Write a self-contained HTML carousel file and return its path."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        total = len(slides)
        slides_html = "\n".join(self._slide_html(s, i) for i, s in enumerate(slides))

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Carousel Preview — {total} slides</title>
<style>
  /* ---- reset ---- */
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #111; color: #f0f0f0; min-height: 100vh; }}

  /* ---- header ---- */
  header {{ padding: 16px 24px; background: #1a1a1a; border-bottom: 1px solid #333;
            display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }}
  header h1 {{ font-size: 1rem; color: #ccc; flex: 1; }}
  .counter {{ font-size: 0.9rem; color: #aaa; white-space: nowrap; }}

  /* ---- viewer ---- */
  .viewer {{ display: flex; align-items: center; justify-content: center;
             padding: 32px 16px; gap: 16px; }}
  .nav-btn {{ background: #2a2a2a; border: 1px solid #444; color: #fff;
              width: 48px; height: 48px; border-radius: 50%; font-size: 1.4rem;
              cursor: pointer; flex-shrink: 0; transition: background 0.2s; }}
  .nav-btn:hover {{ background: #444; }}
  .nav-btn:disabled {{ opacity: 0.3; cursor: default; }}

  /* ---- slides ---- */
  .slides-container {{ position: relative; width: min(480px, 100%); }}
  .slide {{ display: none; background: #1e1e2e; border-radius: 16px;
            padding: 32px; min-height: 360px; border: 1px solid #333;
            animation: fadeIn 0.25s ease; }}
  .slide.active {{ display: block; }}
  @keyframes fadeIn {{ from {{ opacity:0; transform: translateY(6px); }}
                        to   {{ opacity:1; transform: translateY(0); }} }}

  .slide-number {{ font-size: 0.75rem; color: #888; margin-bottom: 8px; }}
  .slide-title {{ font-size: 1.25rem; font-weight: 700; color: #e0d0ff;
                  margin-bottom: 20px; line-height: 1.3; }}
  .slide-body {{ font-size: 0.85rem; line-height: 1.7; color: #ccc;
                 white-space: pre-wrap; word-break: break-word; }}
  .slide-notes {{ margin-top: 20px; padding-top: 16px; border-top: 1px solid #333;
                  font-size: 0.75rem; color: #888; white-space: pre-wrap; }}

  /* ---- dots ---- */
  .dots {{ display: flex; justify-content: center; gap: 8px; padding: 12px 0 24px; flex-wrap: wrap; }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; background: #444; cursor: pointer;
          transition: background 0.2s, transform 0.2s; border: none; }}
  .dot.active {{ background: #a78bfa; transform: scale(1.3); }}

  /* ---- progress bar ---- */
  .progress {{ height: 3px; background: #333; position: fixed; top: 0; left: 0; right: 0; z-index: 99; }}
  .progress-fill {{ height: 100%; background: #a78bfa; transition: width 0.3s ease; }}

  /* ---- print ---- */
  @media print {{
    body {{ background: #fff; color: #000; }}
    header, .nav-btn, .dots, .progress {{ display: none !important; }}
    .slides-container {{ width: 100%; }}
    .slide {{ display: block !important; break-inside: avoid; page-break-after: always;
              background: #fff; color: #000; border: 1px solid #ccc; margin-bottom: 24px; }}
    .slide-title {{ color: #3a1a8f; }}
    .slide-body, .slide-notes {{ color: #333; }}
  }}
</style>
</head>
<body>

<div class="progress"><div class="progress-fill" id="progressFill"></div></div>

<header>
  <h1>Carousel Preview</h1>
  <span class="counter" id="counterLabel">1 / {total}</span>
</header>

<div class="viewer">
  <button class="nav-btn" id="prevBtn" onclick="navigate(-1)" disabled>&#8592;</button>
  <div class="slides-container">
{slides_html}
  </div>
  <button class="nav-btn" id="nextBtn" onclick="navigate(1)">&#8594;</button>
</div>

<div class="dots" id="dotsContainer">
{"".join(f'  <button class="dot{" active" if i == 0 else ""}" onclick="goTo({i})" title="Slide {s["number"]}"></button>' for i, s in enumerate(slides))}
</div>

<script>
  var current = 0;
  var total = {total};

  function update() {{
    document.querySelectorAll('.slide').forEach(function(el, i) {{
      el.classList.toggle('active', i === current);
    }});
    document.querySelectorAll('.dot').forEach(function(el, i) {{
      el.classList.toggle('active', i === current);
    }});
    document.getElementById('counterLabel').textContent = (current + 1) + ' / ' + total;
    document.getElementById('prevBtn').disabled = current === 0;
    document.getElementById('nextBtn').disabled = current === total - 1;
    document.getElementById('progressFill').style.width = ((current + 1) / total * 100) + '%';
  }}

  function navigate(dir) {{
    current = Math.max(0, Math.min(total - 1, current + dir));
    update();
  }}

  function goTo(i) {{
    current = i;
    update();
  }}

  document.addEventListener('keydown', function(e) {{
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') navigate(1);
    if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   navigate(-1);
  }});

  update();
</script>
</body>
</html>
"""
        output_path.write_text(html, encoding="utf-8")
        return output_path

    # ------------------------------------------------------------------
    # Orchestrate
    # ------------------------------------------------------------------

    def run(self, mission_dir: Path, output_path: Optional[Path] = None) -> Path:
        """Parse outputs from a mission dir and generate the HTML preview."""
        mission_dir = Path(mission_dir)
        md_path = mission_dir / "05_outputs" / "estrutura_slide_a_slide.md"
        if not md_path.exists():
            raise FileNotFoundError(f"Slide structure not found: {md_path}")

        if output_path is None:
            output_path = mission_dir / "preview" / "carousel_preview.html"

        slides = self.parse(md_path)
        return self.generate_html(slides, output_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _slide_html(slide: dict, index: int) -> str:
        active = " active" if index == 0 else ""
        number_label = f"Slide {slide['number']}"

        def esc(s: str) -> str:
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        notes_block = ""
        if slide.get("notes"):
            notes_block = f'    <div class="slide-notes">{esc(slide["notes"])}</div>\n'

        return (
            f'  <div class="slide{active}">\n'
            f'    <div class="slide-number">{number_label}</div>\n'
            f'    <div class="slide-title">{esc(slide["title"])}</div>\n'
            f'    <div class="slide-body">{esc(slide["body"])}</div>\n'
            f'{notes_block}'
            f'  </div>'
        )

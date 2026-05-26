"""CarrosselGenerator — Camada 3 da Agência.

Gera carrossel (múltiplos slides PNG) + thumbnail a partir de texto/hook
usando PIL/Pillow local — zero cloud, zero custo.

Estrutura de slides:
  slide_00 → capa (título grande + nome do perfil)
  slide_01..N → conteúdo (uma bullet por slide)
  slide_CTA → chamada pra ação (texto fixo por perfil)

Princípios:
- dry_run=True: retorna paths sem criar arquivos (manifesto JSON salvo)
- dry_run=False: cria imagens PNG reais em output_dir
- Fontes: tenta Arial (Windows) → fallback PIL default
- Cores por perfil via _PERFIL_PALETTE (extensível)
- Nunca publica — só entrega arquivo em output/agencia/<perfil>/<data>/
"""
from __future__ import annotations

import json
import logging
import textwrap
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("omnis.agencia.carrossel")

# ------------------------------------------------------------------
# Paleta de cores por perfil (bg, text, accent)
# ------------------------------------------------------------------
_PERFIL_PALETTE: dict[str, tuple[str, str, str]] = {
    "lucastigrereal":    ("#1a1a2e", "#e8e8e8", "#f5a623"),
    "oinatalrn":         ("#0d3b66", "#ffffff", "#ffd700"),
    "agenteviajabrasil": ("#0a5c36", "#ffffff", "#f5a623"),
    "afamiliatigrereal": ("#4a1942", "#ffffff", "#ff69b4"),
    "oquecomernatalrn":  ("#8b1a1a", "#ffffff", "#ffd700"),
    "natalaivoueu":      ("#1a3c5e", "#ffffff", "#00bfff"),
    "default":           ("#1a1a2e", "#e8e8e8", "#f5a623"),
}

_SLIDE_W  = 1080
_SLIDE_H  = 1080
_THUMB_W  = 1280
_THUMB_H  = 720

# Fontes tentadas em ordem (Windows paths)
_FONT_PATHS_TITLE   = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
]
_FONT_PATHS_BODY    = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _load_font(paths: list[str], size: int):
    """Tenta carregar TrueType; fallback para default (sem size arg)."""
    try:
        from PIL import ImageFont
        for p in paths:
            if Path(p).exists():
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()
    except Exception:  # noqa: BLE001
        from PIL import ImageFont
        return ImageFont.load_default()


# ------------------------------------------------------------------
# Dataclasses de resultado
# ------------------------------------------------------------------

@dataclass
class CarrosselResult:
    session_id: str
    perfil: str
    slides: list[Path]
    thumbnail: Optional[Path]
    output_dir: Path
    dry_run: bool
    slides_count: int
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "perfil": self.perfil,
            "slides": [str(p) for p in self.slides],
            "thumbnail": str(self.thumbnail) if self.thumbnail else None,
            "output_dir": str(self.output_dir),
            "dry_run": self.dry_run,
            "slides_count": self.slides_count,
            "metadata": self.metadata,
        }

    def summary(self) -> str:
        lines = [
            f"session={self.session_id}  perfil={self.perfil}  dry_run={self.dry_run}",
            f"output:    {self.output_dir}",
            f"slides:    {self.slides_count} arquivo(s)",
            f"thumbnail: {self.thumbnail or 'N/A'}",
        ]
        for i, s in enumerate(self.slides):
            lines.append(f"  slide {i:02d}: {s.name}")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Gerador principal
# ------------------------------------------------------------------

class CarrosselGenerator:
    """Gera carrossel PNG + thumbnail PNG via PIL/Pillow.

    Uso:
        gen = CarrosselGenerator(dry_run=False)
        result = gen.generate(
            title="Hotel Vista Mar",
            slides=["Piscina privativa", "Café da manhã gourmet", "Vista pro mar"],
            perfil="oinatalrn",
            output_dir=Path("output/agencia/oinatalrn/2026-05-25"),
        )
    """

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def generate(
        self,
        title: str,
        slides: list[str],
        perfil: str,
        output_dir: Path,
        session_id: Optional[str] = None,
        cta: str = "Veja mais no link da bio ↗",
    ) -> CarrosselResult:
        """Gera o carrossel completo + thumbnail.

        Args:
            title:      Título principal (capa + thumbnail).
            slides:     Lista de textos — cada item vira 1 slide de conteúdo.
            perfil:     Slug do perfil (ex: 'oinatalrn').
            output_dir: Pasta onde os arquivos serão salvos.
            session_id: ID da sessão (gerado se não fornecido).
            cta:        Texto do slide final de call-to-action.

        Returns:
            CarrosselResult com paths de todos os slides + thumbnail.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]

        output_dir = Path(output_dir)

        palette = _PERFIL_PALETTE.get(perfil, _PERFIL_PALETTE["default"])
        bg_color, text_color, accent_color = palette

        # Slides gerados: capa + conteúdo + CTA
        all_slide_texts = [("capa", title)] + [("slide", s) for s in slides] + [("cta", cta)]
        slide_paths: list[Path] = []

        if not self.dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)

        for idx, (kind, text) in enumerate(all_slide_texts):
            slug = f"carrossel_{session_id}_slide{idx:02d}_{kind}"
            path = output_dir / f"{slug}.png"
            slide_paths.append(path)

            if not self.dry_run:
                img = self._render_slide(
                    text=text,
                    kind=kind,
                    perfil=perfil,
                    bg_color=bg_color,
                    text_color=text_color,
                    accent_color=accent_color,
                    index=idx,
                    total=len(all_slide_texts),
                )
                img.save(str(path), "PNG")
                _logger.debug("carrossel: slide %d salvo em %s", idx, path)

        # Thumbnail
        thumb_path = output_dir / f"thumbnail_{session_id}.png"
        if not self.dry_run:
            thumb = self._render_thumbnail(
                title=title,
                perfil=perfil,
                bg_color=bg_color,
                text_color=text_color,
                accent_color=accent_color,
            )
            thumb.save(str(thumb_path), "PNG")
            _logger.debug("carrossel: thumbnail salvo em %s", thumb_path)

        # Manifesto (sempre salvo — rastreabilidade)
        result = CarrosselResult(
            session_id=session_id,
            perfil=perfil,
            slides=slide_paths,
            thumbnail=thumb_path,
            output_dir=output_dir,
            dry_run=self.dry_run,
            slides_count=len(slide_paths),
            metadata={
                "title": title,
                "perfil": perfil,
                "slide_texts": slides,
                "cta": cta,
                "bg_color": bg_color,
                "accent_color": accent_color,
            },
        )

        manifest_path = output_dir / f"carrossel_{session_id}.manifest.json"
        if not self.dry_run:
            manifest_path.write_text(
                json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        else:
            output_dir.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        _logger.info(
            "carrossel: %s gerado — %d slides + thumbnail | dry_run=%s",
            session_id,
            len(slide_paths),
            self.dry_run,
        )
        return result

    # ------------------------------------------------------------------
    # Renderização interna
    # ------------------------------------------------------------------

    def _render_slide(
        self,
        text: str,
        kind: str,          # "capa" | "slide" | "cta"
        perfil: str,
        bg_color: str,
        text_color: str,
        accent_color: str,
        index: int,
        total: int,
    ):
        """Renderiza 1 slide PIL Image (_SLIDE_W x _SLIDE_H)."""
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (_SLIDE_W, _SLIDE_H), color=_hex_to_rgb(bg_color))
        draw = ImageDraw.Draw(img)

        # Barra decorativa superior (accent)
        bar_h = 12
        draw.rectangle(
            [(0, 0), (_SLIDE_W, bar_h)],
            fill=_hex_to_rgb(accent_color),
        )
        # Barra decorativa inferior
        draw.rectangle(
            [(0, _SLIDE_H - bar_h), (_SLIDE_W, _SLIDE_H)],
            fill=_hex_to_rgb(accent_color),
        )

        if kind == "capa":
            self._draw_capa(draw, text, perfil, text_color, accent_color)
        elif kind == "cta":
            self._draw_cta(draw, text, text_color, accent_color)
        else:
            self._draw_content_slide(draw, text, text_color, accent_color, index, total)

        # Numeração de slide
        self._draw_page_num(draw, index + 1, total, text_color)

        return img

    def _draw_capa(self, draw, title: str, perfil: str, text_color: str, accent_color: str) -> None:
        from PIL import ImageDraw
        font_title  = _load_font(_FONT_PATHS_TITLE, 72)
        font_sub    = _load_font(_FONT_PATHS_BODY,  36)

        cx = _SLIDE_W // 2
        cy = _SLIDE_H // 2

        # Linha accent decorativa central
        draw.rectangle([(cx - 60, cy - 80), (cx + 60, cy - 74)], fill=_hex_to_rgb(accent_color))

        # Título (com wrap)
        wrapped = textwrap.fill(title, width=22)
        draw.text(
            (cx, cy - 40),
            wrapped,
            font=font_title,
            fill=_hex_to_rgb(text_color),
            anchor="mm",
            align="center",
        )

        # Perfil abaixo
        draw.text(
            (cx, cy + 120),
            f"@{perfil}",
            font=font_sub,
            fill=_hex_to_rgb(accent_color),
            anchor="mm",
        )

    def _draw_content_slide(
        self, draw, text: str, text_color: str, accent_color: str, index: int, total: int
    ) -> None:
        font_body = _load_font(_FONT_PATHS_BODY, 52)
        font_num  = _load_font(_FONT_PATHS_TITLE, 120)

        cx = _SLIDE_W // 2
        cy = _SLIDE_H // 2

        # Número do item em grande (decorativo, translúcido via cor diluída)
        tc = _hex_to_rgb(text_color)
        ghost_color = (tc[0] // 4, tc[1] // 4, tc[2] // 4)
        draw.text(
            (cx - 320, cy + 160),
            str(index),
            font=font_num,
            fill=ghost_color,
        )

        # Texto principal (wrap ~20 chars por linha)
        wrapped = textwrap.fill(text, width=24)
        draw.text(
            (cx, cy - 30),
            wrapped,
            font=font_body,
            fill=_hex_to_rgb(text_color),
            anchor="mm",
            align="center",
        )

    def _draw_cta(self, draw, text: str, text_color: str, accent_color: str) -> None:
        font_cta = _load_font(_FONT_PATHS_TITLE, 58)
        font_arr = _load_font(_FONT_PATHS_BODY,  42)

        cx = _SLIDE_W // 2
        cy = _SLIDE_H // 2

        draw.text(
            (cx, cy - 60),
            "Curtiu?",
            font=font_cta,
            fill=_hex_to_rgb(accent_color),
            anchor="mm",
        )
        draw.text(
            (cx, cy + 60),
            text,
            font=font_arr,
            fill=_hex_to_rgb(text_color),
            anchor="mm",
            align="center",
        )

    def _draw_page_num(self, draw, current: int, total: int, text_color: str) -> None:
        font = _load_font(_FONT_PATHS_BODY, 28)
        draw.text(
            (_SLIDE_W - 40, _SLIDE_H - 50),
            f"{current}/{total}",
            font=font,
            fill=_hex_to_rgb(text_color),
            anchor="rm",
        )

    def _render_thumbnail(
        self,
        title: str,
        perfil: str,
        bg_color: str,
        text_color: str,
        accent_color: str,
    ):
        """Renderiza thumbnail 1280x720 PNG."""
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (_THUMB_W, _THUMB_H), color=_hex_to_rgb(bg_color))
        draw = ImageDraw.Draw(img)

        font_title = _load_font(_FONT_PATHS_TITLE, 80)
        font_sub   = _load_font(_FONT_PATHS_BODY,  38)

        # Barras laterais accent
        bar_w = 16
        draw.rectangle([(0, 0), (bar_w, _THUMB_H)], fill=_hex_to_rgb(accent_color))
        draw.rectangle([(_THUMB_W - bar_w, 0), (_THUMB_W, _THUMB_H)], fill=_hex_to_rgb(accent_color))

        cx = _THUMB_W // 2
        cy = _THUMB_H // 2

        wrapped = textwrap.fill(title, width=26)
        draw.text(
            (cx, cy - 30),
            wrapped,
            font=font_title,
            fill=_hex_to_rgb(text_color),
            anchor="mm",
            align="center",
        )
        draw.text(
            (cx, cy + 110),
            f"@{perfil}",
            font=font_sub,
            fill=_hex_to_rgb(accent_color),
            anchor="mm",
        )
        return img

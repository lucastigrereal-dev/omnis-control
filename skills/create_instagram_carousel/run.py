#!/usr/bin/env python3
"""Gera estrutura de carrossel Instagram slide-a-slide."""
import argparse, json, sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
OUTPUT = HOME / "JARVIS_OS" / "60_OUTPUTS" / "instagram" / "carrosseis"

def gerar(perfil: str, tema: str, qtd_slides: int = 5):
    perfil = perfil.lower().replace("@", "")
    qtd = max(3, min(10, qtd_slides))

    slides = []
    slides.append({"slide": 1, "tipo": "capa", "texto": f"Capa: {tema}"})
    for i in range(2, qtd + 1):
        if i == qtd - 1:
            slides.append({"slide": i, "tipo": "dica", "texto": f"Dica pratica: {tema}"})
        elif i == qtd:
            slides.append({"slide": i, "tipo": "cta", "texto": f"Gostou? Segue @{perfil} para mais!"})
        else:
            slides.append({"slide": i, "tipo": "conteudo", "texto": f"{tema}: dica {i}"})

    output = {
        "skill": "create_instagram_carousel",
        "gerado_em": datetime.now().isoformat(),
        "perfil": f"@{perfil}",
        "tema": tema,
        "total_slides": len(slides),
        "slides": slides,
        "next_action": "Usar estrutura para criar design no Canva.",
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    slug = tema.lower().replace(" ", "_")[:20]
    path = OUTPUT / f"carrossel_{perfil}_{slug}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Carrossel: @{perfil} — {tema}")
    print(f"  Slides: {len(slides)}")
    for s in slides:
        print(f"    {s['slide']}. [{s['tipo']}] {s['texto'][:50]}")
    print(f"  JSON: {path}")
    return output

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Gera estrutura de carrossel Instagram")
    p.add_argument("perfil", nargs="?", default="lucastigrereal", help="Handle Instagram")
    p.add_argument("tema", nargs="?", default="conteudo", help="Tema do carrossel")
    p.add_argument("qtd", nargs="?", type=int, default=5, help="Numero de slides (3-10)")
    args = p.parse_args()
    gerar(args.perfil, args.tema, args.qtd)

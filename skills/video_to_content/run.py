#!/usr/bin/env python3
"""Transforma video em conteudo Instagram (carrossel + hooks + legenda)."""
import argparse, json, sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
OUTPUT = HOME / "JARVIS_OS" / "60_OUTPUTS" / "instagram" / "content_batches"

def transformar(titulo: str, topicos: list = None, perfil: str = "lucastigrereal"):
    perfil = perfil.lower().replace("@", "")
    if not topicos:
        topicos = ["Ponto principal 1", "Ponto principal 2", "Dica bonus"]

    hooks = [
        f"{topicos[0]} — voce ja sabia disso?",
        f"O que ninguem te conta sobre {titulo}",
        f"{len(topicos)} motivos para {titulo.lower()}",
    ]

    slides = []
    slides.append({"slide": 1, "tipo": "capa", "texto": titulo})
    for i, t in enumerate(topicos, start=2):
        slides.append({"slide": i, "tipo": "conteudo", "texto": str(t)})
    slides.append({
        "slide": len(topicos) + 2,
        "tipo": "cta",
        "texto": f"Gostou? Segue @{perfil} para mais!",
    })

    output = {
        "skill": "video_to_content",
        "gerado_em": datetime.now().isoformat(),
        "video_origem": titulo,
        "perfil": f"@{perfil}",
        "topicos_extraidos": topicos,
        "total_slides": len(slides),
        "hooks_sugeridos": hooks,
        "slides": slides,
        "formato_sugerido": "carrossel",
        "next_action": "Revisar slides e programar publicacao no calendario.",
    }

    data_dir = OUTPUT / datetime.now().strftime("%Y-%m-%d")
    data_dir.mkdir(parents=True, exist_ok=True)
    slug = titulo.lower().replace(" ", "_")[:20]
    path = data_dir / f"repurpose_{perfil}_{slug}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Transformacao video -> conteudo: {titulo}")
    print(f"  Carrossel: {len(slides)} slides")
    print(f"  Hooks: {len(hooks)} sugeridos")
    for h in hooks:
        print(f"    -> {h}")
    print(f"  JSON: {path}")
    return output

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Transforma video em conteudo Instagram")
    p.add_argument("titulo", nargs="?", default="Video transformado", help="Titulo do video")
    p.add_argument("topicos", nargs="*", default=None, help="Topicos principais do video")
    args = p.parse_args()
    transformar(args.titulo, args.topicos)

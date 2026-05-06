#!/usr/bin/env python3
"""Gera legenda SEOgram para Instagram."""
import argparse, json, sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
OUTPUT = HOME / "JARVIS_OS" / "60_OUTPUTS" / "instagram" / "legendas"

HASHTAGS = {
    "viagem": "#viagem #turismo #viajar #viagens #destinos #roteiro #dicasdeviagem #viajante #ferias",
    "familia": "#familia #viagememfamilia #maedeprimeiraviagem #filhos #familiabrasil",
    "gastronomia": "#gastronomia #comida #restaurante #bares #comerfora",
    "natal": "#NatalRN #PraiasDoRN #RioGrandeDoNorte #TurismoRN #NordesteBrasil",
    "autoridade": "#criacaodeconteudo #socialmedia #marketingdigital #instagramtips #criador",
}

CAPTION_TEMPLATES = {
    "carrossel": "**GUIA COMPLETO**\n\n{conteudo}\n\n{cta}\n\nSalva pra ver depois\n\n{hashtags}",
    "reel": "{hook}\n\n{conteudo}\n\n{cta}\n\n{hashtags}",
    "foto": "{hook}\n\n{conteudo}\n\n{cta}\n\n{hashtags}",
}

def gerar(perfil: str, assunto: str, formato: str = "carrossel"):
    perfil = perfil.lower().replace("@", "")
    formato = formato.lower()
    if formato not in CAPTION_TEMPLATES:
        print(f"ERRO: Formato '{formato}' invalido. Use: carrossel, reel, foto", file=sys.stderr)
        sys.exit(1)

    nicho = "viagem"
    for key in ["lucas", "viagem", "familia", "gastro", "natal", "tigre"]:
        if key in perfil or key in assunto.lower():
            nicho = {"lucas": "autoridade", "viagem": "viagem", "familia": "familia",
                     "gastro": "gastronomia", "natal": "natal", "tigre": "autoridade"}.get(key, "viagem")
            break

    hook = f"Descubra {assunto} — o guia mais completo que voce vai ler hoje!"
    cta = f"Gostou? Segue @{perfil} para mais conteudos como este!"
    conteudo = (f"Aqui vai um guia completo sobre {assunto}.\n\n"
                f"1. Primeiro passo: planejamento\n"
                f"2. Segundo passo: na hora da viagem\n"
                f"3. Terceiro passo: curtindo o destino\n"
                f"4. Bonus: dica imperdivel!\n\n"
                f"Se voce esta planejando {assunto}, esse guia e para voce.")

    hashtags = HASHTAGS.get(nicho, HASHTAGS["viagem"])
    legenda = CAPTION_TEMPLATES[formato].format(
        hook=hook, conteudo=conteudo, cta=cta, hashtags=hashtags
    )

    output = {
        "skill": "generate_seogram_caption",
        "gerado_em": datetime.now().isoformat(),
        "perfil": f"@{perfil}",
        "assunto": assunto,
        "formato": formato,
        "nicho": nicho,
        "legenda": legenda,
        "hashtags": hashtags,
        "next_action": "Revisar hook e hashtags antes de publicar.",
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    slug = assunto.lower().replace(" ", "_")[:20]
    path_json = OUTPUT / f"caption_{perfil}_{slug}.json"
    path_txt = OUTPUT / f"caption_{perfil}_{slug}.txt"

    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    with open(path_txt, "w", encoding="utf-8") as f:
        f.write(legenda)

    print(f"Caption SEOgram para @{perfil}")
    print(f"  Formato: {formato} | Nicho: {nicho}")
    print(f"  JSON: {path_json}")
    print(f"  TXT:  {path_txt}")
    return output

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Gera legenda SEOgram para Instagram")
    p.add_argument("perfil", nargs="?", default="lucastigrereal", help="Handle Instagram")
    p.add_argument("assunto", nargs="?", default="conteudo", help="Assunto do post")
    p.add_argument("formato", nargs="?", default="carrossel", help="carrossel|reel|foto")
    args = p.parse_args()
    gerar(args.perfil, args.assunto, args.formato)

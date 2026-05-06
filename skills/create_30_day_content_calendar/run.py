#!/usr/bin/env python3
"""Gera calendario editorial de 30 dias para Instagram."""
import argparse, json, sys
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path.home()
OUTPUT = HOME / "JARVIS_OS" / "60_OUTPUTS" / "instagram" / "calendarios"

PERFIS = {
    "lucastigrereal": {"seguidores": "690K", "nicho": "autoridade_lifestyle",
        "pilares": ["autoridade", "bastidores", "educacional", "inspiracional"]},
    "oinatalrn": {"seguidores": "630K", "nicho": "turismo_natal",
        "pilares": ["destinos", "hoteis", "praias", "dicas_viagem"]},
    "agenteviajabrasil": {"seguidores": "452K", "nicho": "viagens_brasil",
        "pilares": ["roteiros", "destinos_nacionais", "dicas_viagem", "curiosidades"]},
    "afamiliatigrereal": {"seguidores": "320K", "nicho": "familia_viagem",
        "pilares": ["viagem_familia", "filhos", "destinos", "dicas"]},
    "oquecomernatalrn": {"seguidores": "249K", "nicho": "gastronomia_natal",
        "pilares": ["restaurantes", "comidas_tipicas", "bares", "feiras"]},
    "natalaivoueu": {"seguidores": "240K", "nicho": "guia_natal",
        "pilares": ["praias", "passeios", "gastronomia", "cultura"]},
}

def gerar(perfil: str, tema: str = ""):
    perfil = perfil.lower().replace("@", "")
    info = PERFIS.get(perfil)
    if not info:
        print(f"ERRO: Perfil '{perfil}' nao encontrado.", file=sys.stderr)
        print(f"Validos: {', '.join(PERFIS.keys())}", file=sys.stderr)
        sys.exit(1)

    hoje = datetime.now()
    dias = []
    for d in range(30):
        data = hoje + timedelta(days=d)
        pilar = info["pilares"][d % len(info["pilares"])]
        fmt = "carrossel" if d % 3 == 0 else ("reel" if d % 3 == 1 else "foto")
        dias.append({
            "dia": d + 1,
            "data": data.strftime("%Y-%m-%d"),
            "pilar": pilar,
            "formato_sugerido": fmt,
            "status": "rascunho",
        })

    output = {
        "skill": "create_30_day_content_calendar",
        "gerado_em": datetime.now().isoformat(),
        "perfil": f"@{perfil}",
        "seguidores": info["seguidores"],
        "nicho": info["nicho"],
        "tema": tema or "geral",
        "total_dias": 30,
        "dias": dias,
        "next_action": "Revisar calendario e ajustar conforme feriados/eventos do mes.",
    }

    data_str = hoje.strftime("%Y-%m-%d")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path_json = OUTPUT / f"calendario_{perfil}_{data_str}.json"
    path_md = OUTPUT / f"calendario_{perfil}_{data_str}.md"

    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    with open(path_md, "w", encoding="utf-8") as f:
        f.write(f"# Calendario Editorial @{perfil}\n")
        f.write(f"**Gerado em:** {data_str}  |  **Tema:** {tema or 'geral'}\n\n")
        f.write("| Dia | Data | Pilar | Formato | Status |\n")
        f.write("|---|---|---|---|---|\n")
        for d in dias:
            f.write(f"| {d['dia']} | {d['data']} | {d['pilar']} | {d['formato_sugerido']} | {d['status']} |\n")

    print(f"Calendario: @{perfil} — 30 dias")
    print(f"  Nicho: {info['nicho']}")
    print(f"  JSON: {path_json}")
    print(f"  MD:   {path_md}")
    return output

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Gera calendario editorial 30 dias Instagram")
    p.add_argument("perfil", nargs="?", default="lucastigrereal", help="Handle Instagram")
    p.add_argument("tema", nargs="?", default="", help="Tema do mes")
    args = p.parse_args()
    gerar(args.perfil, args.tema)

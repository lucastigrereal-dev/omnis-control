#!/usr/bin/env python3
"""Exporta lote de conteudo para CSV (Publer/Metricool)."""
import argparse, csv, json, sys
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path.home()
OUTPUT = HOME / "JARVIS_OS" / "60_OUTPUTS" / "instagram" / "csv_batches"

FORMATOS = {"publer", "metricool", "content"}

def gerar(perfil: str, dias: int = 7, formato: str = "publer"):
    perfil = perfil.lower().replace("@", "")
    formato = formato.lower()
    if formato not in FORMATOS:
        print(f"ERRO: Formato '{formato}' invalido. Use: publer, metricool, content", file=sys.stderr)
        sys.exit(1)

    hoje = datetime.now()
    headers = ["id", "empresa", "setor", "instituicao_financiadora",
               "natureza_juridica", "porte", "municipio", "uf",
               "valor_contratado", "data_contrato"]
    linhas = []
    for d in range(dias):
        data = (hoje + timedelta(days=d)).strftime("%Y-%m-%d")
        linhas.append({
            "id": f"{perfil}_{d+1:02d}",
            "empresa": perfil,
            "setor": "turismo" if perfil != "oquecomernatalrn" else "gastronomia",
            "instituicao_financiadora": "editorial",
            "natureza_juridica": "conteudo",
            "porte": "micro",
            "municipio": "Natal",
            "uf": "RN",
            "valor_contratado": "0",
            "data_contrato": data,
        })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    slug = f"batch_{perfil}_{formato}_{hoje.strftime('%Y%m%d')}"
    path_csv = OUTPUT / f"{slug}.csv"
    path_json = OUTPUT / f"{slug}.json"

    with open(path_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(linhas)

    output = {
        "skill": "export_content_batch_to_csv",
        "gerado_em": hoje.isoformat(),
        "perfil": perfil,
        "dias": dias,
        "formato": formato,
        "linhas": len(linhas),
        "arquivo": str(path_csv),
        "next_action": "Fazer upload do CSV no Publer/Metricool ou conectar ARGOS.",
    }
    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"CSV exportado: @{perfil} — {dias} dias ({formato})")
    print(f"  Linhas: {len(linhas)}")
    print(f"  CSV: {path_csv}")
    return output

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Exporta lote de conteudo para CSV")
    p.add_argument("perfil", nargs="?", default="lucastigrereal", help="Handle Instagram")
    p.add_argument("dias", nargs="?", type=int, default=7, help="Quantidade de dias")
    p.add_argument("formato", nargs="?", default="publer", help="publer|metricool|content")
    args = p.parse_args()
    gerar(args.perfil, args.dias, args.formato)

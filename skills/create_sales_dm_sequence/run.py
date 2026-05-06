#!/usr/bin/env python3
"""Gera sequencia de DMs comerciais para prospeccao de hoteis."""
import argparse, json, sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
OUTPUT = HOME / "JARVIS_OS" / "60_OUTPUTS" / "instagram" / "scripts_dm"

PACOTES = {"starter": "R$350", "growth": "R$990/mes", "premium": "R$1.200"}

SEQUENCIA_PADRAO = [
    {"ordem": 1, "timing": "Dia 1 — 10h", "tipo": "abertura",
     "script": "Divulgue seu hotel/restaurante para mais de 2,3 milhoes de pessoas. A partir de R$350. Somos o maior ecossistema de viagem e familia do Instagram: @lucastigrereal (690K), @oinatalrn (630K), @agenteviajabrasil (452K), @afamiliatigrereal (320K), @oquecomernatalrn (249K). Funciona assim: voces criam o post, nos convidam pra collab, e a gente aceita. Permanente. Quer conhecer os pacotes?"},
    {"ordem": 2, "timing": "Follow-up 2h apos resposta", "tipo": "follow_up_rapido",
     "script": "Oi! Viu minha mensagem? Tenho 2 na fila querendo a vaga. Prefiro fechar com voces. Retorno ate hoje?"},
    {"ordem": 3, "timing": "Follow-up 24h sem resposta", "tipo": "follow_up_frio",
     "script": "Ultima tentativa! Acabei de fechar com hotel em {cidade}. Ainda tenho 1 vaga essa semana. Interesse?"},
    {"ordem": 4, "timing": "Respondeu SIM", "tipo": "qualificacao",
     "script": "Show! Pra gente alinhar: 1. Conseguem criar os posts? 2. Qual pacote? Starter R$350 / Growth R$990/mes / Premium R$1.200 3. Conseguem fazer PIX hoje? Mando o midia kit com todos os detalhes!"},
    {"ordem": 5, "timing": "Objecao 'muito caro'", "tipo": "objecao_preco",
     "script": "R$990 / 1,3M = menos de R$0,001/pessoa. Uma reserva ja paga. Preco de lancamento. Depois volta pra R$1.500."},
]

def gerar(empresa: str, contato: str = "Gerente", pacote: str = "growth"):
    pacote = pacote.lower()
    if pacote not in PACOTES:
        print(f"ERRO: Pacote '{pacote}' invalido. Use: starter, growth, premium", file=sys.stderr)
        sys.exit(1)

    sequencia = json.loads(json.dumps(SEQUENCIA_PADRAO))
    cidade = empresa.split(" ")[0]
    for msg in sequencia:
        msg["script"] = msg["script"].replace("{cidade}", cidade)

    output = {
        "skill": "create_sales_dm_sequence",
        "gerado_em": datetime.now().isoformat(),
        "empresa": empresa,
        "contato": contato,
        "pacote": pacote,
        "valor": PACOTES[pacote],
        "sequencia": sequencia,
        "next_action": "Copiar primeira DM e enviar para o contato no Instagram.",
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    slug = empresa.lower().replace(" ", "_")[:20]
    path = OUTPUT / f"dm_sequence_{slug}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Sequencia DM: {empresa} — {pacote} ({PACOTES[pacote]})")
    print(f"  Contato: {contato}")
    print(f"  {len(sequencia)} mensagens")
    print(f"  JSON: {path}")
    print(f"\nPRIMEIRA DM:")
    print(sequencia[0]["script"])
    return output

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Gera sequencia de DMs comerciais")
    p.add_argument("empresa", nargs="?", default="Hotel Exemplo", help="Nome do hotel/restaurante")
    p.add_argument("contato", nargs="?", default="Gerente", help="Cargo do contato")
    p.add_argument("pacote", nargs="?", default="growth", help="starter|growth|premium")
    args = p.parse_args()
    gerar(args.empresa, args.contato, args.pacote)

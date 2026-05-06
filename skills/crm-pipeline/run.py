#!/usr/bin/env python3
"""
CRM Pipeline — Gestao de vendas para hoteis.

Pipeline: lead → qualificado → proposta → negociacao → fechado/perdido

Modos:
  lead       Adicionar novo lead (hotel)
  list       Listar leads por status
  stage      Mudar estagio do lead
  proposta   Registrar proposta enviada
  today      O que fazer hoje (follow-ups)
  metrics    Metricas do pipeline
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path.home() / "JARVIS_OS" / "01_MEMORY" / "crm_pipeline.db"
ESTAGIOS = ["lead", "qualificado", "proposta", "negociacao", "fechado", "perdido"]
PERFIS = ["lucastigrereal", "oinatalrn", "agenteviajabrasil", "afamiliatigrereal", "oquecomernatalrn", "natalaivoueu"]


def _con():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            hotel TEXT,
            cidade TEXT,
            contato TEXT,
            estagio TEXT DEFAULT 'lead',
            perfil_interesse TEXT,
            valor_estimado REAL DEFAULT 0,
            origem TEXT DEFAULT 'manual',
            notas TEXT,
            proximo_contato DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS propostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER REFERENCES leads(id),
            pacote TEXT,
            valor REAL,
            perfis TEXT,
            data_envio DATE,
            status TEXT DEFAULT 'enviada',
            notas TEXT
        )
    """)
    conn.commit()
    return conn


def cmd_lead(args):
    conn = _con()
    cur = conn.execute(
        "INSERT INTO leads (nome, hotel, cidade, contato, estagio, perfil_interesse, valor_estimado, origem, notas, proximo_contato) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (args.nome, args.hotel or "", args.cidade or "", args.contato or "", args.estagio, args.perfil or "", args.valor or 0, args.origem or "manual", args.notas or "", args.proximo or None),
    )
    conn.commit()
    lead_id = cur.lastrowid
    print(json.dumps({
        "status": "ok",
        "lead_id": lead_id,
        "nome": args.nome,
        "estagio": args.estagio,
        "next_action": f"crm-pipeline list --estagio {args.estagio}",
    }, indent=2, ensure_ascii=False))
    conn.close()


def cmd_list(args):
    conn = _con()
    where = "1=1"
    params = []
    if args.estagio:
        where += " AND estagio = ?"
        params.append(args.estagio)
    if args.dias:
        where += " AND proximo_contato <= date('now', '+' || ? || ' days')"
        params.append(str(args.dias))

    rows = conn.execute(
        f"SELECT id, nome, hotel, cidade, estagio, valor_estimado, proximo_contato, created_at FROM leads WHERE {where} ORDER BY updated_at DESC LIMIT 50",
        params,
    ).fetchall()
    conn.close()

    if not rows:
        print(json.dumps({"status": "ok", "total": 0, "leads": [], "next_action": "add first lead"}, indent=2, ensure_ascii=False))
        return

    leads = [dict(r) for r in rows]
    total_valor = sum(l.get("valor_estimado", 0) or 0 for l in leads)

    print(json.dumps({
        "status": "ok",
        "total": len(leads),
        "valor_total_estimado": total_valor,
        "leads": [
            {
                "id": l["id"],
                "nome": l["nome"],
                "hotel": l["hotel"],
                "cidade": l["cidade"],
                "estagio": l["estagio"],
                "valor": l["valor_estimado"],
                "proximo_contato": l["proximo_contato"],
                "criado": l["created_at"][:10] if l["created_at"] else "",
            }
            for l in leads
        ],
        "next_action": "crm-pipeline stage --id X --estagio qualificado" if not args.estagio else "crm-pipeline proposta --id X --pacote Growth",
    }, indent=2, ensure_ascii=False))


def cmd_stage(args):
    if args.estagio not in ESTAGIOS:
        print(f"ERRO: Estagio invalido. Opcoes: {', '.join(ESTAGIOS)}")
        sys.exit(1)
    conn = _con()
    conn.execute("UPDATE leads SET estagio = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (args.estagio, args.id))
    conn.commit()
    row = conn.execute("SELECT id, nome, estagio FROM leads WHERE id = ?", (args.id,)).fetchone()
    conn.close()
    if not row:
        print(f"ERRO: Lead {args.id} nao encontrado")
        sys.exit(1)
    print(json.dumps({
        "status": "ok",
        "lead_id": row["id"],
        "nome": row["nome"],
        "novo_estagio": args.estagio,
        "next_action": "crm-pipeline proposta" if args.estagio == "qualificado" else "crm-pipeline list",
    }, indent=2, ensure_ascii=False))


def cmd_proposta(args):
    conn = _con()
    conn.execute(
        "INSERT INTO propostas (lead_id, pacote, valor, perfis, data_envio, notas) VALUES (?, ?, ?, ?, ?, ?)",
        (args.id, args.pacote, args.valor, args.perfis or "", args.data or str(date.today()), args.notas or ""),
    )
    conn.execute("UPDATE leads SET estagio = 'proposta', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (args.id,))
    conn.commit()
    conn.close()
    print(json.dumps({
        "status": "ok",
        "lead_id": args.id,
        "pacote": args.pacote,
        "valor": args.valor,
        "next_action": "crm-pipeline stage --id X --estagio negociacao",
    }, indent=2, ensure_ascii=False))


def cmd_today(args):
    conn = _con()
    rows = conn.execute(
        "SELECT id, nome, hotel, estagio, proximo_contato, notas FROM leads WHERE proximo_contato <= date('now', '+3 days') AND estagio NOT IN ('fechado', 'perdido') ORDER BY proximo_contato ASC",
    ).fetchall()

    if not rows:
        print(json.dumps({"status": "ok", "total": 0, "message": "Nenhum contato pendente nos proximos 3 dias", "next_action": "crm-pipeline list"}, indent=2, ensure_ascii=False))
        return

    pendentes = [dict(r) for r in rows]
    print(json.dumps({
        "status": "ok",
        "total": len(pendentes),
        "acoes_hoje": [
            {
                "id": l["id"],
                "nome": l["nome"],
                "hotel": l["hotel"],
                "estagio": l["estagio"],
                "contato_ate": l["proximo_contato"],
                "notas": l["notas"],
            }
            for l in pendentes
        ],
        "next_action": "follow-up: chamar cada lead da lista",
    }, indent=2, ensure_ascii=False))
    conn.close()


def cmd_metrics(args):
    conn = _con()
    rows = conn.execute(
        "SELECT estagio, COUNT(*) as qtd, COALESCE(SUM(valor_estimado),0) as total FROM leads GROUP BY estagio ORDER BY CASE estagio WHEN 'lead' THEN 1 WHEN 'qualificado' THEN 2 WHEN 'proposta' THEN 3 WHEN 'negociacao' THEN 4 WHEN 'fechado' THEN 5 WHEN 'perdido' THEN 6 END"
    ).fetchall()
    fechados = conn.execute("SELECT COALESCE(SUM(valor_estimado),0) as total FROM leads WHERE estagio='fechado'").fetchone()
    conn.close()

    estagios = [dict(r) for r in rows]
    faturamento = float(fechados["total"]) if fechados else 0

    print(json.dumps({
        "status": "ok",
        "pipeline": estagios,
        "faturamento_fechado": faturamento,
        "total_leads": sum(e["qtd"] for e in estagios),
        "next_action": "crm-pipeline today" if any(e["qtd"] > 0 and e["estagio"] not in ("fechado", "perdido") for e in estagios) else "crm-pipeline lead",
    }, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="CRM Pipeline — Gestao de vendas para hoteis")
    sub = parser.add_subparsers(dest="mode", required=True)

    p = sub.add_parser("lead", help="Adicionar novo lead")
    p.add_argument("--nome", required=True)
    p.add_argument("--hotel")
    p.add_argument("--cidade")
    p.add_argument("--contato")
    p.add_argument("--estagio", default="lead", choices=ESTAGIOS)
    p.add_argument("--perfil", help="Perfil de interesse")
    p.add_argument("--valor", type=float, default=0)
    p.add_argument("--origem", default="manual")
    p.add_argument("--notas")
    p.add_argument("--proximo", help="Proximo contato (YYYY-MM-DD)")

    p = sub.add_parser("list", help="Listar leads")
    p.add_argument("--estagio", choices=ESTAGIOS)
    p.add_argument("--dias", type=int, help="Filtrar por dias ate proximo contato")

    p = sub.add_parser("stage", help="Mudar estagio do lead")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--estagio", required=True, choices=ESTAGIOS)

    p = sub.add_parser("proposta", help="Registrar proposta")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--pacote", required=True, choices=["Starter", "Growth", "Premium"])
    p.add_argument("--valor", type=float, required=True)
    p.add_argument("--perfis")
    p.add_argument("--data", help="Data envio (YYYY-MM-DD)")
    p.add_argument("--notas")

    sub.add_parser("today", help="O que fazer hoje")

    sub.add_parser("metrics", help="Metricas do pipeline")

    args = parser.parse_args()
    handlers = {"lead": cmd_lead, "list": cmd_list, "stage": cmd_stage, "proposta": cmd_proposta, "today": cmd_today, "metrics": cmd_metrics}
    h = handlers.get(args.mode)
    if h:
        h(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

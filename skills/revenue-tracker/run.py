#!/usr/bin/env python3
"""
Revenue Tracker — Receitas e custos da operacao Instagram.
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path.home() / "JARVIS_OS" / "01_MEMORY" / "revenue.db"
PACOTES = {"Starter": 350, "Growth": 990, "Premium": 1200}
PERFIS = ["lucastigrereal", "oinatalrn", "agenteviajabrasil", "afamiliatigrereal", "oquecomernatalrn", "natalaivoueu"]


def _con():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            pacote TEXT NOT NULL,
            valor REAL NOT NULL,
            perfis TEXT,
            mes TEXT NOT NULL,
            status TEXT DEFAULT 'recebido',
            data_recebimento DATE,
            notas TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS custos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            categoria TEXT DEFAULT 'operacional',
            valor REAL NOT NULL,
            mes TEXT NOT NULL,
            data_pagamento DATE,
            recorrente INTEGER DEFAULT 0,
            notas TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def cmd_add(args):
    conn = _con()
    cur = conn.execute(
        "INSERT INTO receitas (cliente, pacote, valor, perfis, mes, status, data_recebimento, notas) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (args.cliente, args.pacote, PACOTES.get(args.pacote, args.valor), args.perfis or "", args.mes, "pendente" if args.pendente else "recebido", args.data or str(date.today()), args.notas or ""),
    )
    conn.commit()
    print(json.dumps({"status": "ok", "id": cur.lastrowid, "cliente": args.cliente, "valor": PACOTES.get(args.pacote, args.valor), "mes": args.mes}, indent=2, ensure_ascii=False))
    conn.close()


def cmd_list(args):
    conn = _con()
    rows = conn.execute(
        "SELECT id, cliente, pacote, valor, perfis, mes, status, data_recebimento FROM receitas ORDER BY mes DESC, id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    receitas = [dict(r) for r in rows]
    total = sum(r["valor"] for r in receitas)
    print(json.dumps({"status": "ok", "total": len(receitas), "valor_total": total, "receitas": receitas}, indent=2, ensure_ascii=False))


def cmd_resumo(args):
    conn = _con()
    receitas = conn.execute(
        "SELECT mes, COUNT(*) as qtd, COALESCE(SUM(valor),0) as total FROM receitas WHERE status='recebido' GROUP BY mes ORDER BY mes DESC LIMIT 6"
    ).fetchall()
    custos = conn.execute(
        "SELECT mes, COALESCE(SUM(valor),0) as total FROM custos GROUP BY mes ORDER BY mes DESC LIMIT 6"
    ).fetchall()
    conn.close()

    r_dict = {r["mes"]: {"qtd": r["qtd"], "total": float(r["total"])} for r in receitas}
    c_dict = {c["mes"]: float(c["total"]) for c in custos}

    meses = sorted(set(list(r_dict.keys()) + list(c_dict.keys())), reverse=True)[:6]
    linhas = []
    for m in meses:
        rec = r_dict.get(m, {"qtd": 0, "total": 0})
        cst = c_dict.get(m, 0)
        linhas.append({"mes": m, "receitas": rec["total"], "custos": cst, "contratos": rec["qtd"], "lucro": round(rec["total"] - cst, 2)})

    print(json.dumps({"status": "ok", "meses": linhas, "next_action": "revenue-tracker add --cliente X --pacote Growth --mes YYYY-MM"}, indent=2, ensure_ascii=False))


def cmd_custo(args):
    conn = _con()
    cur = conn.execute(
        "INSERT INTO custos (descricao, categoria, valor, mes, data_pagamento, recorrente, notas) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (args.descricao, args.categoria, args.valor, args.mes, args.data or str(date.today()), 1 if args.recorrente else 0, args.notas or ""),
    )
    conn.commit()
    print(json.dumps({"status": "ok", "id": cur.lastrowid, "descricao": args.descricao, "valor": args.valor, "mes": args.mes}, indent=2, ensure_ascii=False))
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Revenue Tracker — Receitas e custos")
    sub = parser.add_subparsers(dest="mode", required=True)

    p = sub.add_parser("add", help="Registrar receita")
    p.add_argument("--cliente", required=True)
    p.add_argument("--pacote", required=True, choices=list(PACOTES.keys()))
    p.add_argument("--valor", type=float, default=0)
    p.add_argument("--perfis")
    p.add_argument("--mes", required=True, help="YYYY-MM")
    p.add_argument("--data", help="Data recebimento YYYY-MM-DD")
    p.add_argument("--pendente", action="store_true")
    p.add_argument("--notas")

    sub.add_parser("list", help="Listar receitas")

    p = sub.add_parser("resumo", help="Resumo financeiro por mes")

    p = sub.add_parser("custo", help="Registrar custo")
    p.add_argument("--descricao", required=True)
    p.add_argument("--categoria", default="operacional", choices=["operacional", "ferramentas", "anuncios", "freelas", "impostos", "outros"])
    p.add_argument("--valor", type=float, required=True)
    p.add_argument("--mes", required=True, help="YYYY-MM")
    p.add_argument("--data")
    p.add_argument("--recorrente", action="store_true")
    p.add_argument("--notas")

    args = parser.parse_args()
    handlers = {"add": cmd_add, "list": cmd_list, "resumo": cmd_resumo, "custo": cmd_custo}
    h = handlers.get(args.mode)
    if h:
        h(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

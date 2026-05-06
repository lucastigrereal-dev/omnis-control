#!/usr/bin/env python3
"""
ARGOS Bridge — Conecta skills Instagram ao ARGOS publishing pipeline.

Pipeline: skill output → argos-bridge → ARGOS API (:8000) → BullMQ → publish-worker → Graph API

Modos:
  caption     Cria post no ARGOS a partir de uma legenda
  carousel    Cria post do tipo CAROUSEL
  calendar    Cria lote de posts a partir de calendario editorial (bulk)
  video       Cria post do tipo VIDEO (Reels)
  evaluate    Avalia conteudo antes de publicar
  list        Lista fila de publicacao
  accounts    Lista contas sociais cadastradas
"""
import argparse
import json
import sys
import httpx
from datetime import datetime
from typing import Optional

API_BASE = "http://localhost:8000"

# Mapeamento handle → nome da conta no ARGOS
# Usado para buscar account_id dinamicamente
PERFIL_MAP = {
    "lucastigrereal": "lucastigrereal",
    "oinatalrn": "oinatalrn",
    "agenteviajabrasil": "agenteviajabrasil",
    "afamiliatigrereal": "afamiliatigrereal",
    "oquecomernatalrn": "oquecomernatalrn",
    "natalaivoueu": "natalaivoueu",
}

STATUS_EMOJI = {
    "draft": "rascunho",
    "scheduled": "agendado",
    "publishing": "publicando",
    "published": "publicado",
    "failed": "falha",
}


def _get(path: str, params: dict = None) -> dict:
    with httpx.Client(timeout=30.0) as c:
        r = c.get(f"{API_BASE}{path}", params=params or {})
        r.raise_for_status()
        return r.json()


def _post(path: str, body: dict = None) -> dict:
    with httpx.Client(timeout=30.0) as c:
        r = c.post(f"{API_BASE}{path}", json=body or {})
        r.raise_for_status()
        return r.json()


def _patch(path: str, body: dict = None) -> dict:
    with httpx.Client(timeout=30.0) as c:
        r = c.request("PATCH", f"{API_BASE}{path}", json=body or {})
        r.raise_for_status()
        return r.json()


def _find_account_id(handle: str) -> Optional[str]:
    """Busca account_id pelo nome da pagina no ARGOS."""
    data = _get("/api/v1/argos/social-accounts")
    name = PERFIL_MAP.get(handle, handle)
    for acc in data.get("items", []):
        if acc.get("name", "").lower() == name.lower():
            return acc["id"]
    return None


def cmd_caption(args):
    """Cria post no ARGOS a partir de legenda gerada."""
    account_id = _find_account_id(args.pagina)
    if not account_id:
        print(f"ERRO: Conta '{args.pagina}' nao encontrada no ARGOS")
        sys.exit(1)

    payload = {
        "account_id": account_id,
        "caption": args.caption or args.texto,
        "media_url": args.media_url or "",
        "media_type": "IMAGE",
        "format": "single",
        "status": "draft" if not args.schedule else "scheduled",
    }
    result = _post("/api/v1/argos/posts", payload)
    item = result.get("item", {})

    # Se schedule, agendar
    post_id = item.get("id")
    if args.schedule and post_id:
        _patch(f"/api/v1/argos/posts/{post_id}/schedule", {"scheduled_at": args.schedule})

    print(json.dumps({
        "status": "ok" if result.get("ok") else "error",
        "post_id": post_id,
        "account": args.pagina,
        "status_post": "scheduled" if args.schedule else "draft",
        "scheduled_at": args.schedule if args.schedule else None,
        "next_action": "schedule" if not args.schedule else "enqueue" if args.queue else "approve",
    }, indent=2, ensure_ascii=False))


def cmd_carousel(args):
    """Cria posts de carrossel no ARGOS."""
    account_id = _find_account_id(args.pagina)
    if not account_id:
        print(f"ERRO: Conta '{args.pagina}' nao encontrada no ARGOS")
        sys.exit(1)

    # Carregar estrutura do carrossel de arquivo ou stdin
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            carousel = json.load(f)
    else:
        carousel = {"slides": [{"caption": args.caption or "Carrossel"}]}

    posts_created = []
    for i, slide in enumerate(carousel.get("slides", [])):
        payload = {
            "account_id": account_id,
            "caption": slide.get("caption", f"Slide {i+1}"),
            "media_url": slide.get("media_url", args.media_url or ""),
            "media_type": "CAROUSEL",
            "format": "carousel",
            "status": "draft",
        }
        result = _post("/api/v1/argos/posts", payload)
        posts_created.append(result.get("item", {}).get("id"))

    print(json.dumps({
        "status": "ok",
        "post_ids": posts_created,
        "total": len(posts_created),
        "account": args.pagina,
        "next_action": f"approve {len(posts_created)} posts",
    }, indent=2, ensure_ascii=False))


def cmd_calendar(args):
    """Cria lote de posts a partir de calendario editorial."""
    account_id = _find_account_id(args.pagina)
    if not account_id:
        print(f"ERRO: Conta '{args.pagina}' nao encontrada no ARGOS")
        sys.exit(1)

    with open(args.file, "r", encoding="utf-8") as f:
        calendario = json.load(f)

    dias = calendario.get("dias", calendario.get("days", []))
    if not dias:
        print("ERRO: Calendario vazio ou formato invalido")
        sys.exit(1)

    posts_created = []
    for dia in dias:
        data_str = dia.get("data", dia.get("date", ""))
        tema = dia.get("tema", dia.get("hook", "Conteudo"))
        payload = {
            "account_id": account_id,
            "caption": f"{tema}\n\n{dia.get('descricao', dia.get('caption', ''))}",
            "media_url": "",
            "media_type": dia.get("media_type", "IMAGE"),
            "format": dia.get("format", "single"),
            "status": "draft",
        }
        result = _post("/api/v1/argos/posts", payload)
        post_id = result.get("item", {}).get("id")

        # Se tem data, ja agenda
        if data_str and post_id:
            try:
                dt = datetime.fromisoformat(data_str)
                _patch(f"/api/v1/argos/posts/{post_id}/schedule", {"scheduled_at": dt.isoformat()})
            except ValueError:
                pass

        posts_created.append({"post_id": post_id, "data": data_str, "tema": tema})

    print(json.dumps({
        "status": "ok",
        "total": len(posts_created),
        "account": args.pagina,
        "posts": posts_created,
        "next_action": f"review {len(posts_created)} posts no ARGOS approval queue",
    }, indent=2, ensure_ascii=False))


def cmd_video(args):
    """Cria post de video/Reels no ARGOS."""
    account_id = _find_account_id(args.pagina)
    if not account_id:
        print(f"ERRO: Conta '{args.pagina}' nao encontrada no ARGOS")
        sys.exit(1)

    if not args.media_url:
        print("ERRO: --media-url obrigatorio para video")
        sys.exit(1)

    payload = {
        "account_id": account_id,
        "caption": args.caption or args.texto or "Reels",
        "media_url": args.media_url,
        "media_type": "VIDEO",
        "format": "reel",
        "status": "draft",
    }
    result = _post("/api/v1/argos/posts", payload)
    item = result.get("item", {})

    if args.schedule and item.get("id"):
        _patch(f"/api/v1/argos/posts/{item['id']}/schedule", {"scheduled_at": args.schedule})

    print(json.dumps({
        "status": "ok",
        "post_id": item.get("id"),
        "account": args.pagina,
        "media_type": "VIDEO",
        "next_action": "approve e enqueue",
    }, indent=2, ensure_ascii=False))


def cmd_evaluate(args):
    """Avalia conteudo antes de publicar (ContentJudge)."""
    text = args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()

    if not text:
        print("ERRO: --text ou --file obrigatorio")
        sys.exit(1)

    result = _post("/api/v1/judge/evaluate", {
        "content": text,
        "page_id": args.pagina,
        "format_type": args.formato,
    })

    print(json.dumps({
        "status": "ok",
        "score": result.get("score", result.get("overall_score", "?")),
        "breakdown": result.get("breakdown", result),
        "next_action": "publish if score >= 7.0 else revise",
    }, indent=2, ensure_ascii=False))


def cmd_list(args):
    """Lista fila de publicacao."""
    result = _get("/api/v1/argos/publish-queue")
    items = result.get("items", [])
    status_filter = args.status
    if status_filter:
        items = [i for i in items if i.get("status") == status_filter]

    print(json.dumps({
        "status": "ok",
        "total": len(items),
        "items": [
            {
                "id": i.get("id"),
                "account": i.get("account", {}).get("name", "?"),
                "status": i.get("status"),
                "scheduled_at": i.get("scheduled_at"),
                "caption_preview": (i.get("content") or "")[:80],
            }
            for i in items
        ],
        "next_action": "enqueue posts scheduled e prontos",
    }, indent=2, ensure_ascii=False))


def cmd_accounts(args):
    """Lista contas sociais cadastradas no ARGOS."""
    result = _get("/api/v1/argos/social-accounts")
    items = result.get("items", [])
    print(json.dumps({
        "status": "ok",
        "total": len(items),
        "accounts": [
            {
                "id": a.get("id"),
                "name": a.get("name"),
                "platform": a.get("platform"),
                "ig_user_id": a.get("ig_user_id"),
                "followers": a.get("followers_count", 0),
            }
            for a in items
        ],
        "next_action": "add missing accounts via --add-account" if len(items) < 6 else None,
    }, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="ARGOS Bridge — Conecta skills ao pipeline de publicacao")
    sub = parser.add_subparsers(dest="mode", required=True)

    # caption
    p = sub.add_parser("caption", help="Cria post a partir de legenda")
    p.add_argument("--pagina", default="lucastigrereal")
    p.add_argument("--caption", "-c", help="Texto da legenda")
    p.add_argument("--texto", "-t", help="Texto alternativo")
    p.add_argument("--media-url", "-m", help="URL da midia")
    p.add_argument("--schedule", "-s", help="Agendar em ISO (2026-05-01T10:00:00)")
    p.add_argument("--queue", "-q", action="store_true", help="Enfileirar direto")

    # carousel
    p = sub.add_parser("carousel", help="Cria posts de carrossel")
    p.add_argument("--pagina", default="lucastigrereal")
    p.add_argument("--file", "-f", help="JSON do carrossel")
    p.add_argument("--caption", "-c", help="Legenda")
    p.add_argument("--media-url", "-m", help="URL da midia")

    # calendar
    p = sub.add_parser("calendar", help="Importa calendario editorial (bulk)")
    p.add_argument("--file", "-f", required=True, help="JSON do calendario")
    p.add_argument("--pagina", default="lucastigrereal")

    # video
    p = sub.add_parser("video", help="Cria post de video/Reels")
    p.add_argument("--pagina", default="lucastigrereal")
    p.add_argument("--media-url", "-m", required=True, help="URL do video")
    p.add_argument("--caption", "-c", help="Legenda")
    p.add_argument("--texto", "-t", help="Texto alternativo")
    p.add_argument("--schedule", "-s", help="Agendar em ISO")

    # evaluate
    p = sub.add_parser("evaluate", help="Avalia conteudo antes de publicar")
    p.add_argument("--text", help="Texto para avaliar")
    p.add_argument("--file", "-f", help="Arquivo com texto")
    p.add_argument("--pagina", default="lucastigrereal")
    p.add_argument("--formato", default="carrossel", choices=["carrossel", "reel", "multi_copy"])

    # list
    p = sub.add_parser("list", help="Lista fila de publicacao")
    p.add_argument("--status", choices=["draft", "scheduled", "publishing", "published", "failed"])

    # accounts
    sub.add_parser("accounts", help="Lista contas sociais")

    args = parser.parse_args()

    handlers = {
        "caption": cmd_caption,
        "carousel": cmd_carousel,
        "calendar": cmd_calendar,
        "video": cmd_video,
        "evaluate": cmd_evaluate,
        "list": cmd_list,
        "accounts": cmd_accounts,
    }

    handler = handlers.get(args.mode)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

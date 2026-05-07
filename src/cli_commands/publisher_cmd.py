"""Publisher CLI — pipeline unificado IDEA->PUBLISH."""
from __future__ import annotations
import asyncio
import json
import typer
from typing import Optional

publisher_app = typer.Typer(
    name="publisher",
    help="Pipeline unificado IDEA->PUBLISH (dry-run local)",
    add_completion=False,
)


@publisher_app.command(name="status")
def publisher_status():
    """Status do modulo Publisher Local."""
    from src.publisher.statemachine import ContentStatus
    states = [s.value for s in ContentStatus]
    typer.echo(f"Publisher Local — 9 estados: {', '.join(states)}")


@publisher_app.command(name="create")
def publisher_create(
    title: str = typer.Argument(..., help="Titulo do conteudo"),
    account: str = typer.Option("lucastigrereal", "--account", help="Handle da conta"),
    format: str = typer.Option("post", "--format", help="Formato: post, carousel, reel"),
):
    """Cria um novo item no pipeline (estado IDEA)."""
    import uuid
    from src.publisher.pipeline import JsonLStore
    from src.publisher.statemachine import ContentStatus

    store = JsonLStore()
    content_id = str(uuid.uuid4())
    store.insert("content_items", {
        "id": content_id,
        "account_handle": account,
        "title": title,
        "format": format,
        "status": ContentStatus.IDEA.value,
        "idempotency_key": str(uuid.uuid4()),
    })
    typer.echo(json.dumps({"content_id": content_id, "status": "idea", "title": title}, indent=2))


@publisher_app.command(name="list")
def publisher_list(
    status: Optional[str] = typer.Option(None, "--status", help="Filtrar por status"),
):
    """Lista itens no pipeline."""
    from src.publisher.pipeline import JsonLStore
    store = JsonLStore()
    items = store._read_items()
    if status:
        items = [i for i in items if i.get("status") == status]
    typer.echo(json.dumps(items, indent=2, ensure_ascii=False, default=str))


@publisher_app.command(name="pipeline")
def publisher_run(
    content_id: str = typer.Argument(..., help="ID do conteudo"),
    brief: str = typer.Option("", "--brief", help="Prompt do brief"),
):
    """Executa pipeline completo ate PUBLICADO."""
    from src.publisher.pipeline import PublishPipeline

    pipe = PublishPipeline()
    result = asyncio.run(pipe.run_full_pipeline(content_id, brief))
    typer.echo(json.dumps({
        "content_id": result.content_id,
        "status": result.status.value,
        "transitions": result.transitions,
        "error_log": result.error_log,
    }, indent=2, ensure_ascii=False, default=str))

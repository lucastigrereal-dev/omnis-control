"""CLI for Approval Center."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

approval_center_app = typer.Typer(
    name="approvals-center",
    help="Approval Center — gerencia fila de aprovacoes para operacoes de alto risco.",
    add_completion=False,
)
console = Console()


@approval_center_app.callback()
def _callback():
    """Approvals Center — request / list / show / approve / reject."""


@approval_center_app.command(name="request")
def cmd_request(
    subject: str = typer.Argument(..., help="Assunto da solicitacao"),
    description: str = typer.Option("", "--description", "-d"),
    capability_id: str = typer.Option("unknown", "--capability", "-c"),
    risk_level: str = typer.Option("high", "--risk"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Cria nova solicitacao de aprovacao."""
    from src.approval_center import service as svc_mod
    from src.approval_center import store as store_mod

    req = svc_mod.request_approval(
        subject=subject,
        description=description,
        capability_id=capability_id,
        risk_level=risk_level,
        approvals_log=store_mod.DEFAULT_APPROVALS_LOG,
    )

    if json_out:
        console.print_json(json.dumps(req.to_dict(), ensure_ascii=False))
        return

    console.print(Panel(f"[bold]Approval Request Created[/bold]", expand=False))
    console.print(f"  request_id : {req.request_id}")
    console.print(f"  subject    : {req.subject}")
    console.print(f"  capability : {req.capability_id}")
    console.print(f"  risk       : {req.risk_level}")
    console.print(f"  status     : [yellow]{req.status}[/yellow]")


@approval_center_app.command(name="list")
def cmd_list(
    status: str = typer.Option("", "--status", "-s", help="Filtrar por status (pending/approved/rejected)"),
    limit: int = typer.Option(20, "--limit"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lista solicitacoes de aprovacao."""
    from src.approval_center import store as store_mod
    from src.approval_center.store import ApprovalStore

    store = ApprovalStore(store_mod.DEFAULT_APPROVALS_LOG)
    reqs = store.list_all(limit=limit, status=status or None)

    if json_out:
        console.print_json(json.dumps([r.to_dict() for r in reqs], ensure_ascii=False))
        return

    if not reqs:
        console.print("[dim]Nenhuma solicitacao encontrada.[/dim]")
        return

    table = Table(title="Approval Requests")
    table.add_column("request_id", style="dim")
    table.add_column("subject")
    table.add_column("capability")
    table.add_column("risk")
    table.add_column("status")
    table.add_column("criado")
    for r in reqs:
        color = {"pending": "yellow", "approved": "green", "rejected": "red"}.get(r.status, "white")
        table.add_row(
            r.request_id, r.subject, r.capability_id, r.risk_level,
            f"[{color}]{r.status}[/{color}]", r.requested_at[:10],
        )
    console.print(table)


@approval_center_app.command(name="show")
def cmd_show(
    request_id: str = typer.Argument(..., help="ID da solicitacao (req_...)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Mostra detalhes de uma solicitacao."""
    from src.approval_center import store as store_mod
    from src.approval_center.store import ApprovalStore

    store = ApprovalStore(store_mod.DEFAULT_APPROVALS_LOG)
    req = store.get(request_id)
    if req is None:
        console.print(f"[yellow]Request {request_id} nao encontrado.[/yellow]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(req.to_dict(), ensure_ascii=False))
        return

    color = {"pending": "yellow", "approved": "green", "rejected": "red"}.get(req.status, "white")
    console.print(Panel(f"[bold]Approval Request[/bold] — {req.request_id}", expand=False))
    console.print(f"  subject    : {req.subject}")
    console.print(f"  description: {req.description}")
    console.print(f"  capability : {req.capability_id}")
    console.print(f"  risk       : {req.risk_level}")
    console.print(f"  status     : [{color}]{req.status}[/{color}]")
    if req.resolution_note:
        console.print(f"  note       : {req.resolution_note}")
    if req.resolved_at:
        console.print(f"  resolved   : {req.resolved_at}")
    console.print(f"  requested  : {req.requested_at}")


@approval_center_app.command(name="approve")
def cmd_approve(
    request_id: str = typer.Argument(..., help="ID da solicitacao"),
    note: str = typer.Option("", "--note", "-n"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Aprova uma solicitacao pendente."""
    from src.approval_center import service as svc_mod
    from src.approval_center import store as store_mod
    from src.approval_center.errors import ApprovalNotFoundError, ApprovalAlreadyResolvedError

    try:
        req = svc_mod.approve(request_id, note=note, approvals_log=store_mod.DEFAULT_APPROVALS_LOG)
    except ApprovalNotFoundError as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)
    except ApprovalAlreadyResolvedError as e:
        console.print(f"[yellow]Aviso: {e}[/yellow]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(req.to_dict(), ensure_ascii=False))
        return
    console.print(f"[green]Aprovado:[/green] {req.request_id}")


@approval_center_app.command(name="reject")
def cmd_reject(
    request_id: str = typer.Argument(..., help="ID da solicitacao"),
    note: str = typer.Option("", "--note", "-n"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Rejeita uma solicitacao pendente."""
    from src.approval_center import service as svc_mod
    from src.approval_center import store as store_mod
    from src.approval_center.errors import ApprovalNotFoundError, ApprovalAlreadyResolvedError

    try:
        req = svc_mod.reject(request_id, note=note, approvals_log=store_mod.DEFAULT_APPROVALS_LOG)
    except ApprovalNotFoundError as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)
    except ApprovalAlreadyResolvedError as e:
        console.print(f"[yellow]Aviso: {e}[/yellow]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(req.to_dict(), ensure_ascii=False))
        return
    console.print(f"[red]Rejeitado:[/red] {req.request_id}")

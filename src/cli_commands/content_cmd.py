"""CLI 'content' — Ciclo de aprovação de conteúdo.

Namespace limpo para o fluxo de draft → aprovação → export.

Comandos:
    content list           — lista drafts com filtro de status
    content approve <id>   — aprova 1 draft
    content approve --batch — aprova até N drafts válidos em lote
    content reject <id>    — rejeita 1 draft (--reason obrigatório)
    content status         — contagem por status

Nota: lógica real fica em src.caption_approval.{drafts,approvals}.
      Este módulo é só o adapter CLI.
"""
from __future__ import annotations

import json
import sys

import typer
from rich.console import Console
from rich.table import Table

content_app = typer.Typer(
    name="content",
    help="Ciclo de aprovação de conteúdo — lista, aprova, rejeita.",
    add_completion=False,
)
console = Console()


def _make_gate():
    from src.caption_approval.drafts import DraftsManager
    from src.caption_approval.approvals import ApprovalGate
    dm = DraftsManager()
    gate = ApprovalGate(dm)
    return dm, gate


def _queue_updater(queue_id: str, new_status: str) -> bool:
    """Tenta atualizar queue item — falha graciosa se queue não disponível."""
    try:
        from src.content_queue.queue import Queue as CQQueue
        q = CQQueue()
        return q.update_status(queue_id, new_status) is not None
    except Exception:  # noqa: BLE001
        return False


# ------------------------------------------------------------------
# content list
# ------------------------------------------------------------------

@content_app.command(name="list")
def cmd_list(
    status: str = typer.Option("", "--status", "-s", help="Filtra por status: draft|needs_review|approved|rejected"),
    account: str = typer.Option("", "--account", "-a", help="Filtra por @perfil"),
    json_out: bool = typer.Option(False, "--json", help="Saída em JSON"),
) -> None:
    """Lista drafts de conteúdo (todos os status por padrão)."""
    dm, _ = _make_gate()
    items = dm.list_all()

    if status:
        items = [i for i in items if i.status == status]
    if account:
        handle = account.lstrip("@")
        items = [i for i in items if i.account_handle.lstrip("@") == handle]

    if json_out:
        console.print_json(json.dumps([i.to_dict() for i in items], ensure_ascii=False))
        return

    if not items:
        console.print("[yellow]Nenhum draft encontrado.[/yellow]")
        return

    table = Table(title=f"Drafts de conteúdo ({len(items)} total)")
    table.add_column("ID",      style="cyan",   width=10)
    table.add_column("Perfil",  style="blue",   width=20)
    table.add_column("Status",  style="green",  width=14)
    table.add_column("v",       style="dim",    width=3)
    table.add_column("Texto",   width=50)

    _STATUS_STYLE = {
        "approved":    "green",
        "rejected":    "red",
        "needs_review":"yellow",
        "draft":       "dim",
        "revised":     "cyan",
        "stale":       "red dim",
    }

    for item in items:
        style = _STATUS_STYLE.get(item.status, "")
        txt = (item.caption_text or "")[:50].replace("\n", " ")
        table.add_row(
            item.draft_id[:8],
            item.account_handle,
            f"[{style}]{item.status}[/{style}]",
            str(item.version),
            txt,
        )

    console.print(table)


# ------------------------------------------------------------------
# content approve
# ------------------------------------------------------------------

@content_app.command(name="approve")
def cmd_approve(
    draft_id: str = typer.Argument("", help="ID do draft (omitir com --batch)"),
    batch: bool = typer.Option(False, "--batch", help="Aprova até --limit drafts válidos em lote"),
    limit: int  = typer.Option(5, "--limit", help="Máximo de drafts no modo --batch"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Aprova 1 draft ou --batch aprova N drafts válidos de uma vez."""
    dm, gate = _make_gate()

    # --batch
    if batch:
        result = gate.batch_approve(limit=limit, queue_updater=_queue_updater)

        if json_out:
            console.print_json(json.dumps(result, ensure_ascii=False))
            return

        if result["approved"] == 0 and result["skipped"] == 0:
            console.print("[yellow]Nenhum draft em needs_review ou revised encontrado.[/yellow]")
            return

        console.print(
            f"[green bold]✓ Aprovados:[/green bold] {result['approved']}  "
            f"[yellow]Pulados:[/yellow] {result['skipped']}"
        )
        for reason in result.get("skip_reasons", []):
            console.print(f"  [yellow dim]skip:[/yellow dim] {reason}")
        return

    # Aprovação unitária
    if not draft_id:
        console.print("[red]Informe um DRAFT_ID ou use --batch[/red]")
        raise typer.Exit(1)

    try:
        draft, warning = gate.approve(draft_id, queue_updater=_queue_updater)
        if json_out:
            console.print_json(json.dumps(draft.to_dict(), ensure_ascii=False))
            return
        console.print(f"[green]✓ Draft {draft.draft_id[:8]} aprovado[/green] — versão {draft.version}")
        if warning:
            console.print(f"[yellow]Aviso:[/yellow] {warning}")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


# ------------------------------------------------------------------
# content reject
# ------------------------------------------------------------------

@content_app.command(name="reject")
def cmd_reject(
    draft_id: str = typer.Argument(..., help="ID do draft"),
    reason: str = typer.Option(..., "--reason", help="Motivo da rejeição"),
) -> None:
    """Rejeita um draft. --reason é obrigatório."""
    _, gate = _make_gate()
    try:
        draft, warning = gate.reject(draft_id, reason=reason, queue_updater=_queue_updater)
        console.print(f"[yellow]Draft {draft.draft_id[:8]} rejeitado.[/yellow]")
        console.print(f"  Motivo: {reason}")
        if warning:
            console.print(f"[yellow]Aviso:[/yellow] {warning}")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


# ------------------------------------------------------------------
# content report
# ------------------------------------------------------------------

@content_app.command(name="report")
def cmd_report(
    days: int = typer.Option(7, "--days", "-d", help="Período em dias"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Relatório de performance: clips, carrosseis, aprovações, custo (R$0,00)."""
    from src.agencia.performance_report import PerformanceReporter
    reporter = PerformanceReporter()
    report = reporter.generate(period_days=days)

    if json_out:
        import json
        console.print_json(json.dumps(report.to_dict(), ensure_ascii=False))
        return

    console.print(report.summary())


# ------------------------------------------------------------------
# content export
# ------------------------------------------------------------------

@content_app.command(name="export")
def cmd_export(
    account: str = typer.Option("", "--account", "-a", help="Filtra por @perfil"),
    output: str = typer.Option("", "--output", "-o", help="Pasta de destino (default: data/exports/<date>)"),
    dry_run: bool = typer.Option(True, "--dry-run/--real", help="--real escreve arquivos; --dry-run só gera manifesto"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Exporta drafts aprovados em pacote CSV+assets pronto para Publer.

    Por padrão roda em --dry-run (sem copiar assets). Use --real para gerar pasta completa.
    """
    from pathlib import Path
    from src.agencia.export import ContentExporter

    exporter = ContentExporter(dry_run=dry_run)
    result = exporter.export(
        account_filter=account or None,
        export_dir=Path(output) if output else None,
    )

    if json_out:
        import json
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    console.print(f"[green]Export concluido:[/green]")
    console.print(f"  ID:      {result.export_id}")
    console.print(f"  dir:     {result.export_dir}")
    console.print(f"  csv:     {result.csv_path.name}")
    console.print(f"  drafts:  {result.total_drafts}")
    console.print(f"  assets:  {result.total_assets_copied}")
    console.print(f"  dry_run: {result.dry_run}")
    for w in result.warnings:
        console.print(f"  [yellow]AVISO:[/yellow] {w}")


# ------------------------------------------------------------------
# content prepare-publish
# ------------------------------------------------------------------

@content_app.command(name="prepare-publish")
def cmd_prepare_publish(
    account: str = typer.Option("", "--account", "-a", help="Filtra por @perfil"),
    real: bool = typer.Option(False, "--real", help="Gera CSV + ManyChat stub (default: dry-run)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Prepara payload para Publer (CSV) + ManyChat stub. NUNCA publica.

    Por padrão roda em dry-run (gera apenas manifesto).
    Use --real para gerar publer_bulk.csv e manychat_stub.json.
    """
    from src.agencia.publisher_prepare import PublisherPrepare

    prep = PublisherPrepare(dry_run=not real)
    pkg = prep.prepare(account_filter=account or None)

    if json_out:
        import json
        console.print_json(json.dumps(pkg.to_dict(), ensure_ascii=False))
        return

    console.print(pkg.summary())


# ------------------------------------------------------------------
# content status
# ------------------------------------------------------------------

@content_app.command(name="status")
def cmd_status(json_out: bool = typer.Option(False, "--json")) -> None:
    """Contagem de drafts por status."""
    from collections import Counter
    dm, _ = _make_gate()
    counts = Counter(d.status for d in dm.list_all())
    total = sum(counts.values())

    if json_out:
        console.print_json(json.dumps(dict(counts), ensure_ascii=False))
        return

    table = Table(title=f"Content — Status ({total} drafts total)")
    table.add_column("Status", style="cyan")
    table.add_column("Total", justify="right")

    for s, n in sorted(counts.items(), key=lambda x: -x[1]):
        style = "green" if s == "approved" else ("red" if s == "rejected" else "yellow")
        table.add_row(f"[{style}]{s}[/{style}]", str(n))

    console.print(table)

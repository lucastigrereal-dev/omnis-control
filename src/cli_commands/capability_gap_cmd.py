"""CLI for Capability Gap Detector."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

capability_gap_app = typer.Typer(
    name="capability-gap",
    help="Capability Gap Detector — detecta lacunas entre pedido e capabilities disponiveis.",
    add_completion=False,
)
console = Console()


@capability_gap_app.callback()
def _callback():
    """Capability Gap — detecta e registra lacunas de capacidade."""


@capability_gap_app.command(name="detect")
def cmd_detect(
    request: str = typer.Argument(..., help="Pedido para detectar gap"),
    save: bool = typer.Option(True, "--save/--no-save", help="Salvar gap no log"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Detecta gap de capability para um pedido."""
    from src.capability_gap.detector import detect
    from src.capability_gap import store as store_mod
    from src.capability_gap.store import GapStore

    result = detect(request)

    if save and result.gaps:
        store = GapStore(store_mod.DEFAULT_GAPS_LOG)
        for gap in result.gaps:
            store.save(gap)

    if json_out:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    status_color = {"covered": "green", "gap_detected": "yellow", "unknown_sector": "red"}.get(
        result.status, "white"
    )
    console.print(Panel("[bold]Capability Gap Detection[/bold]", expand=False))
    console.print(f"  status  : [{status_color}]{result.status}[/{status_color}]")
    console.print(f"  sector  : {result.sector_id}")
    if result.matched_capabilities:
        console.print(f"  covered : {', '.join(result.matched_capabilities)}")
    if result.gaps:
        for gap in result.gaps:
            console.print(f"\n  [yellow]GAP:[/yellow] {gap.gap_id}")
            console.print(f"    missing   : {gap.missing_capability}")
            console.print(f"    output    : {gap.desired_output}")
            console.print(f"    recommend : {gap.recommendation}")


@capability_gap_app.command(name="list")
def cmd_list(
    limit: int = typer.Option(20, "--limit"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lista gaps registrados."""
    from src.capability_gap import store as store_mod
    from src.capability_gap.store import GapStore

    store = GapStore(store_mod.DEFAULT_GAPS_LOG)
    gaps = store.list_all(limit=limit)

    if json_out:
        console.print_json(json.dumps([g.to_dict() for g in gaps], ensure_ascii=False))
        return

    if not gaps:
        console.print("[dim]Nenhum gap registrado.[/dim]")
        return

    table = Table(title="Capability Gaps")
    table.add_column("gap_id", style="dim")
    table.add_column("sector")
    table.add_column("missing")
    table.add_column("status")
    table.add_column("criado")
    for g in gaps:
        status_color = {"open": "yellow", "covered": "green", "dismissed": "dim", "planned": "blue"}.get(g.status, "white")
        table.add_row(g.gap_id, g.sector, g.missing_capability,
                      f"[{status_color}]{g.status}[/{status_color}]",
                      g.created_at[:10])
    console.print(table)


@capability_gap_app.command(name="show")
def cmd_show(
    gap_id: str = typer.Argument(..., help="ID do gap (gap_...)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Mostra detalhes de um gap."""
    from src.capability_gap import store as store_mod
    from src.capability_gap.store import GapStore

    store = GapStore(store_mod.DEFAULT_GAPS_LOG)
    gap = store.get(gap_id)
    if gap is None:
        console.print(f"[yellow]Gap {gap_id} nao encontrado.[/yellow]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(gap.to_dict(), ensure_ascii=False))
        return

    console.print(Panel(f"[bold]Gap[/bold] — {gap.gap_id}", expand=False))
    console.print(f"  sector    : {gap.sector}")
    console.print(f"  missing   : {gap.missing_capability}")
    console.print(f"  output    : {gap.desired_output}")
    console.print(f"  risk      : {gap.risk_level}")
    console.print(f"  status    : {gap.status}")
    console.print(f"  recommend : {gap.recommendation}")
    console.print(f"  criado    : {gap.created_at}")

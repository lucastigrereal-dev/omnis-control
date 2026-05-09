"""CLI for Capability Forge Lite."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

capability_forge_lite_app = typer.Typer(
    name="forge-lite",
    help="Capability Forge Lite — propoe, especifica e registra capabilities planejadas.",
    add_completion=False,
)
console = Console()


@capability_forge_lite_app.callback()
def _callback():
    """Forge Lite — gap → proposal → spec → approval → planned capability."""


@capability_forge_lite_app.command(name="propose")
def cmd_propose(
    gap_id: str = typer.Argument(..., help="ID do gap (gap_...)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Cria proposta de capability a partir de um gap existente."""
    from src.capability_forge_lite import store as store_mod
    from src.capability_gap import store as gap_store_mod
    from src.capability_forge_lite.proposal import propose_from_gap
    from src.capability_forge_lite.errors import GapNotFoundError

    try:
        proposal = propose_from_gap(
            gap_id,
            gaps_log=gap_store_mod.DEFAULT_GAPS_LOG,
            proposals_log=store_mod.DEFAULT_PROPOSALS_LOG,
        )
    except GapNotFoundError as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(proposal.to_dict(), ensure_ascii=False))
        return

    console.print(Panel("[bold]Capability Proposal Created[/bold]", expand=False))
    console.print(f"  proposal_id  : {proposal.proposal_id}")
    console.print(f"  capability   : {proposal.capability_name}")
    console.print(f"  sector       : {proposal.sector}")
    console.print(f"  risk         : {proposal.risk_level}")
    console.print(f"  impl_type    : {proposal.implementation_type}")
    console.print(f"  status       : [yellow]{proposal.status}[/yellow]")
    if proposal.warnings:
        for w in proposal.warnings:
            console.print(f"  [yellow]warn[/yellow]       : {w}")
    if proposal.next_actions:
        console.print(f"  next         : {proposal.next_actions[0]}")


@capability_forge_lite_app.command(name="list")
def cmd_list(
    limit: int = typer.Option(20, "--limit"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lista proposals existentes."""
    from src.capability_forge_lite import store as store_mod
    from src.capability_forge_lite.store import ProposalStore

    proposals = ProposalStore(store_mod.DEFAULT_PROPOSALS_LOG).list_all(limit=limit)

    if json_out:
        console.print_json(json.dumps([p.to_dict() for p in proposals], ensure_ascii=False))
        return

    if not proposals:
        console.print("[dim]Nenhuma proposal encontrada.[/dim]")
        return

    table = Table(title="Capability Proposals")
    table.add_column("proposal_id", style="dim")
    table.add_column("capability")
    table.add_column("sector")
    table.add_column("risk")
    table.add_column("status")
    for p in proposals:
        color = {
            "draft": "white", "needs_approval": "yellow",
            "approved": "green", "rejected": "red", "registered": "blue",
        }.get(p.status, "white")
        table.add_row(p.proposal_id, p.capability_name, p.sector, p.risk_level,
                      f"[{color}]{p.status}[/{color}]")
    console.print(table)


@capability_forge_lite_app.command(name="show")
def cmd_show(
    proposal_id: str = typer.Argument(..., help="ID da proposal (prop_...)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Mostra detalhes de uma proposal."""
    from src.capability_forge_lite import store as store_mod
    from src.capability_forge_lite.store import ProposalStore

    p = ProposalStore(store_mod.DEFAULT_PROPOSALS_LOG).get(proposal_id)
    if p is None:
        console.print(f"[yellow]Proposal {proposal_id} nao encontrada.[/yellow]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(p.to_dict(), ensure_ascii=False))
        return

    console.print(Panel(f"[bold]Proposal[/bold] — {p.proposal_id}", expand=False))
    console.print(f"  gap_id       : {p.gap_id}")
    console.print(f"  capability   : {p.capability_name}")
    console.print(f"  sector       : {p.sector}")
    console.print(f"  output       : {p.desired_output}")
    console.print(f"  risk         : {p.risk_level}")
    console.print(f"  impl_type    : {p.implementation_type}")
    console.print(f"  status       : {p.status}")
    console.print(f"  approval_req : {p.approval_required}")
    if p.approval_id:
        console.print(f"  approval_id  : {p.approval_id}")
    console.print(f"  criado       : {p.created_at}")


@capability_forge_lite_app.command(name="export-spec")
def cmd_export_spec(
    proposal_id: str = typer.Argument(..., help="ID da proposal (prop_...)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Exporta arquivos de spec para uma proposal."""
    from src.capability_forge_lite import store as store_mod
    from src.capability_forge_lite.spec_exporter import export_spec
    from src.capability_forge_lite.errors import ProposalNotFoundError

    try:
        spec_dir = export_spec(proposal_id, proposals_log=store_mod.DEFAULT_PROPOSALS_LOG)
    except ProposalNotFoundError as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)

    if json_out:
        import json as _json
        console.print_json(_json.dumps({"spec_dir": str(spec_dir)}, ensure_ascii=False))
        return

    console.print(Panel("[bold]Spec Exported[/bold]", expand=False))
    console.print(f"  spec_dir : {spec_dir}")
    console.print("  arquivos : capability_manifest.json, CAPABILITY_SPEC.md,")
    console.print("             implementation_plan.md, risk_assessment.md, next_actions.md")


@capability_forge_lite_app.command(name="validate-spec")
def cmd_validate_spec(
    proposal_id: str = typer.Argument(..., help="ID da proposal (prop_...)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Valida arquivos de spec exportados para uma proposal."""
    from src.capability_forge_lite import store as store_mod
    from src.capability_forge_lite.spec_validator import validate_spec
    from src.capability_forge_lite.errors import ProposalNotFoundError

    try:
        result = validate_spec(proposal_id, proposals_log=store_mod.DEFAULT_PROPOSALS_LOG)
    except ProposalNotFoundError as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)

    if json_out:
        import json as _json
        console.print_json(_json.dumps(result, ensure_ascii=False))
        return

    status_color = "green" if result["valid"] else "red"
    status_text = "VALID" if result["valid"] else "INVALID"
    console.print(Panel(f"[bold]Spec Validation — [{status_color}]{status_text}[/{status_color}][/bold]", expand=False))
    console.print(f"  proposal_id    : {result['proposal_id']}")
    console.print(f"  spec_dir       : {result['spec_dir']}")
    console.print(f"  files_present  : {len(result['files_present'])}/5")
    if result["files_missing"]:
        for f in result["files_missing"]:
            console.print(f"  [red]missing[/red]       : {f}")
    console.print(f"  manifest_valid : {result['manifest_valid']}")
    if result["manifest_errors"]:
        for err in result["manifest_errors"]:
            console.print(f"  [red]error[/red]         : {err}")
    console.print(f"  no_secrets     : {result['no_secrets']}")
    if not result["valid"]:
        raise typer.Exit(1)


@capability_forge_lite_app.command(name="request-approval")
def cmd_request_approval(
    proposal_id: str = typer.Argument(..., help="ID da proposal (prop_...)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Cria pedido de aprovacao para uma proposal no Approval Center."""
    import json as _json
    from src.capability_forge_lite import store as store_mod
    from src.approval_center import store as approval_store_mod
    from src.capability_forge_lite.approval_bridge import request_proposal_approval
    from src.capability_forge_lite.errors import ProposalNotFoundError

    try:
        request_id = request_proposal_approval(
            proposal_id,
            proposals_log=store_mod.DEFAULT_PROPOSALS_LOG,
            approvals_log=approval_store_mod.DEFAULT_APPROVALS_LOG,
        )
    except ProposalNotFoundError as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(_json.dumps({"request_id": request_id, "proposal_id": proposal_id}, ensure_ascii=False))
        return

    console.print(Panel("[bold]Approval Request Created[/bold]", expand=False))
    console.print(f"  request_id  : {request_id}")
    console.print(f"  proposal_id : {proposal_id}")
    console.print(f"  next        : jarvis forge-lite mark-approved {proposal_id}")


@capability_forge_lite_app.command(name="mark-approved")
def cmd_mark_approved(
    proposal_id: str = typer.Argument(..., help="ID da proposal (prop_...)"),
    note: str = typer.Option("", "--note"),
) -> None:
    """Marca proposta como aprovada (resolve o pedido de aprovacao)."""
    from src.capability_forge_lite import store as store_mod
    from src.approval_center import store as approval_store_mod
    from src.capability_forge_lite.approval_bridge import mark_proposal_approved
    from src.capability_forge_lite.errors import ProposalNotFoundError, ProposalNotApprovedError

    try:
        mark_proposal_approved(
            proposal_id,
            note=note,
            proposals_log=store_mod.DEFAULT_PROPOSALS_LOG,
            approvals_log=approval_store_mod.DEFAULT_APPROVALS_LOG,
        )
    except (ProposalNotFoundError, ProposalNotApprovedError) as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Proposal {proposal_id} aprovada.[/green]")
    console.print(f"  next : jarvis forge-lite register {proposal_id}")


@capability_forge_lite_app.command(name="mark-rejected")
def cmd_mark_rejected(
    proposal_id: str = typer.Argument(..., help="ID da proposal (prop_...)"),
    note: str = typer.Option("", "--note"),
) -> None:
    """Marca proposta como rejeitada."""
    from src.capability_forge_lite import store as store_mod
    from src.approval_center import store as approval_store_mod
    from src.capability_forge_lite.approval_bridge import mark_proposal_rejected
    from src.capability_forge_lite.errors import ProposalNotFoundError, ProposalNotApprovedError

    try:
        mark_proposal_rejected(
            proposal_id,
            note=note,
            proposals_log=store_mod.DEFAULT_PROPOSALS_LOG,
            approvals_log=approval_store_mod.DEFAULT_APPROVALS_LOG,
        )
    except (ProposalNotFoundError, ProposalNotApprovedError) as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[yellow]Proposal {proposal_id} rejeitada.[/yellow]")


@capability_forge_lite_app.command(name="register")
def cmd_register(
    proposal_id: str = typer.Argument(..., help="ID da proposal aprovada (prop_...)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Registra capability aprovada em capabilities.yaml como 'planned'."""
    import json as _json
    from src.capability_forge_lite import store as store_mod
    from src.capability_forge_lite.registrar import register_capability
    from src.capability_forge_lite.errors import (
        ProposalNotFoundError,
        ProposalNotApprovedError,
        DuplicateCapabilityError,
    )

    try:
        cap_id = register_capability(proposal_id, proposals_log=store_mod.DEFAULT_PROPOSALS_LOG)
    except ProposalNotFoundError as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)
    except ProposalNotApprovedError as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)
    except DuplicateCapabilityError as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(_json.dumps({"capability_id": cap_id, "status": "planned"}, ensure_ascii=False))
        return

    console.print(Panel("[bold]Capability Registered[/bold]", expand=False))
    console.print(f"  capability_id : {cap_id}")
    console.print(f"  status        : [blue]planned[/blue]")
    console.print(f"  file          : config/capabilities.yaml")

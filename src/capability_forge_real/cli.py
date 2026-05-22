"""Capability Forge Real CLI — merged argparse + typer commands."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer

from src.capability_forge_real.store import ProposalStore
from src.capability_forge_real import store as store_mod
from src.capability_forge_real.builder import CapabilityBuilder
from src.capability_forge_real.models import BuildResult
from src.capability_forge_real.orchestrator import CapabilityForge
from src.capability_forge_real.registrymanager import RegistryManager

forge = CapabilityForge()
registry = RegistryManager()

forge_app = typer.Typer(
    name="forge",
    help="Capability Forge — fabrica governada de skills",
    add_completion=False,
)


def cmd_build(args) -> int:
    """Build code for an approved proposal."""
    store = ProposalStore(store_mod.DEFAULT_PROPOSALS_LOG)
    proposal = store.get(args.proposal_id)
    if proposal is None:
        print(f"Proposal {args.proposal_id} not found", file=sys.stderr)
        return 1

    builder = CapabilityBuilder(dry_run=args.dry_run)
    try:
        result = builder.build(proposal)
        if result.is_success:
            print(f"Build {result.build_id}: DONE — {result.capability_name}")
            print(f"  Files: {result.files_created}")
            print(f"  Tests: {result.test_count}")
            print(f"  Policy: {'PASS' if result.policy_scan['passed'] else 'FAIL'}")
        else:
            print(f"Build {result.build_id}: FAILED ({result.state})", file=sys.stderr)
            if result.policy_scan.get("violations"):
                for v in result.policy_scan["violations"]:
                    print(f"  Policy violation: {v['description']}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Build error: {e}", file=sys.stderr)
        return 1

    return 0


def cmd_status(args) -> int:
    """Check build status (stub — BuildResult is ephemeral)."""
    print(f"Build {args.build_id}: status tracking is ephemeral")
    print("BuildResults are not persisted. Re-run build to see current state.")
    return 0


def cmd_rollback(args) -> int:
    """Remove files from a failed build."""
    builder = CapabilityBuilder(dry_run=False)
    try:
        builder.rollback_files(args.files)
        print(f"Rollback: removed {len(args.files)} file(s)")
    except Exception as e:
        print(f"Rollback error: {e}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="forge-real")
    sub = parser.add_subparsers(dest="command")

    # build
    build_p = sub.add_parser("build", help="Build skill from approved proposal")
    build_p.add_argument("proposal_id")
    build_p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    build_p.add_argument("--no-dry-run", dest="dry_run", action="store_false")

    # status
    status_p = sub.add_parser("status", help="Check build status")
    status_p.add_argument("build_id")

    # rollback
    rollback_p = sub.add_parser("rollback", help="Rollback files")
    rollback_p.add_argument("files", nargs="+")

    args = parser.parse_args()
    if args.command == "build":
        return cmd_build(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "rollback":
        return cmd_rollback(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


# ── Typer forge_app commands ──────────────────────────────────────────────────

@forge_app.command(name="propose")
def propose(
    gap: str = typer.Argument(..., help="Descricao da lacuna/necessidade"),
    sector: str = typer.Option(..., "--sector", help="Setor: marketing, sales, operations..."),
    name: str = typer.Option("", "--name", help="Nome sugerido para a skill"),
):
    """Detecta gap e propoe spec de nova skill."""
    result = asyncio.run(forge.propose_skill(gap, sector, name))
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


@forge_app.command(name="approve")
def approve(
    name: str = typer.Argument(..., help="Nome da skill"),
    approver: str = typer.Option("lucas", "--approver", help="Identificacao do aprovador"),
):
    """Aprova uma skill gerada para status 'approved'."""
    result = asyncio.run(forge.approve_skill(name, approver))
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


@forge_app.command(name="list")
def list_skills(
    status: Optional[str] = typer.Option(None, "--status", help="Filtrar por status"),
    sector: Optional[str] = typer.Option(None, "--sector", help="Filtrar por setor"),
):
    """Lista skills no registry."""
    if status:
        skills = registry.list_by_status(status)
    elif sector:
        skills = registry.list_by_sector(sector)
    else:
        skills = registry._load_all()
    typer.echo(json.dumps(skills, indent=2, ensure_ascii=False, default=str))


@forge_app.command(name="audit")
def audit(
    name: str = typer.Argument(..., help="Nome da skill"),
):
    """Executa policy check em uma skill do registry."""
    from src.capability_forge_real.policy import PolicyEngine
    entry = registry.get(name)
    if not entry:
        typer.echo(f"Skill '{name}' nao encontrada.")
        return
    engine = PolicyEngine()
    report = engine.check_file(Path(entry["path"]) / "run.py") if entry.get("path") else None
    if report:
        typer.echo(report.summary())
    else:
        typer.echo("Sem arquivo run.py para auditar.")

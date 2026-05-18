"""
OMNIS local command group.
All commands run with dry_run=True by default — they print what they WOULD do
and generate a minimal Mission Package stub in missions/.
No real API calls, no external integrations.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(
    name="local",
    help="Local OMNIS commands — dry_run=True, no external calls",
    add_completion=False,
)
console = Console()

MISSIONS_DIR = Path(__file__).parent.parent / "missions"


def _create_mission_stub(
    mission_type: str,
    params: dict,
    missions_dir: Path | None = None,
) -> Path:
    """Create a minimal Mission Package stub: mission_contract.json + 01_mission_brief.md."""
    base = missions_dir or MISSIONS_DIR
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = mission_type.lower().replace(" ", "_")
    folder = base / f"{slug}_{ts}"
    folder.mkdir(parents=True, exist_ok=True)

    contract = {
        "mission_type": mission_type,
        "params": params,
        "dry_run": True,
        "created_at": ts,
        "status": "stub",
    }
    (folder / "mission_contract.json").write_text(
        json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    brief_lines = [
        f"# Mission Brief — {mission_type}",
        "",
        f"**Created:** {ts}",
        f"**dry_run:** True",
        "",
        "## Parameters",
        "",
    ]
    for k, v in params.items():
        brief_lines.append(f"- **{k}:** {v}")
    brief_lines += [
        "",
        "## Status",
        "stub — awaiting operator approval",
    ]
    (folder / "01_mission_brief.md").write_text(
        "\n".join(brief_lines), encoding="utf-8"
    )

    return folder


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


@app.command()
def campaign(
    profile: str = typer.Option(..., help="Instagram profile handle"),
    theme: str = typer.Option(..., help="Campaign theme"),
    objective: str = typer.Option(..., help="Campaign objective"),
):
    """[DRY RUN] Generate a campaign mission stub."""
    params = {"profile": profile, "theme": theme, "objective": objective}
    folder = _create_mission_stub("campaign", params)
    console.print(
        Panel(
            f"[bold green]DRY RUN — campaign stub created[/bold green]\n"
            f"Profile   : {profile}\n"
            f"Theme     : {theme}\n"
            f"Objective : {objective}\n"
            f"Stub path : {folder}",
            title="omnis local campaign",
        )
    )


@app.command()
def carousel(
    profile: str = typer.Option(..., help="Instagram profile handle"),
    theme: str = typer.Option(..., help="Carousel theme"),
):
    """[DRY RUN] Generate a carousel mission stub."""
    params = {"profile": profile, "theme": theme}
    folder = _create_mission_stub("carousel", params)
    console.print(
        Panel(
            f"[bold green]DRY RUN — carousel stub created[/bold green]\n"
            f"Profile : {profile}\n"
            f"Theme   : {theme}\n"
            f"Stub path: {folder}",
            title="omnis local carousel",
        )
    )


@app.command()
def reels(
    profile: str = typer.Option(..., help="Instagram profile handle"),
    theme: str = typer.Option(..., help="Reels theme"),
):
    """[DRY RUN] Generate a reels mission stub."""
    params = {"profile": profile, "theme": theme}
    folder = _create_mission_stub("reels", params)
    console.print(
        Panel(
            f"[bold green]DRY RUN — reels stub created[/bold green]\n"
            f"Profile  : {profile}\n"
            f"Theme    : {theme}\n"
            f"Stub path: {folder}",
            title="omnis local reels",
        )
    )


@app.command(name="app")
def app_cmd(
    name: str = typer.Option(..., help="Application name"),
    domain: str = typer.Option(..., help="Application domain"),
):
    """[DRY RUN] Generate an app-factory mission stub."""
    params = {"name": name, "domain": domain}
    folder = _create_mission_stub("app_factory", params)
    console.print(
        Panel(
            f"[bold green]DRY RUN — app stub created[/bold green]\n"
            f"Name   : {name}\n"
            f"Domain : {domain}\n"
            f"Stub path: {folder}",
            title="omnis local app",
        )
    )


@app.command()
def forge(
    skill_name: str = typer.Option(..., help="Name of the skill to forge"),
    description: str = typer.Option(..., help="Skill description"),
):
    """[DRY RUN] Generate a forge/skill-creation mission stub."""
    params = {"skill_name": skill_name, "description": description}
    folder = _create_mission_stub("forge", params)
    console.print(
        Panel(
            f"[bold green]DRY RUN — forge stub created[/bold green]\n"
            f"Skill name  : {skill_name}\n"
            f"Description : {description}\n"
            f"Stub path   : {folder}",
            title="omnis local forge",
        )
    )


@app.command()
def cockpit():
    """Print path to cockpit/index.html (or open it if available)."""
    cockpit_path = Path(__file__).parent.parent / "cockpit" / "index.html"
    if cockpit_path.exists():
        console.print(
            Panel(
                f"[bold cyan]Cockpit found:[/bold cyan] {cockpit_path}\n"
                "Open the path above in your browser.",
                title="omnis local cockpit",
            )
        )
    else:
        console.print(
            Panel(
                f"[yellow]Cockpit not found at:[/yellow] {cockpit_path}\n"
                "Generate cockpit first via: python src/reports/cockpit_generator.py",
                title="omnis local cockpit",
            )
        )


@app.command()
def status():
    """Print summary of the missions/ directory."""
    missions_base = MISSIONS_DIR
    if not missions_base.exists():
        console.print(
            Panel(
                f"[yellow]missions/ directory not found at {missions_base}[/yellow]\n"
                "No missions created yet.",
                title="omnis local status",
            )
        )
        return

    folders = sorted(missions_base.iterdir()) if missions_base.is_dir() else []
    mission_entries = [f for f in folders if f.is_dir()]

    if not mission_entries:
        console.print(
            Panel("[yellow]No mission stubs found in missions/[/yellow]", title="omnis local status")
        )
        return

    lines = [f"[bold]Total missions:[/bold] {len(mission_entries)}", ""]
    for m in mission_entries:
        contract_file = m / "mission_contract.json"
        if contract_file.exists():
            try:
                data = json.loads(contract_file.read_text(encoding="utf-8"))
                mtype = data.get("mission_type", "unknown")
                mstatus = data.get("status", "unknown")
                lines.append(f"  [cyan]{m.name}[/cyan]  type={mtype}  status={mstatus}")
            except Exception:
                lines.append(f"  [cyan]{m.name}[/cyan]  (unreadable contract)")
        else:
            lines.append(f"  [cyan]{m.name}[/cyan]  (no contract)")

    console.print(Panel("\n".join(lines), title="omnis local status — missions/"))

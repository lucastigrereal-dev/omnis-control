"""
OMNIS / omnis-control — Cabine mínima de controle do ecossistema.

Uso:
    python jarvis.py status
    python jarvis.py skills
    python jarvis.py doctor
    python jarvis.py report
"""

import time
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.utils.logger import new_session_id, log_mission, log_tool_run
from src.utils.safe_paths import validate_skill_name
from src.checkers import (
    skills_check,
    docker_check,
    publisher_check,
    memory_check,
    obsidian_check,
    disk_check,
    video_pipeline_check,
)
from src.runners.skill_runner import run_skill as _run_skill
from src.reports import status_report
from src.video_assets import Registry, Scanner, Queue as VAQueue, AssetStatus, VideoAsset
from src.content_queue import AccountRegistry, Queue as CQQueue, Account, QueueItem, QueueStatus
from src.caption_approval import DraftsManager, ApprovalGate, TemplateLibrary
from src.caption_approval.models import DraftStatus
from src.caption_approval.drafts import STALE_DAYS
from src.reports import briefing as briefing_mod
from src.app_factory.idea_cli import idea_app
from src.cli_local import app as local_app
from src.cli_commands.content_cmd import content_app
from src.cli_commands.mission_cmd import runs_app
from src.cli_commands.notion_cmd import notion_app
from src.cli_commands.akasha_cmd import akasha_app

app = typer.Typer(
    name="jarvis",
    help="OMNIS — Cabine mínima de controle do ecossistema",
    add_completion=False,
)
console = Console()

_OMNIS_ROOT = os.path.normpath(
    os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control"))
)
_CLAUDE_DIR = os.path.normpath(
    os.getenv("CLAUDE_DIR", os.path.expanduser("~/.claude"))
)
_DAILY_PROPHET_DIR = os.path.normpath(
    os.getenv("DAILY_PROPHET_DIR", os.path.expanduser("~/daily-prophet-hotels"))
)
_LLM_ROUTER_DIR = os.path.normpath(
    os.getenv("LLM_ROUTER_DIR", os.path.expanduser("~/llm-router"))
)

PATHS_YAML = os.path.join(_OMNIS_ROOT, "config", "paths.yaml")


def _load_paths_config() -> dict:
    if os.path.isfile(PATHS_YAML):
        try:
            with open(PATHS_YAML, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError:
            return {}
    return {}


def _check_path(path: str) -> str:
    expanded = os.path.expanduser(path)
    if os.path.isdir(expanded):
        return "[OK]"
    return "[!!]"


def _disk_severity(disk: dict) -> str:
    if disk["severity"] == "critical":
        return "[bold red]CRÍTICO[/bold red]"
    elif disk["severity"] == "warning":
        return "[yellow]ALERTA[/yellow]"
    return "[green]OK[/green]"


# ---------------------------------------------------------------------------
# COMMANDS
# ---------------------------------------------------------------------------


@app.command()
def status():
    """Saúde geral dos 8 componentes do ecossistema (idempotente).

    Não modifica nada fora de logs/missions.jsonl.
    Não altera paths.yaml.
    Pode ser rodado múltiplas vezes sem efeito colateral.
    """
    session_id = new_session_id()
    start = time.time()

    config = _load_paths_config()
    paths = config.get("paths", {})
    services = config.get("services", {})

    skills = skills_check.check()
    docker = docker_check.check()
    publisher = publisher_check.check()
    memory = memory_check.check()
    obsidian = obsidian_check.check()
    disk = disk_check.check()

    # Path health table
    path_table = Table(title="Caminhos", show_header=True)
    path_table.add_column("Path", style="cyan")
    path_table.add_column("Status")
    if paths:
        path_table.add_row(".claude/skills", _check_path(paths.get("claude_skills_path", "")))
        path_table.add_row("publisher-os", _check_path(paths.get("publisher_os_path", "")))
        path_table.add_row("JARVIS_OS docs", _check_path(paths.get("jarvis_os_docs_path", "")))
        path_table.add_row("Obsidian vault", _check_path(paths.get("obsidian_vault_path", "")))

    console.print(Panel(path_table, title="[bold]OMNIS — Status do Ecossistema[/bold]"))

    # Summary table
    summary = Table.grid()
    summary.add_column()
    summary.add_column()
    summary.add_row("[cyan]Skills[/cyan]", f"{skills['total']} ({skills['executable']} executáveis)")
    summary.add_row("[cyan]Docker[/cyan]", f"{docker['containers_running']} rodando")
    if docker["containers_unhealthy"]:
        summary.add_row("", f"[red]{docker['containers_unhealthy']} unhealthy[/red]")
    summary.add_row("[cyan]Publisher OS[/cyan]", f"{publisher['status']}")
    summary.add_row("[cyan]Qdrant[/cyan]", "[OK] acessível" if memory.get("qdrant", {}).get("accessible") else "[!!] inacessível")
    summary.add_row("[cyan]Akasha[/cyan]", "[OK] encontrado" if memory.get("akasha", {}).get("container_found") else "[!!] não encontrado")
    summary.add_row("[cyan]Obsidian[/cyan]", f"{obsidian.get('md_file_count', '?')} .md files" if obsidian.get("vault_found") else "[!!] vault não encontrado")

    disk_text = _disk_severity(disk)
    summary.add_row("[cyan]Disco[/cyan]", disk_text)
    if disk.get("critical"):
        for d in disk["disks"]:
            if d["percent_free"] < 10:
                summary.add_row("", f"[red][WARN] {d['mount']}: {d['percent_free']}% livre ({d['free_gb']} GB)[/red]")

    console.print(Panel(summary, title="Resumo"))

    dur = int((time.time() - start) * 1000)
    has_warnings = docker["containers_unhealthy"] > 0 or disk["severity"] in ("warning", "critical")
    log_mission(
        session_id=session_id,
        command="status",
        status="warning" if has_warnings else "success",
        duration_ms=dur,
        summary=f"{skills['total']} skills, {docker['containers_running']} containers, publisher={publisher['status']}",
    )


@app.command()
def skills():
    """Lista todas as skills detectadas, classificadas por tipo."""
    session_id = new_session_id()
    start = time.time()

    data = skills_check.check()
    table = Table(title=f"Skills ({data['total']} encontradas)")
    table.add_column("Tipo", style="cyan")
    table.add_column("Nome")
    table.add_column("run.py?", style="green")
    table.add_column("SKILL.md?")

    for e in data.get("executable_list", []):
        table.add_row("executable", e, "[OK]", "—")
    for e in data.get("doc_folder_list", []):
        table.add_row("doc_folder", e, "—", "[OK]")
    for e in data.get("doc_file_list", []):
        table.add_row("doc_file", e, "—", "—")

    console.print(table)

    if data.get("orphan_skills"):
        console.print(f"\n[yellow]Skills órfãs (disco mas sem registry):[/yellow]")
        for s in data["orphan_skills"][:10]:
            console.print(f"  {s}")

    dur = int((time.time() - start) * 1000)
    log_mission(session_id, "skills", "success", dur)


@app.command()
def skill_info(skill_name: str = typer.Argument(..., help="Nome da skill")):
    """Mostra detalhes de uma skill específica."""
    session_id = new_session_id()
    start = time.time()

    try:
        name = validate_skill_name(skill_name)
    except ValueError as e:
        console.print(f"[red]Erro:[/red] {e}")
        log_mission(session_id, "skill-info", "error", int((time.time()-start)*1000), errors=[str(e)])
        raise typer.Exit(1)

    skills_dir = os.path.join(_CLAUDE_DIR, "skills")
    entry_path = os.path.join(skills_dir, name)

    info = {
        "name": name,
        "exists": os.path.exists(entry_path),
        "is_dir": os.path.isdir(entry_path),
        "has_run": os.path.isfile(os.path.join(entry_path, "run.py")),
        "has_skill_md": os.path.isfile(os.path.join(entry_path, "SKILL.md")),
    }

    if info["has_run"]:
        info["type"] = "executable"
    elif info["is_dir"]:
        info["type"] = "doc_folder"
    elif os.path.isfile(os.path.join(skills_dir, f"{name}.md")):
        info["type"] = "doc_file"
        info["exists"] = True
    else:
        info["type"] = "not_found"

    table = Table(title=f"Skill: {name}")
    table.add_column("Propriedade", style="cyan")
    table.add_column("Valor")
    table.add_row("Nome", name)
    table.add_row("Tipo", info["type"])
    table.add_row("Caminho", entry_path)
    table.add_row("Existe?", "[OK]" if info["exists"] else "[!!]")
    table.add_row("Tem run.py?", "[OK]" if info["has_run"] else "—")
    table.add_row("Tem SKILL.md?", "[OK]" if info["has_skill_md"] else "—")
    console.print(table)

    dur = int((time.time() - start) * 1000)
    log_mission(session_id, "skill-info", "success", dur)


@app.command()
def run_skill(
    skill_name: str = typer.Argument(..., help="Nome da skill para executar"),
    payload: str = typer.Option(None, "--payload", help="Caminho para arquivo JSON de payload"),
    timeout: int = typer.Option(60, "--timeout", help="Timeout em segundos (max 300)"),
    yes: bool = typer.Option(False, "--yes", help="Confirma a execução"),
):
    """Executa uma skill Python com run.py e timeout obrigatório.

    Sem --yes, faz apenas dry-run.
    """
    session_id = new_session_id()
    start = time.time()

    try:
        result = _run_skill(
            skill_name=skill_name,
            payload_path=payload,
            timeout=timeout,
            dry_run=not yes,
        )
    except (ValueError, PermissionError) as e:
        console.print(f"[red]Erro:[/red] {e}")
        log_mission(session_id, "run-skill", "error", int((time.time()-start)*1000), errors=[str(e)])
        raise typer.Exit(1)

    if result["status"] == "dry_run":
        console.print(f"[yellow]{result['message']}[/yellow]")
        console.print(f"[dim]Comando: {result['command']}[/dim]")
        log_mission(session_id, "run-skill", "dry_run", int((time.time()-start)*1000))
        return

    # Log execution
    log_tool_run(
        session_id=session_id,
        skill=skill_name,
        payload_file=payload or "",
        status=result["status"],
        stdout_preview=result.get("stdout_preview", ""),
        stderr_preview=result.get("stderr_preview", ""),
        duration_ms=result.get("duration_ms", 0),
        timeout_used=timeout,
    )

    if result["status"] == "success":
        console.print(f"[green]Skill '{skill_name}' executada com sucesso[/green]")
        console.print(f"Duração: {result['duration_ms']}ms")
        if result.get("stdout"):
            console.print(Panel(result["stdout"][:2000], title="stdout"))
        if result.get("stderr"):
            console.print(Panel(result["stderr"][:2000], title="stderr", style="red"))
    elif result["status"] == "timeout":
        console.print(f"[red]Skill '{skill_name}' excedeu timeout de {timeout}s[/red]")
    else:
        console.print(f"[red]Skill '{skill_name}' falhou (exit code {result['returncode']})[/red]")
        if result.get("stderr"):
            console.print(Panel(result["stderr"][:2000], title="stderr", style="red"))

    mission_status = result["status"]
    log_mission(session_id, "run-skill", mission_status, int((time.time()-start)*1000))


@app.command(name="publisher-health")
def publisher_health():
    """Verifica saúde do Publisher OS na porta 8000."""
    session_id = new_session_id()
    start = time.time()

    result = publisher_check.check()
    if result["status"] == "ok":
        console.print(f"[green]Publisher OS: {result['status']}[/green]")
        if result.get("identify_hint"):
            console.print(f"  {result['identify_hint']}")
    elif result["status"] == "port_closed":
        console.print(f"[red]Publisher OS: porta 8000 não responde[/red]")
    else:
        console.print(f"[yellow]Publisher OS: {result['status']}[/yellow]")

    console.print(f"  Endpoints testados: {len(result.get('tried_endpoints', []))}")
    log_mission(session_id, "publisher-health", result["status"], int((time.time()-start)*1000))


@app.command(name="docker-status")
def docker_status():
    """Lista containers Docker (read-only)."""
    session_id = new_session_id()
    start = time.time()

    result = docker_check.check()
    if result.get("error"):
        console.print(f"[red]Erro Docker: {result['error']}[/red]")
        log_mission(session_id, "docker-status", "error", int((time.time()-start)*1000), errors=[result["error"]])
        return

    table = Table(title=f"Containers ({result['containers_running']} rodando)")
    table.add_column("Nome", style="cyan")
    table.add_column("Status")
    table.add_column("Imagem")
    table.add_column("Portas")

    for c in result["containers"]:
        indicator = "[UNHEALTHY]" if c["unhealthy"] else "[OK]"
        table.add_row(f"{indicator} {c['name']}", c["status"][:30], c["image"][:30], c.get("ports", "")[:40])
    console.print(table)

    log_mission(session_id, "docker-status", "success", int((time.time()-start)*1000))


@app.command(name="memory-status")
def memory_status():
    """Verifica Qdrant e Akasha."""
    session_id = new_session_id()
    start = time.time()

    result = memory_check.check()

    q = result.get("qdrant", {})
    console.print("[bold]Qdrant[/bold]")
    if q.get("accessible"):
        console.print(f"  [OK] acessível em localhost:6333")
        console.print(f"  Coleções: {q.get('collections_count', 0)}")
        for col in q.get("collections", []):
            console.print(f"    - {col}")
    else:
        console.print(f"  [!!] {q.get('error', 'inacessível')}")

    a = result.get("akasha", {})
    console.print("\n[bold]Akasha (PostgreSQL+pgvector)[/bold]")
    if a.get("container_found"):
        console.print(f"  [OK] Container encontrado ({a.get('status', 'unknown')})")
    else:
        console.print(f"  [!!] Container não encontrado")

    log_mission(session_id, "memory-status", result.get("overall", "ok"), int((time.time()-start)*1000))


@app.command(name="obsidian-status")
def obsidian_status():
    """Verifica vault Obsidian."""
    session_id = new_session_id()
    start = time.time()

    result = obsidian_check.check()
    if result.get("vault_found"):
        console.print(f"[green][OK] Vault encontrado[/green]")
        console.print(f"  Caminho: {result['vault_path']}")
        console.print(f"  Arquivos .md: {result.get('md_file_count', 'timeout')}")
        if result.get("top_folders"):
            console.print(f"  Pastas:")
            for f in result["top_folders"][:10]:
                console.print(f"    - {os.path.basename(f)}")
    else:
        console.print(f"[red][!!] vault não encontrado[/red]")
        console.print(f"  Caminho testado: {result['vault_path']}")

    log_mission(session_id, "obsidian-status", "success" if result.get("vault_found") else "error", int((time.time()-start)*1000))


@app.command()
def doctor():
    """Roda todos os checks e gera diagnóstico JSON no stdout.

    Uso: jarvis doctor > diagnose.json
    """
    session_id = new_session_id()
    start_total = time.time()

    checks = {}
    errors = []
    healthy = 0
    warnings_count = 0

    try:
        d = disk_check.check()
        checks["disk"] = d
        if d["severity"] == "critical":
            warnings_count += 1
            errors.append(f"Disco crítico: {d.get('critical', [])}")
        elif d["severity"] == "warning":
            warnings_count += 1
        else:
            healthy += 1
    except Exception as e:
        checks["disk"] = {"error": str(e)}
        errors.append(str(e))

    try:
        checks["docker"] = docker_check.check()
        if checks["docker"].get("containers_unhealthy", 0) > 0:
            warnings_count += 1
        else:
            healthy += 1
    except Exception as e:
        checks["docker"] = {"error": str(e)}
        errors.append(str(e))

    try:
        checks["publisher"] = publisher_check.check()
        healthy += 1
    except Exception as e:
        checks["publisher"] = {"error": str(e)}
        errors.append(str(e))

    try:
        checks["memory"] = memory_check.check()
        healthy += 1
    except Exception as e:
        checks["memory"] = {"error": str(e)}
        errors.append(str(e))

    try:
        checks["obsidian"] = obsidian_check.check()
        healthy += 1
    except Exception as e:
        checks["obsidian"] = {"error": str(e)}
        errors.append(str(e))

    try:
        checks["skills"] = skills_check.check()
        healthy += 1
    except Exception as e:
        checks["skills"] = {"error": str(e)}
        errors.append(str(e))

    try:
        checks["video_pipeline"] = video_pipeline_check.check()
        healthy += 1
    except Exception as e:
        checks["video_pipeline"] = {"error": str(e)}
        errors.append(str(e))

    # Content Queue health
    try:
        from src.content_queue import AccountRegistry, Queue as CQQueue
        cq_reg = AccountRegistry()
        cq_queue = CQQueue()
        checks["content_queue"] = {
            "accounts_total": cq_reg.count(),
            "accounts_active": len(cq_reg.list_active()),
            "queue_total": len(cq_queue.list_all()),
            "queue_stats": cq_queue.stats(),
        }
        healthy += 1
    except Exception as e:
        checks["content_queue"] = {"error": str(e)}
        errors.append(str(e))

    # Caption Approval health
    try:
        from src.caption_approval import DraftsManager
        from src.caption_approval.drafts import STALE_DAYS
        dm = DraftsManager()
        all_drafts = dm.list_all()
        stale = dm.check_stale()
        by_status = {}
        for d in all_drafts:
            by_status[d.status] = by_status.get(d.status, 0) + 1
        checks["caption_approval"] = {
            "total_drafts": len(all_drafts),
            "by_status": by_status,
            "pending_review": by_status.get("needs_review", 0) + by_status.get("revised", 0),
            "stale_count": len(stale),
            "stale_ids": [s.draft_id[:8] for s in stale[:10]],
        }
        healthy += 1
    except Exception as e:
        checks["caption_approval"] = {"error": str(e)}
        errors.append(str(e))

    # ── Argos Bridge ────────────────────────────────────
    try:
        from src.argos_bridge.draft_builder import stats as argos_stats
        argos = argos_stats()
        checks["argos_bridge"] = {
            "total_drafts": argos["total"],
            "by_status": argos["by_status"],
            "by_account": argos["by_account"],
            "with_warnings": argos["with_warnings"],
        }
    except Exception as e:
        checks["argos_bridge"] = {"error": str(e)}

    total_dur = int((time.time() - start_total) * 1000)

    if errors:
        overall = "critical"
    elif warnings_count > 0:
        overall = "warning"
    else:
        overall = "ok"

    # Build unified HealthReport model
    from src.omnis_health.models import HealthStatus, CheckResult, HealthReport

    normalized_checks = []
    for name, data in checks.items():
        if isinstance(data, dict) and "error" in data and data["error"]:
            status = HealthStatus.ERROR
        else:
            status = HealthStatus.OK
        normalized_checks.append(CheckResult(name=name, status=status, data=data))

    report = HealthReport(
        session_id=session_id,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        overall_status=HealthStatus(overall),
        checks=normalized_checks,
        risks=[],
        next_steps=[
            "Fase 3: OAuth Meta + Publisher OS — configurar META_APP_SECRET, rodar OAuth, conectar fila",
            "Fase 4: Memória conectada — Obsidian read-only -> Qdrant search -> Akasha discovery",
            "Fase 5: Saneamento Docker — limpeza de imagens e volumes não utilizados",
        ],
    )

    log_mission(session_id, "doctor", overall, total_dur, summary=f"healthy={healthy}, warnings={warnings_count}, errors={len(errors)}")

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    output = report.to_dict()
    invoked_from_shim = os.path.basename(sys.argv[0]) in {"omnis.py", "jarvis.py"}
    if invoked_from_shim:
        output["checks"] = checks
    print(json.dumps(output, indent=2, ensure_ascii=False))


@app.command()
def report():
    """Gera docs/ESTADO_ATUAL_RESUMIDO.md com snapshot do ecossistema.

    Atualiza last_validated em paths.yaml.
    """
    session_id = new_session_id()
    start = time.time()

    content = status_report.generate(session_id)
    report_path = os.path.join(_OMNIS_ROOT, "docs", "ESTADO_ATUAL_RESUMIDO.md")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"[green]Relatório gerado:[/green] {report_path}")

        # Update last_validated in paths.yaml
        config_path = os.path.join(_OMNIS_ROOT, "config", "paths.yaml")
        if os.path.isfile(config_path):
            try:
                with open(config_path, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                cfg.setdefault("_metadata", {})["last_validated"] = (
                    datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                )
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(cfg, f, default_flow_style=False, allow_unicode=True)
            except (yaml.YAMLError, OSError):
                pass

    except OSError as e:
        console.print(f"[red]Erro ao gerar relatório:[/red] {e}")
        log_mission(session_id, "report", "error", int((time.time()-start)*1000), errors=[str(e)])
        raise typer.Exit(1)

    dur = int((time.time() - start) * 1000)
    log_mission(session_id, "report", "success", dur)


@app.command()
def disk():
    """Analisa uso de disco — read-only."""
    import subprocess, sys
    subprocess.run([sys.executable, "scripts/disk_analyze.py"])


@app.command()
def briefing(save: bool = typer.Option(False, "--save")):
    """Health score + top 3 acoes do dia."""
    print(briefing_mod.generate(save=save))


@app.command()
def sectors(
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Lista setores do ecossistema com status."""
    from src.checkers import sectors_check
    result = sectors_check.check()

    if json_output:
        import json as _json
        print(_json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print("[bold]Setores do Ecossistema[/bold]\n")
    for s in result.get("sectors", []):
        status_icon = {"operational": "[green]●[/green]", "partial": "[yellow]◐[/yellow]", "blueprint": "[dim]○[/dim]"}.get(s["status"], "[dim]?[/dim]")
        console.print(f"  {status_icon} [cyan]{s['id']:<30}[/cyan] {s['status']:<12} {s['objective']}")
        if s.get("available_skills"):
            skills_str = ", ".join(s["available_skills"][:5])
            console.print(f"    {'':30} Skills: {skills_str}")
        if s.get("next_action"):
            console.print(f"    {'':30} Proximo: {s['next_action']}")
        console.print("")

    console.print(f"[bold]Total:[/bold] {result['total']} setores")
    grouped = sectors_check.by_status()
    for st, ids in grouped.items():
        console.print(f"  {st}: {len(ids)}")


# ---------------------------------------------------------------------------
# SALES COMMANDS
# ---------------------------------------------------------------------------


sales_app = typer.Typer(
    name="sales",
    help="Setor sales_revenue — vendas B2B hoteis",
    add_completion=False,
)


@sales_app.command(name="status")
def sales_status():
    """Status do setor sales_revenue + Daily Prophet."""
    from src.checkers import sectors_check, daily_prophet_check
    sector = sectors_check.get_sector("sales_revenue")

    if sector:
        console.print("[bold]Setor: sales_revenue[/bold]")
        console.print(f"  Status: {sector['status']}")
        console.print(f"  Objetivo: {sector['objective']}")
        if sector.get("available_skills"):
            console.print(f"  Skills: {', '.join(sector['available_skills'])}")
        if sector.get("next_action"):
            console.print(f"  Proximo: {sector['next_action']}")
    else:
        console.print("[red]Setor sales_revenue nao encontrado.[/red]")

    console.print("\n[bold]Daily Prophet Hotels[/bold]")
    dp = daily_prophet_check.check()
    if dp["exists"]:
        console.print(f"  [green]Diretorio:[/green] OK")
        console.print(f"  .env.local: {'[OK]' if dp['has_env'] else '[!!] ausente'}")
        console.print(f"  package.json: {'[OK]' if dp.get('package_json') else '[!!] ausente'}")
        console.print(f"  Scripts: {len(dp.get('scripts', []))}")
        console.print(f"  Arquivos SQL: {dp.get('sql_files', 0)}")
        console.print(f"  Status: {dp['status']}")
    else:
        console.print(f"  [red]Diretorio nao encontrado em {_DAILY_PROPHET_DIR}[/red]")
        console.print(f"  Status: {dp['status']}")


# ---------------------------------------------------------------------------
# MEMORY COMMANDS
# ---------------------------------------------------------------------------


memory_app = typer.Typer(
    name="memory",
    help="Akasha + Qdrant — memorias e indexacao",
    add_completion=False,
)


@memory_app.command(name="recent")
def mem_recent(
    limit: int = typer.Option(5, "--limit", help="Numero de memorias"),
):
    """Ultimas N memorias do Akasha."""
    from src.memory.akasha_reader import ping, get_recent_memories
    if not ping():
        console.print("[red]Akasha offline[/red]")
        return
    memories = get_recent_memories(limit=limit)
    console.print(f"[bold]Ultimas {len(memories)} memorias:[/bold]\n")
    for i, m in enumerate(memories, 1):
        if "error" in m:
            console.print(f"  [red]{m['error']}[/red]")
            continue
        preview = (m.get("content") or "")[:120].replace("\n", " ")
        console.print(f"  {i}. {preview}...")
        if m.get("created_at"):
            console.print(f"     [dim]{m['created_at']}[/dim]")


@memory_app.command(name="project")
def mem_project(
    project_name: str = typer.Argument(..., help="Nome do projeto"),
):
    """Busca contexto de um projeto no Akasha."""
    from src.memory.akasha_reader import ping, get_project_context
    if not ping():
        console.print("[red]Akasha offline[/red]")
        return
    ctx = get_project_context(project_name)
    if ctx:
        console.print(f"[green]{ctx}[/green]")
    else:
        console.print(f"[yellow]Projeto '{project_name}' nao encontrado no Akasha.[/yellow]")


# ---------------------------------------------------------------------------
# LLM COMMANDS
# ---------------------------------------------------------------------------


llm_app = typer.Typer(
    name="llm",
    help="LLM Router — modelos e recomendacoes",
    add_completion=False,
)


@llm_app.command(name="models")
def llm_models():
    """Lista modelos configurados no LLM Router."""
    from src.intelligence.llm_router_bridge import list_models, config_available
    if not config_available():
        console.print(f"[yellow]config.yaml nao encontrado em {_LLM_ROUTER_DIR}[/yellow]")
        return
    models = list_models()
    if not models:
        console.print("[yellow]Nenhum modelo configurado.[/yellow]")
        return
    console.print("[bold]LLM Router — Modelos[/bold]\n")
    for m in models:
        params = m.get("litellm_params", {})
        console.print(f"  [cyan]{m['model_name']:<20}[/cyan] {params.get('model', '?')}")
        if params.get("api_base"):
            console.print(f"    {'':20} API: {params['api_base']}")


@llm_app.command(name="suggest")
def llm_suggest(
    task_type: str = typer.Argument(..., help="Tipo de tarefa (caption, classificacao, etc)"),
):
    """Recomenda modelo para um tipo de tarefa."""
    from src.intelligence.llm_router_bridge import get_model_for_task, list_task_types
    model = get_model_for_task(task_type)
    all_types = list_task_types()
    console.print(f"[bold]Tarefa:[/bold] {task_type}")
    console.print(f"[bold]Modelo recomendado:[/bold] [green]{model}[/green]")
    if model in all_types:
        console.print(f"\n  Outras tarefas usando [cyan]{model}[/cyan]:")
        for t in all_types[model][:8]:
            console.print(f"    - {t}")



@app.command(name="video-status")
def video_status():
    """Diagnóstico do pipeline de vídeo (read-only)."""
    session_id = new_session_id()
    start = time.time()

    result = video_pipeline_check.check()

    console.print("[bold]Video Pipeline — Diagnóstico[/bold]")
    cls = result["classification"]
    cls_str = {
        "operational": "[green]operational[/green]",
        "partial": "[yellow]partial[/yellow]",
        "documented_only": "[blue]documented_only[/blue]",
        "not_found": "[red]not_found[/red]",
        "scan_timeout_partial": "[yellow]scan_timeout_partial[/yellow]",
    }.get(cls, cls)
    console.print(f"  Classificação: {cls_str}")
    console.print(f"  Confiança: {result['confidence']}")

    console.print(f"\n  Sinais:")
    for key, val in result.get("signals", {}).items():
        indicator = "[OK]" if val else "[  ]"
        console.print(f"    {indicator} {key}")

    console.print(f"\n  Counts:")
    for key, val in result.get("counts", {}).items():
        console.print(f"    {key}: {val}")

    if result.get("risks"):
        console.print(f"\n  [yellow]Riscos:[/yellow]")
        for r in result["risks"]:
            console.print(f"    - {r}")

    if result.get("evidence"):
        console.print(f"\n  Evidências ({len(result['evidence'])}):")
        for e in result["evidence"][:8]:
            console.print(f"    [{e['type']}] {e['path']} ({e['keyword']})")
        if result.get("evidence_truncated"):
            console.print(f"    ... mais {len(result['evidence']) - 8} itens truncados")

    dur = int((time.time() - start) * 1000)
    log_mission(session_id, "video-status", cls, dur)


# ---------------------------------------------------------------------------
# VIDEO ASSETS COMMANDS
# ---------------------------------------------------------------------------


video_assets_app = typer.Typer(
    name="video-assets",
    help="Gerencia o registro local de assets de vídeo",
    add_completion=False,
)


@video_assets_app.command(name="scan")
def va_scan(
    dry_run: bool = typer.Option(True, "--dry-run", help="Simular sem importar"),
    max_depth: int = typer.Option(2, "--max-depth", help="Profundidade máxima"),
    max_files: int = typer.Option(500, "--max-files", help="Limite de arquivos"),
    import_: bool = typer.Option(False, "--import", help="Importar arquivos encontrados (inverso de dry-run)"),
):
    """Varre diretórios locais em busca de arquivos de vídeo."""
    session_id = new_session_id()
    start = time.time()

    is_dry_run = not import_ and dry_run
    scanner = Scanner()
    result = scanner.scan(dry_run=is_dry_run, max_depth=max_depth, max_files=max_files)

    console.print("[bold]Scan de Vídeos[/bold]")
    console.print(f"  Dry-run: {'Sim' if result['dry_run'] else 'Não'}")
    console.print(f"  Encontrados: {result['found']}")
    if not result["dry_run"]:
        console.print(f"  Importados: {result['imported']}")
        console.print(f"  Pulados (dup): {result['skipped']}")
    if result.get("timed_out"):
        console.print("  [yellow]Timeout parcial — alguns diretórios não foram varridos[/yellow]")
    if result.get("errors"):
        console.print(f"  [red]Erros: {len(result['errors'])}[/red]")
        for e in result["errors"][:5]:
            console.print(f"    {e}")

    dur = int((time.time() - start) * 1000)
    log_mission(session_id, "video-assets-scan", "success", dur,
                summary=f"found={result['found']}, imported={result.get('imported', 0)}, dry_run={result['dry_run']}")


@video_assets_app.command(name="list")
def va_list(
    status_filter: str = typer.Option(None, "--status", help="Filtrar por status"),
    account: str = typer.Option(None, "--account", help="Filtrar por conta"),
    tag: str = typer.Option(None, "--tag", help="Filtrar por tag"),
):
    """Lista assets de vídeo com filtros opcionais."""
    session_id = new_session_id()
    start = time.time()

    registry = Registry()
    status_enum = AssetStatus(status_filter) if status_filter else None
    assets = registry.filter(status=status_enum, account=account, tag=tag)

    if not assets:
        console.print("Nenhum asset encontrado.")
        log_mission(session_id, "video-assets-list", "success", int((time.time()-start)*1000))
        return

    table = Table(title=f"Assets ({len(assets)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Arquivo")
    table.add_column("Status")
    table.add_column("Conta")
    table.add_column("Formato")
    table.add_column("Tam.")

    for a in assets:
        size_mb = a.size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.1f}MB" if size_mb > 1 else f"{a.size_bytes / 1024:.0f}KB"
        table.add_row(
            a.asset_id[:8],
            a.file_name[:30],
            a.status.value,
            a.account_target or "-",
            a.format,
            size_str,
        )
    console.print(table)

    dur = int((time.time() - start) * 1000)
    log_mission(session_id, "video-assets-list", "success", dur)


@video_assets_app.command(name="inbox")
def va_inbox(
    account: str = typer.Option(None, "--account", help="Filtrar por conta"),
):
    """Assets aguardando triagem (status=inbox)."""
    session_id = new_session_id()
    start = time.time()

    queue = Queue()
    assets = queue.registry.filter(status=AssetStatus.INBOX, account=account)

    if not assets:
        console.print("Nenhum asset na inbox. :D")
        log_mission(session_id, "video-assets-inbox", "success", int((time.time()-start)*1000))
        return

    table = Table(title=f"Inbox ({len(assets)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Arquivo")
    table.add_column("Criado")
    table.add_column("Tamanho")

    for a in assets:
        size_mb = a.size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.1f}MB" if size_mb > 1 else f"{a.size_bytes / 1024:.0f}KB"
        table.add_row(
            a.asset_id[:8],
            a.file_name[:40],
            a.created_at[:10] if a.created_at else "-",
            size_str,
        )
    console.print(table)

    dur = int((time.time() - start) * 1000)
    log_mission(session_id, "video-assets-inbox", "success", dur)


@video_assets_app.command(name="update")
def va_update(
    asset_id: str = typer.Argument(..., help="ID do asset"),
    account: str = typer.Option(None, "--account", help="Conta alvo (@handle)"),
    tags: str = typer.Option(None, "--tags", help="Tags separadas por vírgula"),
    city: str = typer.Option(None, "--city", help="Cidade"),
    format: str = typer.Option(None, "--format", help="Formato (reel, carousel, etc)"),
    status: str = typer.Option(None, "--status", help="Novo status"),
    notes: str = typer.Option(None, "--notes", help="Notas"),
):
    """Atualiza metadados de um asset."""
    registry = Registry()
    asset = registry.get(asset_id)
    if not asset:
        console.print(f"[red]Asset não encontrado: {asset_id}[/red]")
        raise typer.Exit(1)

    kwargs = {}
    if account is not None:
        kwargs["account_target"] = account
    if tags is not None:
        kwargs["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    if city is not None:
        kwargs["city"] = city
    if format is not None:
        kwargs["format"] = format
    if status is not None:
        try:
            target = AssetStatus(status)
            if not asset.status.can_transition_to(target):
                console.print(
                    f"[red]Transição inválida: {asset.status.value} → {target.value}[/red]"
                )
                raise typer.Exit(1)
            kwargs["status"] = target
        except ValueError:
            console.print(f"[red]Status inválido: {status}[/red]")
            raise typer.Exit(1)
    if notes is not None:
        kwargs["notes"] = notes

    if not kwargs:
        console.print("[yellow]Nenhum campo para atualizar.[/yellow]")
        return

    updated = registry.update(asset_id, **kwargs)
    if updated:
        console.print(f"[green]Asset {asset_id[:8]} atualizado:[/green] {', '.join(kwargs.keys())}")
    else:
        console.print(f"[red]Falha ao atualizar {asset_id}[/red]")


@video_assets_app.command(name="schedule")
def va_schedule(
    asset_id: str = typer.Argument(..., help="ID do asset"),
    scheduled_at: str = typer.Argument(..., help="Data ISO (ex: 2026-05-05T14:00:00Z)"),
):
    """Agenda um asset para publicação."""
    queue = Queue()
    try:
        updated = queue.schedule(asset_id, scheduled_at)
        if updated:
            console.print(f"[green]Asset {asset_id[:8]} agendado para {scheduled_at}[/green]")
        else:
            console.print(f"[red]Asset não encontrado: {asset_id}[/red]")
            raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@video_assets_app.command(name="publish")
def va_publish(
    asset_id: str = typer.Argument(..., help="ID do asset"),
):
    """Marca asset como publicado."""
    queue = Queue()
    updated = queue.mark_published(asset_id)
    if updated:
        console.print(f"[green]Asset {asset_id[:8]} marcado como publicado[/green]")
    else:
        console.print(f"[red]Asset não encontrado: {asset_id}[/red]")
        raise typer.Exit(1)


@video_assets_app.command(name="stats")
def va_stats():
    """Estatísticas agregadas do registro."""
    registry = Registry()
    stats = registry.stats()
    total = stats["total"]

    console.print("[bold]Video Assets — Estatísticas[/bold]")
    console.print(f"  Total: {total}")

    if stats["by_status"]:
        console.print(f"\n  Por status:")
        for s, count in sorted(stats["by_status"].items()):
            console.print(f"    {s}: {count}")

    total_mb = stats["total_bytes"] / (1024 * 1024)
    console.print(f"\n  Volume total: {total_mb:.1f} MB")

    if stats["formats"]:
        console.print(f"\n  Formatos:")
        for f, count in sorted(stats["formats"].items()):
            console.print(f"    {f}: {count}")


@video_assets_app.command(name="export")
def va_export(
    fmt: str = typer.Option("csv", "--format", help="Formato de exportação (csv)"),
):
    """Exporta registro como CSV."""
    path = os.path.join(_OMNIS_ROOT, "data", f"video_assets_export.{fmt}")
    registry = Registry()
    if fmt == "csv":
        registry.export_csv(path)
        console.print(f"[green]Exportado:[/green] {path}")
    else:
        console.print(f"[red]Formato não suportado: {fmt}[/red]")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# ACCOUNTS COMMANDS
# ---------------------------------------------------------------------------


accounts_app = typer.Typer(
    name="accounts",
    help="Gerencia o cadastro local de contas Instagram",
    add_completion=False,
)


@accounts_app.command(name="add")
def acc_add(
    handle: str = typer.Argument(..., help="Handle da conta (ex: lucastigrereal)"),
    tags: str = typer.Option("", "--tags", help="Tags separadas por vírgula"),
    priority: str = typer.Option("medium", "--priority", help="low | medium | high"),
    display_name: str = typer.Option(None, "--display-name", help="Nome exibição"),
    niche: str = typer.Option(None, "--niche", help="Apelido do nicho (será convertido em tag)"),
):
    """Adiciona uma nova conta Instagram."""
    try:
        reg = AccountRegistry()
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if niche:
            tag_list.append(niche.strip().lower())
        account = reg.add(
            handle=handle,
            tags=tag_list,
            priority=priority,
            display_name=display_name,
        )
        console.print(f"[green]Conta adicionada:[/green] @{account.handle} (id: {account.account_id[:8]})")
    except ValueError as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)


@accounts_app.command(name="list")
def acc_list():
    """Lista todas as contas cadastradas."""
    reg = AccountRegistry()
    accounts = reg.list_all()

    if not accounts:
        console.print("Nenhuma conta cadastrada.")
        return

    table = Table(title=f"Contas ({len(accounts)})")
    table.add_column("Handle", style="cyan")
    table.add_column("Tags")
    table.add_column("Priority")
    table.add_column("Horários")
    table.add_column("Ativa?")

    for a in accounts:
        tag_str = ", ".join(a.tags[:3]) if a.tags else "-"
        times_str = ", ".join(a.default_posting_times) if a.default_posting_times else "-"
        active_str = "[green]Sim[/green]" if a.active else "[red]Não[/red]"
        table.add_row(f"@{a.handle}", tag_str, a.priority, times_str, active_str)
    console.print(table)


@accounts_app.command(name="update")
def acc_update(
    handle: str = typer.Argument(..., help="Handle da conta"),
    priority: str = typer.Option(None, "--priority", help="low | medium | high"),
    tags: str = typer.Option(None, "--tags", help="Tags separadas por vírgula"),
    display_name: str = typer.Option(None, "--display-name", help="Nome exibição"),
):
    """Atualiza dados de uma conta."""
    reg = AccountRegistry()
    kwargs = {}
    if priority:
        kwargs["priority"] = priority
    if tags is not None:
        kwargs["tags"] = tags
    if display_name is not None:
        kwargs["display_name"] = display_name

    result = reg.update(handle, **kwargs)
    if result:
        console.print(f"[green]Conta @{handle} atualizada.[/green]")
    else:
        console.print(f"[red]Conta @{handle} não encontrada.[/red]")
        raise typer.Exit(1)


@accounts_app.command(name="deactivate")
def acc_deactivate(
    handle: str = typer.Argument(..., help="Handle da conta"),
):
    """Desativa uma conta."""
    reg = AccountRegistry()
    result = reg.deactivate(handle)
    if result:
        console.print(f"[green]Conta @{handle} desativada.[/green]")
    else:
        console.print(f"[red]Conta @{handle} não encontrada.[/red]")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# QUEUE COMMANDS
# ---------------------------------------------------------------------------


queue_app = typer.Typer(
    name="queue",
    help="Gerencia a fila diária de conteúdo (planejamento local)",
    add_completion=False,
)


@queue_app.command(name="generate")
def cq_generate(
    days: int = typer.Option(7, "--days", help="Dias à frente"),
    dry_run: bool = typer.Option(True, "--dry-run", help="Simular sem escrever"),
    apply: bool = typer.Option(False, "--apply", help="Aplicar (grava a fila)"),
    force: bool = typer.Option(False, "--force", help="Permite > 30 dias"),
    account: str = typer.Option(None, "--account", help="Gerar só para uma conta"),
):
    """Gera slots de fila para N dias."""
    queue = CQQueue()
    try:
        is_dry_run = not apply and dry_run
        result = queue.generate(days=days, dry_run=is_dry_run, force=force, account_filter=account)
        console.print("[bold]Queue Generate[/bold]")
        console.print(f"  Dry-run: {'Sim' if result['dry_run'] else 'Não'}")
        console.print(f"  Dias: {result['days']}")
        console.print(f"  Contas: {result['accounts']}")
        console.print(f"  Gerados: {result['generated']}")
        console.print(f"  Pulados (já existem): {result['skipped']}")
        if account:
            console.print(f"  Conta filtrada: @{account}")
    except ValueError as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)


@queue_app.command(name="list")
def cq_list(
    account: str = typer.Option(None, "--account", help="Filtrar por conta"),
    status: str = typer.Option(None, "--status", help="Filtrar por status"),
    date: str = typer.Option(None, "--date", help="Filtrar por data YYYY-MM-DD"),
):
    """Lista itens da fila."""
    queue = CQQueue()
    items = queue.filter(account=account, status=status, date=date)

    if not items:
        console.print("Nenhum item na fila.")
        return

    table = Table(title=f"Fila ({len(items)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Conta")
    table.add_column("Data")
    table.add_column("Hora")
    table.add_column("Formato")
    table.add_column("Status")
    table.add_column("Asset")

    for i in items[:30]:
        asset_str = i.asset_id[:8] if i.asset_id else "-"
        table.add_row(
            i.queue_id[:8],
            f"@{i.account_handle}",
            i.date,
            i.time,
            i.format,
            i.status,
            asset_str,
        )
    console.print(table)
    if len(items) > 30:
        console.print(f"... mais {len(items) - 30} itens (mostrando 30)")


@queue_app.command(name="today")
def cq_today():
    """Itens da fila para hoje."""
    queue = CQQueue()
    items = queue.today()

    if not items:
        console.print("Nenhum item agendado para hoje.")
        return

    table = Table(title=f"Hoje ({len(items)})")
    table.add_column("Hora")
    table.add_column("Conta")
    table.add_column("Status")
    table.add_column("Asset")

    for i in items:
        asset_str = i.asset_id[:8] if i.asset_id else "-"
        table.add_row(i.time, f"@{i.account_handle}", i.status, asset_str)
    console.print(table)


@queue_app.command(name="assign")
def cq_assign(
    queue_id: str = typer.Argument(..., help="ID do slot na fila"),
    asset_id: str = typer.Argument(..., help="ID do asset"),
    force: bool = typer.Option(False, "--force", help="Substituir asset existente"),
):
    """Atribui um asset a um slot da fila."""
    queue = CQQueue()
    try:
        result, warning = queue.assign_asset(queue_id, asset_id, force=force)
        if result:
            console.print(f"[green]Asset {asset_id[:8]} atribuído ao slot {queue_id[:8]}[/green]")
            if warning:
                console.print(f"[yellow]Aviso:[/yellow] {warning}")
        else:
            console.print(f"[red]Falha ao atribuir asset.[/red]")
    except ValueError as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)


@queue_app.command(name="update")
def cq_update(
    queue_id: str = typer.Argument(..., help="ID do slot"),
    status: str = typer.Option(None, "--status", help="Novo status"),
    objective: str = typer.Option(None, "--objective", help="Objetivo"),
    notes: str = typer.Option(None, "--notes", help="Notas"),
):
    """Atualiza um item da fila."""
    queue = CQQueue()
    kwargs = {}
    if status:
        kwargs["status"] = status
    if objective:
        kwargs["objective"] = objective
    if notes is not None:
        kwargs["notes"] = notes

    result = queue.update(queue_id, **kwargs)
    if result:
        console.print(f"[green]Slot {queue_id[:8]} atualizado:[/green] {', '.join(kwargs.keys())}")
    else:
        console.print(f"[red]Slot {queue_id[:8]} não encontrado.[/red]")
        raise typer.Exit(1)


@queue_app.command(name="stats")
def cq_stats():
    """Estatísticas da fila."""
    queue = CQQueue()
    stats = queue.stats()
    total = stats["total"]

    console.print("[bold]Content Queue — Estatísticas[/bold]")
    console.print(f"  Total: {total}")
    if stats["by_status"]:
        console.print(f"\n  Por status:")
        for s, count in sorted(stats["by_status"].items()):
            console.print(f"    {s}: {count}")
    if stats["by_account"]:
        console.print(f"\n  Por conta:")
        for a, count in sorted(stats["by_account"].items()):
            console.print(f"    @{a}: {count}")
    console.print(f"\n  Precisa de asset: {stats['needs_asset']}")
    console.print(f"  Precisa de legenda: {stats['needs_caption']}")
    console.print(f"  Aprovados: {stats['approved']}")
    console.print(f"  Agendados: {stats['scheduled']}")


@queue_app.command(name="export")
def cq_export(
    fmt: str = typer.Option("csv", "--format", help="Formato (csv)"),
    date_from: str = typer.Option(None, "--date-from", help="Data inicial YYYY-MM-DD"),
    date_to: str = typer.Option(None, "--date-to", help="Data final YYYY-MM-DD"),
    status_filter: str = typer.Option(None, "--status", help="Filtrar por status"),
    account_filter: str = typer.Option(None, "--account", help="Filtrar por conta"),
):
    """Exporta fila como CSV."""
    Path(os.path.join(_OMNIS_ROOT, "data", "exports")).mkdir(parents=True, exist_ok=True)
    export_name = f"queue_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.{fmt}"
    path = os.path.join(_OMNIS_ROOT, "data", "exports", export_name)

    queue = CQQueue()
    if fmt == "csv":
        queue.export_csv(
            path,
            date_from=date_from,
            date_to=date_to,
            status_filter=status_filter,
            account_filter=account_filter,
        )
        console.print(f"[green]Exportado:[/green] {path} ({os.path.getsize(path)} bytes)")
    else:
        console.print(f"[red]Formato não suportado: {fmt}[/red]")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# CAPTION DRAFTS COMMANDS
# ---------------------------------------------------------------------------


captions_app = typer.Typer(
    name="captions",
    help="Gerencia rascunhos de legenda (Fase 2C)",
    add_completion=False,
)


def _queue_updater(queue_id: str, status: str) -> bool:
    """Atualiza status na Content Queue (usado pelo ApprovalGate)."""
    queue = CQQueue()
    item = queue.get(queue_id)
    if not item:
        return False
    if item.status in ("scheduled", "published"):
        raise ValueError(
            f"Queue item '{queue_id[:8]}' está {item.status}. "
            f"Não é possível alterar caption depois de agendado."
        )
    queue.update(queue_id, status=status)
    return True


@captions_app.command(name="create")
def cap_create(
    queue_id: str = typer.Argument(..., help="ID do slot na fila"),
    text: str = typer.Option("", "--text", help="Texto da legenda"),
    hashtags: str = typer.Option("", "--hashtags", help="Hashtags separadas por vírgula"),
    cta: str = typer.Option("", "--cta", help="Call to action"),
    objective: str = typer.Option("alcance", "--objective", help="Objetivo (alcance, autoridade, conversao, relacionamento, teste)"),
    format: str = typer.Option("unknown", "--format", help="Formato (reels, carousel, stories, feed)"),
    notes: str = typer.Option("", "--notes", help="Notas"),
    force: bool = typer.Option(False, "--force", help="Atualizar rascunho existente como revised"),
    apply_template: str = typer.Option(None, "--template", help="ID do template para pré-preenchimento"),
):
    """Cria um novo rascunho de legenda para um slot da fila."""
    dm = DraftsManager()

    # Verificar se já existe draft para este queue_id
    existing = dm.get_by_queue_id(queue_id)
    if existing and not force:
        console.print(f"[red]Já existe draft para este slot ({existing.draft_id[:8]}). Use --force para versionar.[/red]")
        raise typer.Exit(1)

    tag_list = [t.strip() for t in hashtags.split(",") if t.strip()]

    # Se template foi solicitado, renderizar
    if apply_template:
        tl = TemplateLibrary()
        templates = [t for t in tl.list_all() if t.template_id == apply_template]
        if not templates:
            console.print(f"[red]Template '{apply_template}' não encontrado.[/red]")
            raise typer.Exit(1)
        rendered = tl.render(templates[0], hook=text or "")
        if not text:
            text = rendered["caption_text"]
        if not cta:
            cta = rendered["cta"]
        if not tag_list:
            tag_list = rendered["hashtags"]

    # Buscar account_handle e asset_id da queue
    queue = CQQueue()
    queue_item = queue.get(queue_id)
    account_handle = queue_item.account_handle if queue_item else "unknown"
    asset_id = queue_item.asset_id if queue_item else None

    if force and existing:
        # Atualizar existente como revised
        updated = dm.update(existing.draft_id, caption_text=text,
                           hashtags=tag_list, cta=cta,
                           objective=objective, format=format,
                           notes=notes, asset_id=asset_id)
        if updated:
            console.print(f"[green]Draft {updated.draft_id[:8]} atualizado (v{updated.version}, status={updated.status})[/green]")
    else:
        draft = dm.create(
            queue_id=queue_id,
            account_handle=account_handle,
            caption_text=text,
            hashtags=tag_list,
            cta=cta,
            objective=objective,
            format=format,
            notes=notes,
            asset_id=asset_id,
        )
        console.print(f"[green]Draft criado:[/green] {draft.draft_id} (v{draft.version})")


@captions_app.command(name="list")
def cap_list(
    status_filter: str = typer.Option(None, "--status", help="Filtrar por status"),
    account: str = typer.Option(None, "--account", help="Filtrar por conta"),
):
    """Lista rascunhos de legenda."""
    dm = DraftsManager()
    items = dm.list_all()
    if status_filter:
        items = [i for i in items if i.status == status_filter]
    if account:
        from src.content_queue.accounts import _normalize_handle
        acct = _normalize_handle(account)
        items = [i for i in items if i.account_handle == acct]

    if not items:
        console.print("Nenhum rascunho encontrado.")
        return

    table = Table(title=f"Rascunhos ({len(items)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Queue")
    table.add_column("Conta")
    table.add_column("Status")
    table.add_column("V")
    table.add_column("Obj.")
    table.add_column("Atualizado")

    for d in items[:30]:
        table.add_row(
            d.draft_id[:8],
            d.queue_id[:8],
            f"@{d.account_handle}",
            d.status,
            str(d.version),
            d.objective[:6],
            d.updated_at[:10] if d.updated_at else "-",
        )
    console.print(table)
    if len(items) > 30:
        console.print(f"... mais {len(items) - 30} rascunhos (mostrando 30)")


@captions_app.command(name="show")
def cap_show(
    draft_id: str = typer.Argument(..., help="ID do rascunho"),
):
    """Mostra detalhes completos de um rascunho."""
    dm = DraftsManager()
    draft = dm.get(draft_id)
    if not draft:
        console.print(f"[red]Draft '{draft_id}' não encontrado.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Draft:[/bold] {draft.draft_id}")
    console.print(f"  Queue ID: {draft.queue_id}")
    console.print(f"  Conta: @{draft.account_handle}")
    console.print(f"  Status: {draft.status}")
    console.print(f"  Versão: {draft.version}")
    console.print(f"  Objetivo: {draft.objective}")
    console.print(f"  Formato: {draft.format}")
    console.print(f"  CTA: {draft.cta or '(não definido)'}")
    console.print(f"  Hashtags: {', '.join(draft.hashtags) if draft.hashtags else '(nenhuma)'}")
    if draft.rejection_reason:
        console.print(f"  Motivo rejeição: {draft.rejection_reason}")
    console.print(f"  Notas: {draft.notes or '(nenhuma)'}")
    console.print(f"  Criado: {draft.created_at}")
    console.print(f"  Atualizado: {draft.updated_at}")
    if draft.caption_text:
        console.print(Panel(draft.caption_text, title="Legenda"))
    else:
        console.print("[dim](sem texto)[/dim]")


@captions_app.command(name="update")
def cap_update(
    draft_id: str = typer.Argument(..., help="ID do rascunho"),
    text: str = typer.Option(None, "--text", help="Novo texto da legenda"),
    hashtags: str = typer.Option(None, "--hashtags", help="Hashtags separadas por vírgula"),
    cta: str = typer.Option(None, "--cta", help="Novo CTA"),
    objective: str = typer.Option(None, "--objective", help="Objetivo"),
    format: str = typer.Option(None, "--format", help="Formato"),
    notes: str = typer.Option(None, "--notes", help="Notas"),
):
    """Atualiza um rascunho existente."""
    dm = DraftsManager()
    kwargs = {}
    if text is not None:
        kwargs["caption_text"] = text
    if hashtags is not None:
        kwargs["hashtags"] = [t.strip() for t in hashtags.split(",") if t.strip()]
    if cta is not None:
        kwargs["cta"] = cta
    if objective is not None:
        kwargs["objective"] = objective
    if format is not None:
        kwargs["format"] = format
    if notes is not None:
        kwargs["notes"] = notes

    updated = dm.update(draft_id, **kwargs)
    if updated:
        console.print(f"[green]Draft {updated.draft_id[:8]} atualizado (v{updated.version}, status={updated.status})[/green]")
    else:
        console.print(f"[red]Draft '{draft_id}' não encontrado.[/red]")
        raise typer.Exit(1)


@captions_app.command(name="submit")
def cap_submit(
    draft_id: str = typer.Argument(..., help="ID do rascunho"),
):
    """Submete rascunho para revisão (draft/revised → needs_review)."""
    dm = DraftsManager()
    submitted = dm.submit(draft_id)
    if submitted:
        console.print(f"[green]Draft {submitted.draft_id[:8]} submetido para revisão (status={submitted.status})[/green]")
    else:
        console.print(f"[red]Não foi possível submeter. Draft está em {dm.get(draft_id).status if dm.get(draft_id) else '?'} (só draft/revised podem ser submetidos).[/red]")
        raise typer.Exit(1)


@captions_app.command(name="export")
def cap_export(
    status_filter: str = typer.Option(None, "--status", help="Filtrar por status"),
    account_filter: str = typer.Option(None, "--account", help="Filtrar por conta"),
):
    """Exporta rascunhos como CSV."""
    from pathlib import Path
    Path(os.path.join(_OMNIS_ROOT, "data", "exports")).mkdir(parents=True, exist_ok=True)
    export_name = f"caption_drafts_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    path = os.path.join(_OMNIS_ROOT, "data", "exports", export_name)

    dm = DraftsManager()
    dm.export_csv(path, status_filter=status_filter, account_filter=account_filter)
    console.print(f"[green]Exportado:[/green] {path} ({os.path.getsize(path)} bytes)")


# ---------------------------------------------------------------------------
# APPROVALS COMMANDS
# ---------------------------------------------------------------------------


approvals_app = typer.Typer(
    name="approvals",
    help="Gate de aprovação de legendas (Fase 2C)",
    add_completion=False,
)


@approvals_app.command(name="pending")
def app_pending():
    """Lista drafts aguardando revisão (needs_review + revised)."""
    dm = DraftsManager()
    items = dm.list_all()
    pending = [d for d in items if d.status in (DraftStatus.NEEDS_REVIEW, DraftStatus.REVISED)]

    if not pending:
        console.print("Nenhum draft pendente de revisão. :D")
        return

    table = Table(title=f"Pendentes ({len(pending)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Conta")
    table.add_column("Status")
    table.add_column("V")
    table.add_column("Atualizado")

    for d in pending:
        table.add_row(d.draft_id[:8], f"@{d.account_handle}", d.status, str(d.version), d.updated_at[:10])
    console.print(table)

    # Stale warning
    stale = dm.check_stale()
    if stale:
        console.print(f"\n[yellow]⚠ {len(stale)} rascunhos stale (> {STALE_DAYS} dias parados):[/yellow]")
        for s in stale:
            console.print(f"  {s.draft_id[:8]} — @{s.account_handle} ({s.status})")


@approvals_app.command(name="log")
def app_log(
    limit: int = typer.Option(20, "--limit", help="Número de entradas"),
    draft_id: str = typer.Option(None, "--draft", help="Filtrar por draft ID"),
    action: str = typer.Option(None, "--action", help="Filtrar por ação"),
):
    """Mostra o log de aprovações."""
    dm = DraftsManager()
    entries = dm.get_approval_log(limit=limit, draft_id=draft_id, action=action)

    if not entries:
        console.print("Nenhum evento no log.")
        return

    table = Table(title=f"Approval Log ({len(entries)})")
    table.add_column("Data")
    table.add_column("Ação")
    table.add_column("Draft")
    table.add_column("Queue")
    table.add_column("Autor")
    table.add_column("Motivo")

    for e in entries:
        table.add_row(
            e.timestamp[:16] if e.timestamp else "-",
            e.action,
            e.draft_id[:8],
            e.queue_id[:8],
            e.actor,
            (e.reason or "")[:25],
        )
    console.print(table)


@approvals_app.command(name="approve")
def app_approve(
    draft_id: str = typer.Argument(..., help="ID do rascunho"),
):
    """Aprova um rascunho e atualiza a Content Queue."""
    dm = DraftsManager()
    gate = ApprovalGate(dm)

    try:
        draft, warning = gate.approve(draft_id, queue_updater=_queue_updater)
        console.print(f"[green]Draft {draft.draft_id[:8]} aprovado![/green]")
        console.print(f"  Queue {draft.queue_id[:8]} → caption_ready")
        if warning:
            console.print(f"[yellow]Aviso:[/yellow] {warning}")
        # Mostrar warnings de validação
        validation = gate.validate(draft.caption_text, draft.hashtags, draft.cta)
        if validation.warnings:
            for w in validation.warnings:
                console.print(f"[yellow]⚠ {w}[/yellow]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@approvals_app.command(name="reject")
def app_reject(
    draft_id: str = typer.Argument(..., help="ID do rascunho"),
    reason: str = typer.Option(..., "--reason", help="Motivo da rejeição (obrigatório)"),
):
    """Rejeita um rascunho. --reason é obrigatório."""
    dm = DraftsManager()
    gate = ApprovalGate(dm)

    try:
        draft, warning = gate.reject(draft_id, reason=reason, queue_updater=_queue_updater)
        console.print(f"[green]Draft {draft.draft_id[:8]} rejeitado.[/green]")
        console.print(f"  Motivo: {reason}")
        if warning:
            console.print(f"[yellow]Aviso:[/yellow] {warning}")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@approvals_app.command(name="batch")
def app_batch(
    limit: int = typer.Option(5, "--limit", help="Maximo de drafts a aprovar"),
):
    """Aprova ate N drafts validos de needs_review/revised sem placeholders."""
    dm = DraftsManager()
    gate = ApprovalGate(dm)
    r = gate.batch_approve(limit=limit, queue_updater=_queue_updater)
    console.print(f"[green]Aprovados:[/green] {r['approved']} | [yellow]Pulados:[/yellow] {r['skipped']}")
    for s in r["skip_reasons"]:
        console.print(f"  [yellow]skip:[/yellow] {s}")


@approvals_app.command(name="status")
def app_approvals_status():
    """Contagem de drafts por status."""
    from collections import Counter
    dm = DraftsManager()
    counts = Counter(d.status for d in dm.list_all())
    console.print("[bold]Drafts por status:[/bold]")
    for s, n in sorted(counts.items()):
        console.print(f"  {s:<20} {n}")


# ---------------------------------------------------------------------------
# TEMPLATES COMMANDS
# ---------------------------------------------------------------------------


templates_app = typer.Typer(
    name="templates",
    help="Gerencia templates de legenda",
    add_completion=False,
)


@templates_app.command(name="list")
def tmp_list(
    objective: str = typer.Option(None, "--objective", help="Filtrar por objetivo"),
):
    """Lista templates disponíveis."""
    tl = TemplateLibrary()
    if objective:
        templates = tl.get_by_objective(objective)
    else:
        templates = tl.list_all()

    if not templates:
        console.print("Nenhum template encontrado.")
        return

    table = Table(title=f"Templates ({len(templates)})")
    table.add_column("ID", style="cyan")
    table.add_column("Nome")
    table.add_column("Objetivo")
    table.add_column("Formato")
    table.add_column("Hook")

    for t in templates:
        hook_preview = t.hook_template[:30] + "..." if len(t.hook_template) > 30 else t.hook_template
        table.add_row(
            t.template_id,
            t.name,
            t.objective,
            t.format or "qualquer",
            hook_preview,
        )
    console.print(table)


@templates_app.command(name="show")
def tmp_show(
    template_id: str = typer.Argument(..., help="ID do template"),
):
    """Mostra detalhes de um template."""
    tl = TemplateLibrary()
    templates = [t for t in tl.list_all() if t.template_id == template_id]
    if not templates:
        console.print(f"[red]Template '{template_id}' não encontrado.[/red]")
        raise typer.Exit(1)

    t = templates[0]
    console.print(f"[bold]Template:[/bold] {t.name}")
    console.print(f"  ID: {t.template_id}")
    console.print(f"  Objetivo: {t.objective}")
    console.print(f"  Formato: {t.format or 'qualquer'}")
    console.print(f"  Hook: {t.hook_template}")
    console.print(f"  Corpo: {t.body_template}")
    console.print(f"  CTA: {t.cta_template}")
    console.print(f"  Hashtags: {', '.join(t.hashtag_suggestions) if t.hashtag_suggestions else '(nenhuma)'}")
    if t.notes:
        console.print(f"  Notas: {t.notes}")

# ---------------------------------------------------------------------------
# WORKFLOW COMMANDS
# ---------------------------------------------------------------------------


workflow_app = typer.Typer(
    name="workflow",
    help="Pipeline ponta a ponta: IDEA → PRODUCE → DRAFT → QUEUE",
    add_completion=False,
)


@workflow_app.command(name="run")
def wf_run(
    topic: str = typer.Argument(..., help="Tema do conteúdo"),
    pagina: str = typer.Option(..., "--pagina", help="Handle Instagram (ex: afamiliatigrereal)"),
    formato: str = typer.Option("carrossel", "--formato", help="carrossel, reel, feed, stories"),
    objective: str = typer.Option("alcance", "--objective", help="alcance, autoridade, conversao, relacionamento"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simular sem executar"),
):
    """Executa pipeline completo: IDEA → PLAN → BRIEF → PRODUCE → DRAFT."""
    from src.workflow import WorkflowEngine

    engine = WorkflowEngine()
    result = engine.run(
        topic=topic,
        pagina=pagina,
        formato=formato,
        objective=objective,
        dry_run=dry_run,
    )

    console.print(f"\n[bold]Workflow:[/bold] {result.workflow_id[:8]} — {topic}")
    console.print(f"  Página: @{pagina}  |  Formato: {formato}")

    for stage, status in result.stages.items():
        icon = {"success": "[green]✅[/green]", "failed": "[red]❌[/red]",
                "running": "[yellow]⏳[/yellow]", "pending": "[dim]⬜[/dim]",
                "skipped": "[blue]⏭️[/blue]", "blocked": "[red]🚫[/red]"}
        s = result.stages[stage]
        console.print(f"  {icon.get(s, '❓')} {stage}: {s}")

    if result.queue_id:
        console.print(f"\n  Queue ID: {result.queue_id[:8]}")
    if result.draft_id:
        console.print(f"  Draft ID: {result.draft_id[:8]}")
    if result.job_id:
        console.print(f"  Job ID: {result.job_id[:8]}")
    if result.errors:
        console.print(f"\n  [red]Erros ({len(result.errors)}):[/red]")
        for e in result.errors:
            console.print(f"    - {e}")

    # Next action
    if result.draft_id:
        console.print(f"\n[bold]Próximo passo:[/bold] aprovar o draft com:")
        console.print(f"  omnis approvals approve {result.draft_id[:8]}")
    elif result.queue_id:
        console.print(f"\n[bold]Próximo passo:[/bold] criar legenda com:")
        console.print(f"  omnis captions create {result.queue_id[:8]} --text \"...\"")


@workflow_app.command(name="enqueue")
def wf_enqueue(
    draft_id: str = typer.Argument(..., help="ID do ArgosDraft"),
):
    """Enfileira um draft no Publisher OS BullMQ para publicação."""
    from src.workflow import WorkflowEngine

    engine = WorkflowEngine()
    result = engine.enqueue_draft(draft_id)

    if result.get("error"):
        console.print(f"[red]Erro:[/red] {result['error']}")
        raise typer.Exit(1)

    console.print(f"[green]Draft {draft_id[:8]} enfileirado com sucesso![/green]")
    if result.get("result"):
        console.print(f"  Resposta: {result['result']}")


@workflow_app.command(name="status")
def wf_status():
    """Status do ecossistema de workflow."""
    from src.workflow import WorkflowEngine

    engine = WorkflowEngine()
    status_data = engine.status()

    console.print("[bold]Workflow Engine — Status[/bold]\n")

    # Publisher OS
    pub = status_data.get("publisher_os", {})
    pub_status = pub.get("status", "unknown")
    pub_icon = "[green]OK[/green]" if pub_status == "ok" else "[red]OFFLINE[/red]"
    console.print(f"  Publisher OS: {pub_icon}")
    if pub.get("error"):
        console.print(f"    [red]{pub['error']}[/red]")

    # Queue
    q = status_data.get("queue", {})
    console.print(f"\n  Content Queue: {q.get('total', 0)} itens")
    console.print(f"    needs_asset: {q.get('needs_asset', 0)}")
    console.print(f"    needs_caption: {q.get('needs_caption', 0)}")
    console.print(f"    approved: {q.get('approved', 0)}")
    console.print(f"    scheduled: {q.get('scheduled', 0)}")

    # Workflows recentes
    wf_list = status_data.get("workflows", [])
    console.print(f"\n  Workflows recentes: {len(wf_list)}")
    for w in wf_list[-5:]:
        stages_ok = sum(1 for s in w.get("stages", {}).values() if s == "success")
        stages_total = len(w.get("stages", {}))
        console.print(f"    [{w['workflow_id'][:8]}] {w['topic'][:30]:30} {stages_ok}/{stages_total}")


@workflow_app.command(name="list")
def wf_list(
    limit: int = typer.Option(10, "--limit", help="Número de workflows"),
):
    """Lista workflows executados."""
    import json as _json
    from pathlib import Path

    wf_path = os.path.join(_OMNIS_ROOT, "data", "workflow_results.jsonl")
    if not os.path.isfile(wf_path):
        console.print("Nenhum workflow executado ainda.")
        return

    items = []
    with open(wf_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    items.append(_json.loads(line))
                except _json.JSONDecodeError:
                    continue

    items = items[-limit:]
    table = Table(title=f"Workflows ({len(items)})")
    table.add_column("ID", style="cyan")
    table.add_column("Tema")
    table.add_column("Página")
    table.add_column("Formato")
    table.add_column("Stages")
    table.add_column("Criado")

    for w in items:
        stages_ok = sum(1 for s in w.get("stages", {}).values() if s == "success")
        stages_total = len(w.get("stages", {}))
        table.add_row(
            w["workflow_id"][:8],
            w.get("topic", "?")[:25],
            f"@{w.get('pagina', '?')}",
            w.get("formato", "?"),
            f"{stages_ok}/{stages_total}",
            w.get("created_at", "?")[:10],
        )
    console.print(table)


# ---------------------------------------------------------------------------
# HEALTH SERVER COMMANDS
# ---------------------------------------------------------------------------

health_app = typer.Typer(
    name="health-server",
    help="OMNIS Health HTTP server — start/stop/status",
    add_completion=False,
)


@health_app.command(name="start")
def health_server_start(
    port: int = typer.Option(0, help="Porta (0 = automatica)"),
    per_check_timeout: float = typer.Option(10.0, help="Timeout por check em segundos"),
    total_timeout: float = typer.Option(60.0, help="Timeout total em segundos"),
):
    """Inicia o health server em background."""
    from src.omnis_health.server import (
        HealthServer,
        ServerState,
        save_server_state,
        is_server_alive,
    )
    from datetime import datetime, timezone

    if is_server_alive():
        state = __import__("src.omnis_health.server", fromlist=["load_server_state"]).load_server_state()
        console.print(f"[yellow]Health server ja esta rodando na porta {state.port if state else '?'}[/yellow]")
        raise typer.Exit(1)

    server = HealthServer(port=port, per_check_timeout_s=per_check_timeout, total_timeout_s=total_timeout)
    actual_port = server.start()
    state = ServerState(
        pid=os.getpid(),
        port=actual_port,
        started_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    save_server_state(state)
    console.print(f"[green]Health server iniciado em http://127.0.0.1:{actual_port}/health[/green]")


@health_app.command(name="stop")
def health_server_stop():
    """Para o health server."""
    from src.omnis_health.server import load_server_state, clear_server_state, is_server_alive
    import signal

    if not is_server_alive():
        console.print("[yellow]Health server nao esta rodando.[/yellow]")
        clear_server_state()
        raise typer.Exit(0)

    state = load_server_state()
    if state:
        try:
            os.kill(state.pid, signal.SIGTERM)
        except OSError:
            pass
        clear_server_state()
        console.print(f"[green]Health server na porta {state.port} parado.[/green]")
    else:
        console.print("[yellow]Estado do server nao encontrado.[/yellow]")


@health_app.command(name="status")
def health_server_status():
    """Mostra status do health server."""
    from src.omnis_health.server import load_server_state, is_server_alive

    if is_server_alive():
        state = load_server_state()
        if state:
            console.print(f"[green]Health server rodando[/green]")
            console.print(f"  URL: http://127.0.0.1:{state.port}/health")
            console.print(f"  PID: {state.pid}")
            console.print(f"  Iniciado: {state.started_at}")
    else:
        console.print("[yellow]Health server parado.[/yellow]")


# ---------------------------------------------------------------------------
# MISSION COMMANDS (OMNIS Supreme — Fase A)
# ---------------------------------------------------------------------------


mission_app = typer.Typer(
    name="mission",
    help="OMNIS Supreme — executa missões agentic",
    add_completion=False,
)


@mission_app.command(name="run")
def mission_run(
    text: str = typer.Argument(..., help="Descrição da missão em texto livre"),
    dry_run: bool = typer.Option(True, "--dry-run/--executar", help="Dry-run (padrão) ou executar de fato"),
    setor: str = typer.Option("", "--setor", help="Forçar setor (vazio = auto-detectar)"),
):
    """Executa o pipeline completo de missão: intake → engine → mapper → report.

    Exemplo: omnis mission run "cria campanha hotel nordeste 30 dias"
    """
    from src.agentic.mission_intake import MissionIntake
    from src.agentic.mission_engine import MissionEngine
    from src.agentic.deliverable_mapper import DeliverableMapper
    from src.reports.report_generator import ReportGenerator

    session_id = new_session_id()
    start = time.time()

    # Step 1 — Intake
    intake = MissionIntake()
    parsed = intake.parse(text)

    if setor:
        parsed.setor = setor

    console.print(Panel.fit(
        f"[bold]Objetivo:[/bold] {parsed.objetivo}\n"
        f"[bold]Setor:[/bold] {parsed.setor}  |  "
        f"[bold]Tipo:[/bold] {parsed.tipo}  |  "
        f"[bold]Risco:[/bold] {parsed.risco}  |  "
        f"[bold]Prazo:[/bold] {parsed.prazo or '—'}",
        title="[bold cyan]Mission Intake[/bold cyan]",
    ))

    if parsed.warnings:
        for w in parsed.warnings:
            console.print(f"[yellow]⚠ {w}[/yellow]")

    if dry_run:
        console.print("\n[yellow][DRY-RUN] Missão analisada. Use --executar para criar.[/yellow]")
        # Step 3 — Show what would be delivered
        mapper = DeliverableMapper()
        manifest = mapper.map(parsed)
        if manifest.deliverables:
            console.print("\n[bold]Entregáveis previstos:[/bold]")
            for d in manifest.deliverables:
                export_tag = " [dim](export)[/dim]" if d.target_subdir == "06_exports" else ""
                req_tag = "" if d.required else " [dim](opcional)[/dim]"
                console.print(f"  • `{d.filename}` — {d.description}{export_tag}{req_tag}")
        dur = int((time.time() - start) * 1000)
        log_mission(session_id, "mission-run", "dry_run", dur,
                    summary=f"intake={parsed.setor}/{parsed.tipo}, risco={parsed.risco}")
        return

    # Step 2 — Engine: open mission
    engine = MissionEngine()
    contract = engine.open_mission(
        objetivo=parsed.objetivo,
        setor=parsed.setor,
    )

    console.print(f"\n[green]Missão aberta:[/green] {contract.mission_id}")
    console.print(f"  Pasta: {contract.mission_path}")

    # Step 3 — Deliverable Mapper
    mapper = DeliverableMapper()
    manifest = mapper.map(parsed)
    manifest.mission_id = contract.mission_id

    # Write deliverable manifest to mission folder
    import json as _json
    manifest_path = Path(contract.mission_path) / "deliverables_manifest.json"
    manifest_path.write_text(
        _json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Step 4 — Report Generator
    generator = ReportGenerator()
    report = generator.generate(
        contract=contract,
        intake=parsed,
        manifest=manifest,
        next_action="Aguardando execução dos entregáveis.",
    )

    # Summary table
    summary = Table(title=f"Missão {contract.mission_id}")
    summary.add_column("Campo", style="cyan")
    summary.add_column("Valor")
    summary.add_row("Status", contract.status)
    summary.add_row("Setor", contract.setor)
    summary.add_row("Tipo", parsed.tipo)
    summary.add_row("Risco", parsed.risco)
    summary.add_row("Prazo", parsed.prazo or "—")
    summary.add_row("Entregáveis", str(len(manifest.deliverables)))
    summary.add_row("Relatório", str(Path(contract.mission_path) / "relatorio_final.md"))
    console.print(summary)

    dur = int((time.time() - start) * 1000)
    log_mission(session_id, "mission-run", "success", dur,
                summary=f"id={contract.mission_id}, setor={contract.setor}, deliverables={len(manifest.deliverables)}")


@mission_app.command(name="list")
def mission_list(
    limit: int = typer.Option(10, "--limit", help="Número máximo de missões"),
):
    """Lista missões recentes."""
    from src.agentic.mission_engine import MissionEngine
    engine = MissionEngine()
    missions_dir = engine.missions_root

    if not missions_dir.exists():
        console.print("Nenhuma missão encontrada.")
        return

    folders = sorted(missions_dir.glob("MIS-*"), reverse=True)[:limit]
    if not folders:
        console.print("Nenhuma missão encontrada.")
        return

    table = Table(title=f"Missões ({len(folders)})")
    table.add_column("ID", style="cyan")
    table.add_column("Status")
    table.add_column("Objetivo")
    table.add_column("Setor")

    for folder in folders:
        contract = engine.get_mission(folder.name)
        if contract:
            table.add_row(
                contract.mission_id,
                contract.status,
                contract.objetivo[:50],
                contract.setor,
            )
        else:
            table.add_row(folder.name, "?", "—", "—")

    console.print(table)


@mission_app.command(name="show")
def mission_show(
    mission_id: str = typer.Argument(..., help="ID da missão (ex: MIS-20260518-001)"),
):
    """Mostra detalhes de uma missão."""
    from src.agentic.mission_engine import MissionEngine
    engine = MissionEngine()
    contract = engine.get_mission(mission_id)

    if not contract:
        console.print(f"[red]Missão '{mission_id}' não encontrada.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Missão:[/bold] {contract.mission_id}")
    console.print(f"  Status: {contract.status}")
    console.print(f"  Objetivo: {contract.objetivo}")
    console.print(f"  Setor: {contract.setor}")
    console.print(f"  Criado por: {contract.criado_por}")
    console.print(f"  Aberto em: {contract.timestamp}")
    console.print(f"  Fechado em: {contract.closed_at or '—'}")
    console.print(f"  Pasta: {contract.mission_path}")

    # Check if relatorio_final.md exists
    if contract.mission_path:
        report_path = Path(contract.mission_path) / "relatorio_final.md"
        if report_path.exists():
            console.print(f"\n[bold]Relatório:[/bold] {report_path}")
            content = report_path.read_text(encoding="utf-8")
            console.print(Panel(content[:2000], title="relatorio_final.md"))


@mission_app.command(name="close")
def mission_close(
    mission_id: str = typer.Argument(..., help="ID da missão para fechar"),
):
    """Fecha uma missão (status=closed)."""
    from src.agentic.mission_engine import MissionEngine
    engine = MissionEngine()
    contract = engine.close_mission(mission_id)

    if not contract:
        console.print(f"[red]Missão '{mission_id}' não encontrada.[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Missão {mission_id} fechada.[/green]")
    console.print(f"  Fechada em: {contract.closed_at}")


# ---------------------------------------------------------------------------
# REGISTRATION BLOCK — centralizado, ordem determinística
# ---------------------------------------------------------------------------

from src.routers import factory_router, system_router
from src.cli_agent import agent_app
from src.cli_lego import lego_app

factory_router.register(app)   # assets, offline, render, quality, campaign, manual-publish, delivery
system_router.register(app)    # argos-drafts, creative, publisher, forge, pipeline, missions, tools, metrics, oauth, post

# Inline apps (definidos neste arquivo)
app.add_typer(agent_app)
app.add_typer(sales_app)
app.add_typer(memory_app)
app.add_typer(llm_app)
app.add_typer(video_assets_app)
app.add_typer(accounts_app)
app.add_typer(queue_app)
app.add_typer(captions_app)
app.add_typer(approvals_app)
app.add_typer(templates_app)
app.add_typer(workflow_app)
app.add_typer(mission_app)
app.add_typer(idea_app)
app.add_typer(health_app)
app.add_typer(local_app, name="local")
app.add_typer(lego_app)
app.add_typer(content_app)
app.add_typer(runs_app)
app.add_typer(notion_app)
app.add_typer(akasha_app)


# ---------------------------------------------------------------------------
# HEALTH SCORE (WAVE 10)
# ---------------------------------------------------------------------------

@app.command(name="health-score")
def cmd_health_score(
    json_out: bool = typer.Option(False, "--json", help="Saída em JSON"),
    history: int = typer.Option(0, "--history", "-H", help="Exibe N últimos scores do histórico"),
    persist: bool = typer.Option(True, "--persist/--no-persist", help="Salvar score no log"),
) -> None:
    """Score único de saúde do sistema OMNIS (0-100 | verde/amarelo/vermelho).

    Agrega: Ollama, Akasha/Docker, drafts pendentes, conteúdo recente, mission logger.
    """
    from src.health.score import HealthScorer

    scorer = HealthScorer(persist=persist)

    if history > 0:
        records = scorer.read_history(limit=history)
        if json_out:
            console.print_json(json.dumps(records, ensure_ascii=False))
        else:
            table = Table(title=f"Health Score — últimos {history} registros")
            table.add_column("Data",  style="dim",   width=17)
            table.add_column("Score", justify="right", width=6)
            table.add_column("Cor",   width=10)
            _COLOR_STYLE = {"green": "green", "yellow": "yellow", "red": "red"}
            for r in records:
                color = r.get("color", "?")
                s = _COLOR_STYLE.get(color, "white")
                table.add_row(
                    r.get("date", "?"),
                    str(r.get("score", "?")),
                    f"[{s}]{color}[/{s}]",
                )
            console.print(table)
        return

    hs = scorer.calculate()

    if json_out:
        console.print_json(json.dumps(hs.to_dict(), ensure_ascii=False))
        return

    _ICON = {"green": "[VERDE]", "yellow": "[AMARELO]", "red": "[VERMELHO]"}
    icon = _ICON.get(hs.color, "")
    console.print(f"\n[bold]HEALTH SCORE: {hs.score}/100[/bold]  [{hs.color}]{icon}[/{hs.color}]")
    console.print(f"   gerado em: {hs.generated_at[:19]} UTC\n")

    table = Table(show_header=True)
    table.add_column("Check",   style="cyan",  width=22)
    table.add_column("Score",   justify="right", width=10)
    table.add_column("Status",  width=8)
    table.add_column("Detalhe", width=45)

    _ST = {"ok": "green", "warn": "yellow", "fail": "red", "skip": "dim"}
    for c in hs.checks:
        st = _ST.get(c.status, "")
        table.add_row(
            c.name,
            f"{c.score}/{c.max_score}",
            f"[{st}]{c.status}[/{st}]",
            c.detail,
        )
    console.print(table)

    if hs.warnings:
        for w in hs.warnings:
            console.print(f"  [yellow]⚠  {w}[/yellow]")

    if persist:
        console.print(f"\n  [dim]score salvo em logs/health_scores.jsonl[/dim]")


if __name__ == "__main__":
    app()






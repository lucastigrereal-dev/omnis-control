"""CLI for app idea intake: omnis idea new | list | show."""
from __future__ import annotations

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

from src.app_factory.api_contract import build_api_contract
from src.app_factory.artifact_registry import ArtifactRegistry, ArtifactRegistryEntry
from src.app_factory.bundle_exporter import build_bundle
from src.app_factory.diff_engine import diff_ideas, diff_schemas, diff_api_contracts
from src.app_factory.docs_generator import build_generated_docs
from src.app_factory.errors import InvalidAppIdeaError
from src.app_factory.idea_store import IdeaStore
from src.app_factory.models import AppBlueprint, AppIdea, AppRequirement
from src.app_factory.pipeline import build_planning_pipeline
from src.app_factory.prd_service import StoredIdeaPRDGenerator
from src.app_factory.quality_gate import validate_bundle
from src.app_factory.quality_score import compute_quality_score
from src.app_factory.recovery import (
    PipelineState,
    init_pipeline_state,
    build_recovery_plan,
    StageStatus,
    STAGE_ORDER,
)
from src.app_factory.schema_planner import build_schema_plan
from src.app_factory.scaffold_engine import run_scaffold
from src.app_factory.scaffold_plan import build_scaffold_plan
from src.app_factory.status_tracker import StatusTracker
from src.app_factory.storage_safety import (
    StorageSafetyPolicy,
    audit_directory,
    validate_command_safety,
    validate_dry_run_enforcement,
)
from src.app_factory.task_plan import build_task_plan

idea_app = typer.Typer(
    name="idea",
    help="App Factory - entrada de ideias de aplicativos",
    add_completion=False,
)

console = Console()


@idea_app.command(name="new")
def idea_new(
    title: str = typer.Option(..., "--title", help="Titulo do aplicativo"),
    description: str = typer.Option(..., "--description", help="Descricao do que o app faz"),
    features: str = typer.Option("", "--features", help="Features separadas por virgula"),
    constraints: str = typer.Option("", "--constraints", help="Restricoes separadas por virgula"),
    domain: str = typer.Option("", "--domain", help="Dominio, ex: financas, saude, educacao"),
    target_audience: str = typer.Option("", "--target-audience", help="Publico-alvo"),
    apply: bool = typer.Option(False, "--apply", help="Gravar ideia; sem --apply e dry-run"),
) -> None:
    """Cria uma nova ideia de aplicativo."""
    feature_list = [f.strip() for f in features.split(",") if f.strip()]
    constraint_list = [c.strip() for c in constraints.split(",") if c.strip()]

    idea = AppIdea.new(
        title=title,
        description=description,
        target_audience=target_audience,
        features=feature_list,
        constraints=constraint_list,
        domain=domain,
    )

    is_dry_run = not apply
    store = IdeaStore(dry_run=is_dry_run)

    try:
        store.save(idea)
    except InvalidAppIdeaError as exc:
        console.print(f"[red]Erro de validacao:[/red] {exc}")
        raise typer.Exit(1) from exc

    if is_dry_run:
        console.print("[yellow]Dry-run:[/yellow] ideia validada mas NAO gravada.")
        console.print(f"  ID: {idea.idea_id}")
        console.print(f"  Titulo: {idea.title}")
        console.print(f"  Dominio: {idea.domain or '(nao definido)'}")
        console.print("  Use [cyan]--apply[/cyan] para gravar.")
    else:
        console.print(f"[green]Ideia gravada:[/green] {idea.idea_id}")
        console.print(f"  Titulo: {idea.title}")
        console.print(f"  Status: {idea.status}")


@idea_app.command(name="list")
def idea_list(
    status: str = typer.Option(None, "--status", help="Filtrar por status: draft, planned, generated"),
) -> None:
    """Lista ideias de aplicativo cadastradas."""
    store = IdeaStore(dry_run=True)
    items = store.list_by_status(status) if status else store.list_all()

    if not items:
        console.print("Nenhuma ideia cadastrada.")
        return

    table = Table(title=f"Ideias ({len(items)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Titulo")
    table.add_column("Dominio")
    table.add_column("Status")
    table.add_column("Submetida")

    for idea in items:
        table.add_row(
            idea.idea_id[:8],
            idea.title[:40],
            idea.domain or "-",
            idea.status,
            idea.submitted_at[:10] if idea.submitted_at else "-",
        )

    console.print(table)


@idea_app.command(name="show")
def idea_show(
    idea_id: str = typer.Argument(..., help="ID da ideia"),
) -> None:
    """Mostra detalhes completos de uma ideia."""
    store = IdeaStore(dry_run=True)
    idea = store.get(idea_id)

    if idea is None:
        console.print(f"[red]Ideia '{idea_id}' nao encontrada.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Ideia:[/bold] {idea.idea_id}")
    console.print(f"  Titulo: {idea.title}")
    console.print(f"  Descricao: {idea.description}")
    console.print(f"  Dominio: {idea.domain or '(nao definido)'}")
    console.print(f"  Publico-alvo: {idea.target_audience or '(nao definido)'}")
    console.print(f"  Status: {idea.status}")
    console.print(f"  Submetida: {idea.submitted_at}")

    if idea.features:
        console.print(f"  Features: {', '.join(idea.features)}")
    else:
        console.print("  Features: [dim](nenhuma)[/dim]")

    if idea.constraints:
        console.print(f"  Restricoes: {', '.join(idea.constraints)}")
    else:
        console.print("  Restricoes: [dim](nenhuma)[/dim]")


@idea_app.command(name="plan")
def idea_plan(
    idea_id: str = typer.Argument(..., help="ID da ideia"),
) -> None:
    """Gera um PRD dry-run para uma ideia armazenada."""
    store = IdeaStore(dry_run=True)
    generator = StoredIdeaPRDGenerator(store=store)
    try:
        result = generator.generate(idea_id, dry_run=True)
    except Exception as exc:
        console.print(f"[red]Erro ao gerar PRD:[/red] {exc}")
        raise typer.Exit(1) from exc

    console.print(f"[green]PRD gerado em dry-run:[/green] {result.artifact.artifact_id}")
    console.print(f"  Ideia: {result.idea_id}")
    console.print(f"  Blueprint: {result.artifact.blueprint_id}")


@idea_app.command(name="schema")
def idea_schema(idea_id: str = typer.Argument(..., help="ID da ideia")) -> None:
    """Gera plano de schema de banco em dry-run."""
    blueprint = _blueprint_for_idea(idea_id)
    plan = build_schema_plan(blueprint, dry_run=True)
    console.print(f"[green]Schema plan dry-run:[/green] {plan.blueprint_id}")
    for table in plan.tables:
        console.print(f"  {table.name}: {', '.join(field.name + ':' + field.type for field in table.fields)}")


@idea_app.command(name="api")
def idea_api(idea_id: str = typer.Argument(..., help="ID da ideia")) -> None:
    """Gera contrato de API em dry-run."""
    blueprint = _blueprint_for_idea(idea_id)
    schema = build_schema_plan(blueprint, dry_run=True)
    contract = build_api_contract(blueprint, schema, dry_run=True)
    console.print(f"[green]API contract dry-run:[/green] {contract.blueprint_id}")
    for endpoint in contract.endpoints:
        console.print(f"  {endpoint.method} {endpoint.path}")


@idea_app.command(name="tasks")
def idea_tasks(idea_id: str = typer.Argument(..., help="ID da ideia")) -> None:
    """Gera plano de tarefas de implementação em dry-run."""
    blueprint = _blueprint_for_idea(idea_id)
    schema = build_schema_plan(blueprint, dry_run=True)
    contract = build_api_contract(blueprint, schema, dry_run=True)
    plan = build_task_plan(blueprint, schema, contract, dry_run=True)
    console.print(f"[green]Task plan dry-run:[/green] {plan.blueprint_id}")
    for task in plan.tasks:
        console.print(f"  [{task.area}] {task.task_id} - {task.title}")


@idea_app.command(name="export")
def idea_export(
    idea_id: str = typer.Argument(..., help="ID da ideia"),
    fmt: str = typer.Option("md", "--format", help="Formato: md ou json"),
) -> None:
    """Exporta bundle completo no stdout em dry-run."""
    bundle = _bundle_for_idea(idea_id)
    if fmt == "json":
        console.print(bundle.to_json())
    else:
        console.print(bundle.to_markdown())


@idea_app.command(name="validate")
def idea_validate(idea_id: str = typer.Argument(..., help="ID da ideia")) -> None:
    """Valida outputs planejados do App Factory."""
    report = validate_bundle(_bundle_for_idea(idea_id), dry_run=True)
    status = "PASS" if report.passed else "FAIL"
    console.print(f"[green]Quality gate:[/green] {status}")
    for issue in report.issues:
        console.print(f"  issue: {issue}")
    for warning in report.warnings:
        console.print(f"  warning: {warning}")
    if not report.passed:
        raise typer.Exit(1)


@idea_app.command(name="artifacts")
def idea_artifacts(idea_id: str = typer.Argument(..., help="ID da ideia")) -> None:
    """Lista artefatos planejados para uma ideia."""
    bundle = _bundle_for_idea(idea_id)
    registry = ArtifactRegistry(dry_run=True)
    for artifact_type, artifact_id in [
        ("prd", bundle.artifact_id),
        ("schema", bundle.schema_plan.blueprint_id),
        ("api", bundle.api_contract.blueprint_id),
        ("tasks", bundle.task_plan.blueprint_id),
        ("bundle", bundle.artifact_id),
    ]:
        registry.register(ArtifactRegistryEntry(idea_id, artifact_type, artifact_id))
    console.print(f"[green]Artifacts dry-run:[/green] {idea_id}")
    for entry in registry.list_for_idea(idea_id):
        console.print(f"  {entry.artifact_type}: {entry.artifact_id}")


@idea_app.command(name="scaffold-plan")
def idea_scaffold_plan(idea_id: str = typer.Argument(..., help="ID da ideia")) -> None:
    """Gera plano de scaffold sem criar app real."""
    bundle = _bundle_for_idea(idea_id)
    plan = build_scaffold_plan(bundle.schema_plan, bundle.api_contract, bundle.task_plan, dry_run=True)
    console.print(f"[green]Scaffold plan dry-run:[/green] {plan.blueprint_id}")
    for file in plan.files:
        console.print(f"  {file.path} - {file.purpose}")


@idea_app.command(name="scaffold")
def idea_scaffold(
    idea_id: str = typer.Argument(..., help="ID da ideia"),
    output_dir: str = typer.Option(".test_tmp/app_factory_scaffold", "--output-dir", help="Diretorio alvo"),
    dry_run: bool = typer.Option(True, "--dry-run/--write", help="Dry-run por padrao; --write grava arquivos"),
) -> None:
    """Executa scaffold seguro em dry-run por padrao."""
    bundle = _bundle_for_idea(idea_id)
    plan = build_scaffold_plan(bundle.schema_plan, bundle.api_contract, bundle.task_plan, dry_run=True)
    result = run_scaffold(plan, output_dir=Path(output_dir), dry_run=dry_run)
    console.print(f"[green]Scaffold {'dry-run' if result.dry_run else 'write'}:[/green] {len(result.planned_files)} arquivos")
    for warning in result.warnings:
        console.print(f"  warning: {warning}")


@idea_app.command(name="docs")
def idea_docs(idea_id: str = typer.Argument(..., help="ID da ideia")) -> None:
    """Gera documentacao tecnica planejada no stdout."""
    docs = build_generated_docs(_bundle_for_idea(idea_id), dry_run=True)
    console.print(f"[green]Docs dry-run:[/green] {docs.artifact_id}")
    for name in docs.documents:
        console.print(f"  {name}")


@idea_app.command(name="build-plan")
def idea_build_plan(
    idea_id: str = typer.Argument(..., help="ID da ideia"),
    safety_dir: str = typer.Option(None, "--safety-dir", help="Auditar diretorio com storage safety"),
) -> None:
    """Roda pipeline PRD -> schema -> API -> tasks -> validate."""
    try:
        result = build_planning_pipeline(
            idea_id, store=IdeaStore(dry_run=True), dry_run=True,
            with_quality_score=True, with_recovery=True,
            with_storage_safety=safety_dir is not None,
            safety_target_dir=safety_dir,
        )
    except Exception as exc:
        console.print(f"[red]Pipeline falhou:[/red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]Build plan dry-run:[/green] {result.idea_id}")
    console.print(f"  Bundle: {result.bundle.artifact_id}")
    console.print(f"  Quality Gate: {'PASS' if result.quality_report.passed else 'FAIL'}")
    if result.quality_score:
        qs = result.quality_score
        overall = qs.get("overall", {})
        console.print(f"  Quality Score: {overall.get('percentage', '?')}% ({overall.get('grade', '?')})")
    if result.pipeline_state:
        ps = result.pipeline_state
        console.print(f"  Pipeline Progress: {ps.get('progress_pct', '?')}% — {ps.get('overall_status', '?')}")
    console.print(f"  Docs: {len(result.docs.documents)}")
    if result.storage_safety:
        ss = result.storage_safety
        console.print(f"  Storage Safety: {'PASS' if ss.get('passed') else 'FAIL'} ({ss.get('scanned_files', 0)} files)")


@idea_app.command(name="safety")
def idea_safety(
    idea_id: str = typer.Option(None, "--idea-id", help="ID da ideia para auditar (opcional, audita dir)"),
    target_dir: str = typer.Option(".", "--dir", help="Diretorio para auditar"),
    scan: bool = typer.Option(True, "--scan/--no-scan", help="Escanear arquivos"),
    check_cmd: str = typer.Option(None, "--check-cmd", help="Verificar seguranca de um comando shell"),
) -> None:
    """Audita seguranca de armazenamento — no-touch zones, comandos destrutivos."""
    policy = StorageSafetyPolicy()

    if check_cmd:
        violations = validate_command_safety(check_cmd, policy)
        if not violations:
            console.print("[green]Comando seguro.[/green]")
        else:
            console.print("[red]Comando BLOQUEADO:[/red]")
            for v in violations:
                console.print(f"  {v.severity}: {v.detail}")
            raise typer.Exit(1)
        return

    report = audit_directory(target_dir, policy, scan_files=scan)
    status = "PASS" if report.passed else "FAIL"
    console.print(f"[{'green' if report.passed else 'red'}]Storage Safety Audit:[/{'green' if report.passed else 'red'}] {status}")
    console.print(f"  Diretorio: {report.target_path}")
    console.print(f"  Arquivos escaneados: {report.scanned_files}")
    console.print(f"  Violations: {report.critical_count}, Warnings: {report.warning_count}")
    for v in report.violations:
        console.print(f"  [red]BLOCKED:[/red] {v.get('path')} - {v.get('detail')}")
    for w in report.warnings:
        console.print(f"  [yellow]WARN:[/yellow] {w}")
    if not report.passed:
        raise typer.Exit(1)


@idea_app.command(name="quality")
def idea_quality(idea_id: str = typer.Argument(..., help="ID da ideia")) -> None:
    """Calcula quality score do bundle planejado."""
    bundle = _bundle_for_idea(idea_id)
    schema_tables = [
        {
            "name": t.name,
            "fields": [f.__dict__ for f in t.fields],
            "relationships": t.relationships,
            "indexes": t.indexes,
        }
        for t in bundle.schema_plan.tables
    ]
    score = compute_quality_score(
        bundle.artifact_id,
        bundle.prd_markdown,
        schema_tables,
        [e.__dict__ for e in bundle.api_contract.endpoints],
        [t.__dict__ for t in bundle.task_plan.tasks],
    )
    console.print(f"[bold]Quality Score:[/bold] {score.overall.percentage}% ({score.overall.grade})")
    console.print(f"  PRD:     {score.prd_score.percentage}% ({score.prd_score.grade})")
    console.print(f"  Schema:  {score.schema_score.percentage}% ({score.schema_score.grade})")
    console.print(f"  API:     {score.api_score.percentage}% ({score.api_score.grade})")
    console.print(f"  Tasks:   {score.tasks_score.percentage}% ({score.tasks_score.grade})")
    for note in score.overall.notes:
        console.print(f"  [dim]{note}[/dim]")


@idea_app.command(name="diff")
def idea_diff(
    idea_left: str = typer.Argument(..., help="ID da primeira ideia"),
    idea_right: str = typer.Argument(..., help="ID da segunda ideia"),
) -> None:
    """Compara duas ideias mostrando diferencas estruturais."""
    left = _blueprint_for_idea(idea_left)
    right = _blueprint_for_idea(idea_right)
    report = diff_ideas(
        _load_idea_dict(idea_left),
        _load_idea_dict(idea_right),
        left_label=idea_left,
        right_label=idea_right,
    )
    console.print(report.to_summary_text())

    # Also diff schemas
    left_schema = build_schema_plan(left, dry_run=True)
    right_schema = build_schema_plan(right, dry_run=True)
    schema_report = diff_schemas(
        [_schema_table_to_dict(t) for t in left_schema.tables],
        [_schema_table_to_dict(t) for t in right_schema.tables],
        left_label=idea_left + "_schema",
        right_label=idea_right + "_schema",
    )
    if schema_report.has_differences:
        console.print(f"\n[yellow]Schema diffs ({schema_report.change_count}):[/yellow]")
        for e in schema_report.entries:
            if e.is_change:
                console.print(f"  {e.kind}: {e.field}")


@idea_app.command(name="recovery")
def idea_recovery(
    idea_id: str = typer.Argument(..., help="ID da ideia"),
    force: bool = typer.Option(False, "--force", help="Forcar criacao de recovery plan mesmo sem falha"),
) -> None:
    """Mostra ou constroi plano de recuperacao para uma ideia."""
    state = init_pipeline_state(idea_id)
    state.mark_completed("validate_idea")
    state.mark_failed("extract_requirements", "simulated: missing data")

    plan = build_recovery_plan(state, force_retry=force)
    if not plan.can_resume:
        console.print("[yellow]Nenhum recovery necessario — pipeline sem falhas.[/yellow]")
        return

    console.print(f"[green]Recovery Plan:[/green]")
    console.print(f"  Resume from: {plan.resume_from_stage}")
    console.print(f"  Failed stages: {', '.join(plan.failed_stages)}")
    console.print(f"  Progress before failure: {plan.state.progress_pct}%")
    for stage in STAGE_ORDER:
        if stage in plan.state.stages:
            s = plan.state.stages[stage]
            icon = {"completed": "[green]+[/green]", "failed": "[red]![/red]", "pending": "[dim]o[/dim]", "running": "[yellow]>[/yellow]", "skipped": "[dim]-[/dim]"}
            console.print(f"  {icon.get(s.status.value, '?')} {stage}: {s.status.value}")


@idea_app.command(name="status")
def idea_status(
    idea_id: str = typer.Option(None, "--idea-id", help="Status de uma ideia especifica"),
    summary: bool = typer.Option(False, "--summary", help="Mostrar resumo agregado"),
) -> None:
    """Mostra status do pipeline para ideias registradas."""
    tracker = StatusTracker()
    store = IdeaStore(dry_run=True)
    ideas = store.list_all()

    for idea in ideas:
        state = tracker.register_idea(idea.idea_id, idea.title)
        state.mark_completed("validate_idea")

    if summary:
        s = tracker.summary()
        console.print(f"[bold]Pipeline Summary:[/bold] {s.total} ideias")
        console.print(f"  Completo: [green]{s.completed}[/green] | Pendente: [dim]{s.pending}[/dim] | Falhou: [red]{s.failed}[/red] | Running: [yellow]{s.running}[/yellow]")
        console.print(f"  Progresso medio: {s.avg_progress_pct}%")
        console.print(f"  Saudavel: {'[green]Sim[/green]' if s.healthy else '[red]Nao[/red]'}")
        return

    if idea_id:
        status = tracker.get_status(idea_id)
        if status is None:
            console.print(f"[red]Ideia '{idea_id}' nao encontrada.[/red]")
            raise typer.Exit(1)
        console.print(f"[bold]{status.title}[/bold] ({status.idea_id})")
        console.print(f"  Status: {status.overall_status}")
        console.print(f"  Progresso: {status.progress_pct}%")
        console.print(f"  Estagio atual: {status.current_stage}")
        if status.failed_stage:
            console.print(f"  [red]Falhou em: {status.failed_stage} — {status.error_message}[/red]")
        return

    all_statuses = tracker.list_all()
    if not all_statuses:
        console.print("Nenhuma ideia registrada para tracking.")
        return

    table = Table(title=f"Pipeline Status ({len(all_statuses)} ideias)")
    table.add_column("ID", style="cyan")
    table.add_column("Titulo")
    table.add_column("Status")
    table.add_column("Progresso")
    table.add_column("Estagio")
    for s in all_statuses:
        color = {"completed": "green", "failed": "red", "running": "yellow"}.get(s.overall_status, "white")
        table.add_row(
            s.idea_id[:8], s.title[:30],
            f"[{color}]{s.overall_status}[/{color}]",
            f"{s.progress_pct}%", s.current_stage,
        )
    console.print(table)


def _blueprint_for_idea(idea_id: str) -> AppBlueprint:
    store = IdeaStore(dry_run=True)
    idea = store.get(idea_id)
    if idea is None:
        console.print(f"[red]Ideia '{idea_id}' nao encontrada.[/red]")
        raise typer.Exit(1)
    requirement = AppRequirement.from_idea(idea)
    return AppBlueprint.from_requirement(requirement)


def _load_idea_dict(idea_id: str) -> dict:
    store = IdeaStore(dry_run=True)
    idea = store.get(idea_id)
    if idea is None:
        console.print(f"[red]Ideia '{idea_id}' nao encontrada.[/red]")
        raise typer.Exit(1)
    return idea.to_dict()


def _schema_table_to_dict(table) -> dict:
    return {
        "name": table.name,
        "fields": [f.__dict__ for f in table.fields],
        "relationships": table.relationships,
        "indexes": table.indexes,
    }


def _bundle_for_idea(idea_id: str):
    store = IdeaStore(dry_run=True)
    prd = StoredIdeaPRDGenerator(store=store).generate(idea_id, dry_run=True)
    blueprint = _blueprint_for_idea(idea_id)
    schema = build_schema_plan(blueprint, dry_run=True)
    contract = build_api_contract(blueprint, schema, dry_run=True)
    tasks = build_task_plan(blueprint, schema, contract, dry_run=True)
    return build_bundle(prd.artifact, schema, contract, tasks, dry_run=True)

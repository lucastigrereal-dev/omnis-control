"""CLI for app idea intake: omnis idea new | list | show."""
from __future__ import annotations

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

from src.app_factory.api_contract import build_api_contract
from src.app_factory.artifact_registry import ArtifactRegistry, ArtifactRegistryEntry
from src.app_factory.bundle_exporter import build_bundle
from src.app_factory.docs_generator import build_generated_docs
from src.app_factory.errors import InvalidAppIdeaError
from src.app_factory.idea_store import IdeaStore
from src.app_factory.models import AppBlueprint, AppIdea, AppRequirement
from src.app_factory.pipeline import build_planning_pipeline
from src.app_factory.prd_service import StoredIdeaPRDGenerator
from src.app_factory.quality_gate import validate_bundle
from src.app_factory.schema_planner import build_schema_plan
from src.app_factory.scaffold_engine import run_scaffold
from src.app_factory.scaffold_plan import build_scaffold_plan
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
def idea_build_plan(idea_id: str = typer.Argument(..., help="ID da ideia")) -> None:
    """Roda pipeline PRD -> schema -> API -> tasks -> validate."""
    try:
        result = build_planning_pipeline(idea_id, store=IdeaStore(dry_run=True), dry_run=True)
    except Exception as exc:
        console.print(f"[red]Pipeline falhou:[/red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]Build plan dry-run:[/green] {result.idea_id}")
    console.print(f"  Bundle: {result.bundle.artifact_id}")
    console.print(f"  Quality: {'PASS' if result.quality_report.passed else 'FAIL'}")
    console.print(f"  Docs: {len(result.docs.documents)}")


def _blueprint_for_idea(idea_id: str) -> AppBlueprint:
    store = IdeaStore(dry_run=True)
    idea = store.get(idea_id)
    if idea is None:
        console.print(f"[red]Ideia '{idea_id}' nao encontrada.[/red]")
        raise typer.Exit(1)
    requirement = AppRequirement.from_idea(idea)
    return AppBlueprint.from_requirement(requirement)


def _bundle_for_idea(idea_id: str):
    store = IdeaStore(dry_run=True)
    prd = StoredIdeaPRDGenerator(store=store).generate(idea_id, dry_run=True)
    blueprint = _blueprint_for_idea(idea_id)
    schema = build_schema_plan(blueprint, dry_run=True)
    contract = build_api_contract(blueprint, schema, dry_run=True)
    tasks = build_task_plan(blueprint, schema, contract, dry_run=True)
    return build_bundle(prd.artifact, schema, contract, tasks, dry_run=True)

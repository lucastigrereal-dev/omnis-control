"""agencia.py — CLI da Agência de Vídeo OMNIS (Camada 1: cortes inteligentes).

Uso:
    python agencia.py video <arquivo> [opções]

Exemplos:
    python agencia.py video gravacao.mp4
    python agencia.py video gravacao.mp4 --perfil oinatalrn --preset reel --dry-run
    python agencia.py video gravacao.mp4 --preset original --max-clips 3
    python agencia.py video gravacao.mp4 --no-dry-run   # Whisper + FFmpeg reais

Presets disponíveis:
    reel      — 1080x1920 9:16 vertical (Instagram Reel)  ← padrão
    feed      — 1080x1080 1:1 quadrado (feed)
    story     — 1080x1920 9:16 (Stories)
    original  — sem reencoding, -c copy (mais rápido)
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

try:
    import typer
except ImportError:  # pragma: no cover
    print("typer não instalado — rode: pip install typer")
    sys.exit(1)

from src.agencia.pipeline import AgenciaPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

app = typer.Typer(
    name="agencia",
    help="Agencia de Video OMNIS -- cortes inteligentes (Camada 1)",
    add_completion=False,
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo("Uso: python agencia.py video <arquivo.mp4>  [--help para opcoes]")


@app.command()
def video(
    arquivo: Path = typer.Argument(..., help="Caminho do vídeo de entrada (.mp4/.mov/.avi)"),
    perfil: str = typer.Option("lucastigrereal", "--perfil", "-p", help="Handle do perfil (pasta de entrega)"),
    preset: str = typer.Option("reel", "--preset", help="reel | feed | story | original"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Simulação (True) ou execução real (False)"),
    max_clips: int = typer.Option(5, "--max-clips", help="Máximo de clipes a gerar"),
    target_duration: float = typer.Option(30.0, "--target-duration", help="Duração alvo de cada clipe (segundos)"),
    max_hooks: int = typer.Option(10, "--max-hooks", help="Máximo de hooks a detectar"),
    burn_captions: bool = typer.Option(True, "--burn-captions/--no-burn-captions", help="Camada 2: queima legenda no vídeo (SRT burn-in)"),
    remove_silence: bool = typer.Option(False, "--remove-silence/--no-remove-silence", help="Camada 2: corta silêncios do áudio"),
) -> None:
    """Processa um vídeo longo e entrega clipes cortados numa pasta."""
    if not arquivo.exists():
        typer.echo(f"ERRO: arquivo não encontrado: {arquivo}", err=True)
        raise typer.Exit(1)

    if arquivo.suffix.lower() not in {".mp4", ".mov", ".avi"}:
        typer.echo(f"ERRO: formato não suportado '{arquivo.suffix}'. Use .mp4, .mov ou .avi", err=True)
        raise typer.Exit(1)

    mode = "DRY-RUN (simulação)" if dry_run else "REAL (Whisper + FFmpeg)"
    typer.echo(f"\n{'='*60}")
    typer.echo(f"  AGÊNCIA DE VÍDEO OMNIS — Camada 1+2 (cortes + acabamento)")
    typer.echo(f"{'='*60}")
    typer.echo(f"  vídeo:   {arquivo}")
    typer.echo(f"  perfil:  {perfil}")
    typer.echo(f"  preset:  {preset}")
    typer.echo(f"  modo:    {mode}")
    typer.echo(f"  clips:   máx {max_clips} × {target_duration}s")
    typer.echo(f"  legenda: {'queimada (burn-in)' if burn_captions else 'desligada'}")
    typer.echo(f"  silêncio:{'corte ligado' if remove_silence else ' mantido'}")
    typer.echo(f"{'='*60}\n")

    pipeline = AgenciaPipeline(
        dry_run=dry_run,
        max_hooks=max_hooks,
        burn_captions=burn_captions,
        remove_silence=remove_silence,
    )

    result = pipeline.run(
        video_path=arquivo,
        perfil=perfil,
        preset_name=preset,
        target_duration=target_duration,
        max_clips=max_clips,
    )

    typer.echo(result.summary())
    typer.echo(f"\n{'='*60}")

    if result.error:
        typer.echo(f"FALHOU: {result.error}", err=True)
        raise typer.Exit(1)

    if not result.clips:
        typer.echo("Nenhum clipe gerado — vídeo pode ser muito curto ou sem hooks detectados.")
        raise typer.Exit(0)

    typer.echo(f"\nEntregáveis em: {result.output_dir}")
    typer.echo("Lucas, revisa os clipes e sobe o que aprovar. Nada foi publicado.\n")


if __name__ == "__main__":
    app()

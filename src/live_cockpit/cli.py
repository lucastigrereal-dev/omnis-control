"""P24 Live Cockpit Supreme — CLI."""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Optional

from src.live_cockpit.collector import CockpitCollector
from src.live_cockpit.renderer import CockpitRenderer


def _collect_snapshot(dry_run: bool = True) -> dict:
    collector = CockpitCollector(dry_run=dry_run)
    return collector.collect_all()


def cmd_show(args: argparse.Namespace) -> int:
    """Exibe o cockpit completo."""
    snapshot = _collect_snapshot(dry_run=args.dry_run)
    renderer = CockpitRenderer(width=args.width)
    print(renderer.render(snapshot))
    return 0


def cmd_compact(args: argparse.Namespace) -> int:
    """Versao compacta do cockpit."""
    snapshot = _collect_snapshot(dry_run=args.dry_run)
    renderer = CockpitRenderer()
    print(renderer.render_compact(snapshot))
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Exporta snapshot para arquivo."""
    snapshot = _collect_snapshot(dry_run=args.dry_run)
    renderer = CockpitRenderer()

    if args.format == "json":
        content = renderer.render_json(snapshot)
        ext = ".json"
    else:
        content = renderer.render_markdown(snapshot)
        ext = ".md"

    output_file = args.output or f"cockpit_{snapshot.snapshot_id}{ext}"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Exported to {output_file}")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    """Modo watch: atualiza cockpit periodicamente."""
    interval = args.interval
    renderer = CockpitRenderer(width=args.width)
    try:
        while True:
            snapshot = _collect_snapshot(dry_run=args.dry_run)
            print("\033[2J\033[H")  # clear screen
            print(renderer.render(snapshot))
            print(f"\nRefreshing every {interval}s. Ctrl+C to exit.")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nWatch mode stopped.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cockpit",
        description="P24 Live Cockpit Supreme — OMNIS control panel",
    )
    sub = parser.add_subparsers(dest="command")

    # show — cockpit completo
    p_show = sub.add_parser("show", help="Display full cockpit")
    p_show.add_argument("--dry-run", action="store_true", default=True)
    p_show.add_argument("--no-dry-run", action="store_false", dest="dry_run")
    p_show.add_argument("--width", type=int, default=80, help="Terminal width")

    # compact — versão 1 tela
    p_compact = sub.add_parser("compact", help="Display compact cockpit (1 screen)")
    p_compact.add_argument("--dry-run", action="store_true", default=True)
    p_compact.add_argument("--no-dry-run", action="store_false", dest="dry_run")

    # export — salva em arquivo
    p_export = sub.add_parser("export", help="Export snapshot to file")
    p_export.add_argument("--format", choices=["json", "markdown"], default="json")
    p_export.add_argument("--dry-run", action="store_true", default=True)
    p_export.add_argument("--no-dry-run", action="store_false", dest="dry_run")
    p_export.add_argument("-o", "--output", help="Output file path")

    # watch — atualização contínua
    p_watch = sub.add_parser("watch", help="Watch mode — auto-refresh")
    p_watch.add_argument("--interval", type=int, default=60, help="Refresh interval in seconds")
    p_watch.add_argument("--dry-run", action="store_true", default=True)
    p_watch.add_argument("--no-dry-run", action="store_false", dest="dry_run")
    p_watch.add_argument("--width", type=int, default=80, help="Terminal width")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    if args.command == "show":
        return cmd_show(args)
    elif args.command == "compact":
        return cmd_compact(args)
    elif args.command == "export":
        return cmd_export(args)
    elif args.command == "watch":
        return cmd_watch(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

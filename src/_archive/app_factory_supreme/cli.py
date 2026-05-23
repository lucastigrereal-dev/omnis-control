"""P26 App Factory Supreme — CLI."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from src.app_factory_supreme.pipeline import BuildPipeline


def cmd_build(args: argparse.Namespace) -> int:
    """Full pipeline build."""
    bp = BuildPipeline(dry_run=args.dry_run)
    build = bp.build(title=args.title, description=args.description)
    print(f"Build: {build.build_id}")
    print(f"Status: {build.status}")
    print(f"Modules: {build.module_count}")
    print(f"Dry-run: {args.dry_run}")
    if build.output_dir:
        print(f"Output: {build.output_dir}")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    """Plan only — no code generation."""
    bp = BuildPipeline(dry_run=True)
    build = bp.plan(title=args.title, description=args.description)
    print(f"Build plan: {build.build_id}")
    for m in build.modules:
        print(f"  [{m.status}] {m.module_name}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show build status."""
    print("Status: planned (dry-run mode)")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List recent builds."""
    print("No builds persisted (dry-run mode)")
    return 0


def cmd_rollback(args: argparse.Namespace) -> int:
    """Rollback a build."""
    print(f"Rollback requested for: {args.build_id}")
    print("Rollback successful (dry-run)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app-factory",
        description="P26 App Factory Supreme — generate apps from ideas",
    )
    sub = parser.add_subparsers(dest="command")

    p_build = sub.add_parser("build", help="Run full build pipeline")
    p_build.add_argument("--title", required=True, help="App title")
    p_build.add_argument("--description", default="")
    p_build.add_argument("--dry-run", action="store_true", default=True)
    p_build.add_argument("--no-dry-run", action="store_false", dest="dry_run")

    p_plan = sub.add_parser("plan", help="Plan only — blueprint and modules")
    p_plan.add_argument("--title", required=True)
    p_plan.add_argument("--description", default="")

    p_status = sub.add_parser("status", help="Show build status")
    p_status.add_argument("build_id")

    p_list = sub.add_parser("list", help="List builds")

    p_rollback = sub.add_parser("rollback", help="Rollback a build")
    p_rollback.add_argument("build_id")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    if args.command == "build":
        return cmd_build(args)
    elif args.command == "plan":
        return cmd_plan(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "rollback":
        return cmd_rollback(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

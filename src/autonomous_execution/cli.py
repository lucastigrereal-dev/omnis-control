"""P23 Autonomous Execution — CLI."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from src.autonomous_execution.executor import AutonomousExecutor
from src.autonomous_execution.models import AutonomousConfig, AutonomousResult, AutonomousState
from src.omnis_supreme.models import SupremePlan, SupremeStep


def _load_plan(plan_file: str) -> SupremePlan:
    """Carrega plano de arquivo JSON."""
    with open(plan_file, "r") as f:
        data = json.load(f)
    return SupremePlan.from_dict(data)


def _print_result(result: AutonomousResult) -> None:
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


def cmd_run(args: argparse.Namespace) -> int:
    """Executa plano autonomamente."""
    plan = _load_plan(args.plan_file)
    cfg = AutonomousConfig.new(dry_run=args.dry_run)
    executor = AutonomousExecutor(cfg)

    result = executor.execute(plan)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    _print_result(result)
    return 0 if result.status == AutonomousState.COMPLETED.value else 1


def cmd_resume(args: argparse.Namespace) -> int:
    """Retoma execucao pausada."""
    with open(args.result_file, "r") as f:
        data = json.load(f)
    result = AutonomousResult.from_dict(data)

    plan = _load_plan(args.plan_file)
    cfg = AutonomousConfig.new(dry_run=args.dry_run)
    executor = AutonomousExecutor(cfg)

    result2 = executor.execute_remaining(result, plan, ctx={})

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result2.to_dict(), f, indent=2, ensure_ascii=False)

    _print_result(result2)
    return 0 if result2.status == AutonomousState.COMPLETED.value else 1


def cmd_status(args: argparse.Namespace) -> int:
    """Exibe status de execucao autonoma."""
    with open(args.result_file, "r") as f:
        data = json.load(f)
    result = AutonomousResult.from_dict(data)
    _print_result(result)
    return 0


def cmd_cancel(args: argparse.Namespace) -> int:
    """Cancela execucao autonoma."""
    with open(args.result_file, "r") as f:
        data = json.load(f)
    result = AutonomousResult.from_dict(data)

    cfg = AutonomousConfig.new()
    executor = AutonomousExecutor(cfg)
    executor.cancel(result)

    _print_result(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autonomous",
        description="P23 Autonomous Execution — supervised autonomous mission runner",
    )
    sub = parser.add_subparsers(dest="command")

    # run
    p_run = sub.add_parser("run", help="Execute plan autonomously")
    p_run.add_argument("plan_file", help="JSON file with SupremePlan")
    p_run.add_argument("--dry-run", action="store_true", default=True, help="Dry-run mode (default)")
    p_run.add_argument("--no-dry-run", action="store_false", dest="dry_run", help="Real execution")
    p_run.add_argument("-o", "--output", help="Output JSON file for result")

    # resume
    p_resume = sub.add_parser("resume", help="Resume paused autonomous execution")
    p_resume.add_argument("result_file", help="JSON file with AutonomousResult")
    p_resume.add_argument("plan_file", help="JSON file with original SupremePlan")
    p_resume.add_argument("--dry-run", action="store_true", default=True)
    p_resume.add_argument("--no-dry-run", action="store_false", dest="dry_run")
    p_resume.add_argument("-o", "--output", help="Output JSON file for result")

    # status
    p_status = sub.add_parser("status", help="Display autonomous execution status")
    p_status.add_argument("result_file", help="JSON file with AutonomousResult")

    # cancel
    p_cancel = sub.add_parser("cancel", help="Cancel autonomous execution")
    p_cancel.add_argument("result_file", help="JSON file with AutonomousResult")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    if args.command == "run":
        return cmd_run(args)
    elif args.command == "resume":
        return cmd_resume(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "cancel":
        return cmd_cancel(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

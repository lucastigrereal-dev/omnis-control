"""P27 Real World Actions CLI — action management and execution."""
import argparse
import json
import sys
from typing import Optional

from src.real_world_actions.registry import ActionRegistry
from src.real_world_actions.executor import ActionExecutor
from src.real_world_actions.models import ActionRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omnis-action",
        description="P27 Real World Actions — execute and manage external actions",
    )
    sub = parser.add_subparsers(dest="command")

    # list
    list_p = sub.add_parser("list", help="List available actions")
    list_p.add_argument("--provider", default="", help="Filter by provider")
    list_p.add_argument("--risk", default="", help="Filter by risk level")
    list_p.add_argument("--type", default="", help="Filter by action type")

    # preview
    preview_p = sub.add_parser("preview", help="Dry-run preview of an action")
    preview_p.add_argument("action", help="Action name (e.g. send_email)")
    preview_p.add_argument("--params", default="{}", help="JSON params for the action")

    # execute
    exec_p = sub.add_parser("execute", help="Execute an action")
    exec_p.add_argument("action", help="Action name (e.g. send_email)")
    exec_p.add_argument("--params", default="{}", help="JSON params for the action")
    exec_p.add_argument("--no-dry-run", action="store_true", help="Actually execute (default: dry-run)")

    # approve
    approve_p = sub.add_parser("approve", help="Approve a pending action")
    approve_p.add_argument("request_id", help="Request ID to approve")
    approve_p.add_argument("--by", default="operator", help="Who is approving")
    approve_p.add_argument("--reason", default="", help="Reason for approval")

    # deny
    deny_p = sub.add_parser("deny", help="Deny a pending action")
    deny_p.add_argument("request_id", help="Request ID to deny")
    deny_p.add_argument("--reason", default="", help="Reason for denial")

    # history
    hist_p = sub.add_parser("history", help="Show action execution history")
    hist_p.add_argument("--limit", type=int, default=20, help="Max entries")

    # providers
    sub.add_parser("providers", help="List available providers")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.command:
        parser.print_help()
        return 1

    registry = ActionRegistry()
    registry.seed_defaults()
    executor = ActionExecutor(dry_run=True, registry=registry)

    if args.command == "list":
        actions = registry.list_all()
        if args.provider:
            actions = [a for a in actions if a.provider == args.provider]
        if args.risk:
            actions = [a for a in actions if a.risk_level == args.risk]
        if args.type:
            actions = [a for a in actions if a.action_type == args.type]
        for a in actions:
            print(f"  {a.action_id}  {a.name:<30} provider={a.provider:<12} type={a.action_type:<10} risk={a.risk_level:<10} approval={'yes' if a.requires_approval else 'no'}")
        print(f"\n{len(actions)} actions listed.")
        return 0

    if args.command == "preview":
        action = registry.find(args.action)
        params = json.loads(args.params) if isinstance(args.params, str) else args.params
        req = ActionRequest.new(action.action_id, params=params, dry_run=True)
        result = executor.execute(req)
        print(json.dumps(result.output, indent=2, ensure_ascii=False))
        return 0

    if args.command == "execute":
        action = registry.find(args.action)
        params = json.loads(args.params) if isinstance(args.params, str) else args.params
        dry_run = not args.no_dry_run
        req = ActionRequest.new(action.action_id, params=params, dry_run=dry_run)
        result = executor.execute(req)
        print(json.dumps({"status": result.status, "output": result.output, "error": result.error}, indent=2, ensure_ascii=False))
        return 0 if result.status in ("success", "dry_run") else 1

    if args.command == "approve":
        decision = executor.approval.approve(args.request_id, approved_by=getattr(args, 'by', 'operator'), reason=args.reason)
        print(f"Approved: {decision.decision_id} — {decision.verdict}")
        return 0

    if args.command == "deny":
        decision = executor.approval.deny(args.request_id, reason=args.reason)
        print(f"Denied: {decision.decision_id} — {decision.verdict}")
        return 0

    if args.command == "history":
        results = executor.get_results()
        for r in results[-args.limit:]:
            print(f"  {r.result_id}  {r.status:<15} {r.error}")
        print(f"\n{len(results)} total, showing last {min(args.limit, len(results))}")
        return 0

    if args.command == "providers":
        for p in registry.provider_names():
            adapter_info = "registered" if p in ["gmail", "instagram", "webhook", "github", "n8n", "slack", "mock"] else "no adapter"
            print(f"  {p:<15} {adapter_info}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

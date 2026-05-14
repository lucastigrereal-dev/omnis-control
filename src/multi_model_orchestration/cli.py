"""P25 Multi-Model Orchestration — CLI."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from src.multi_model_orchestration.classifier import TaskClassifier
from src.multi_model_orchestration.cost_tracker import CostTracker
from src.multi_model_orchestration.registry import ModelRegistry
from src.multi_model_orchestration.router import ModelRouter


def cmd_models(args: argparse.Namespace) -> int:
    """List registered models."""
    registry = ModelRegistry()
    registry.seed_defaults()

    models = registry.list_enabled() if args.active else registry.list_all()
    for m in models:
        status = "✓" if m.enabled else "✗"
        print(f"  [{status}] {m.name} ({m.provider}) — ${m.cost_per_1k_tokens}/1k tokens, {m.avg_latency_ms}ms")
    print(f"\n{registry.enabled_count}/{registry.count} models enabled")
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    """Simulate routing for a task (dry-run)."""
    registry = ModelRegistry()
    registry.seed_defaults()
    router = ModelRouter(registry=registry, dry_run=True)

    dec = router.select_model(args.task, risk_level=args.risk)
    print(f"Task: {args.task}")
    print(f"Selected: {dec.selected_model.name} ({dec.selected_model.provider})")
    print(f"Strategy: {dec.strategy}")
    print(f"Reason: {dec.reason}")
    print(f"Estimated cost: ${dec.estimated_cost_usd:.6f}")
    print(f"Fallback chain: {dec.fallback_chain}")
    return 0


def cmd_cost(args: argparse.Namespace) -> int:
    """Show cost report."""
    tracker = CostTracker(daily_limit_usd=args.limit)
    print(json.dumps(tracker.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_classify(args: argparse.Namespace) -> int:
    """Classify a task intent."""
    classifier = TaskClassifier()
    tc = classifier.classify(args.intent, risk_level=args.risk)
    print(f"Intent: {tc.task_type}")
    print(f"Complexity: {tc.complexity}")
    print(f"Risk: {tc.risk_level}")
    print(f"Capabilities: {tc.min_capabilities}")
    print(f"Creative: {tc.requires_creativity}, Precision: {tc.requires_precision}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multi-model",
        description="P25 Multi-Model Orchestration — model routing CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # models
    p_models = sub.add_parser("models", help="List registered models")
    p_models.add_argument("--active", action="store_true", default=True)

    # route
    p_route = sub.add_parser("route", help="Simulate routing for a task")
    p_route.add_argument("task", help="Task type (e.g., classify_intent, generate_code)")
    p_route.add_argument("--risk", default="low", help="Risk level")

    # cost
    p_cost = sub.add_parser("cost", help="Show cost report")
    p_cost.add_argument("--limit", type=float, default=5.0, help="Daily limit in USD")

    # classify
    p_classify = sub.add_parser("classify", help="Classify a task intent")
    p_classify.add_argument("intent", help="Intent to classify")
    p_classify.add_argument("--risk", default="low")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    if args.command == "models":
        return cmd_models(args)
    elif args.command == "route":
        return cmd_route(args)
    elif args.command == "cost":
        return cmd_cost(args)
    elif args.command == "classify":
        return cmd_classify(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

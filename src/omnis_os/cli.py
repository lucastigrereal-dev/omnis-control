"""P29 OMNIS OS CLI — bootstrap, status, health, events."""
import argparse
import json
import sys
from typing import Optional

from src.omnis_os.kernel import OmnisKernel
from src.omnis_os.models import KernelConfig, ModuleInfo
from src.omnis_os.errors import ModuleNotFoundError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omnis-os",
        description="P29 OMNIS OS Layer — unified module operating system",
    )
    sub = parser.add_subparsers(dest="command")

    # bootstrap
    boot_p = sub.add_parser("bootstrap", help="Bootstrap the OMNIS OS")
    boot_p.add_argument("--dry-run", action="store_true", default=True,
                        help="Dry run only (default: True)")

    # status
    sub.add_parser("status", help="Show kernel status")

    # health
    health_p = sub.add_parser("health", help="Run health checks")
    health_p.add_argument("--module", default="", help="Check specific module")

    # events
    events_p = sub.add_parser("events", help="List recent events")
    events_p.add_argument("--type", default="", help="Filter by event type")
    events_p.add_argument("--limit", type=int, default=20, help="Max events")

    # modules
    modules_p = sub.add_parser("modules", help="List registered modules")
    modules_p.add_argument("--namespace", default="", help="Filter by namespace")
    modules_p.add_argument("--legacy", action="store_true", help="Only legacy modules")

    # shutdown
    sub.add_parser("shutdown", help="Shutdown the kernel")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.command:
        parser.print_help()
        return 1

    kernel = OmnisKernel(dry_run=True)

    if args.command == "bootstrap":
        result = kernel.bootstrap()
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.status in ("dry_run", "ready") else 1

    if args.command == "status":
        status = kernel.status()
        print(json.dumps(status, indent=2))
        return 0

    if args.command == "health":
        if args.module:
            try:
                result = kernel.health_monitor.check_module(args.module)
                print(json.dumps(result.to_dict(), indent=2))
            except ModuleNotFoundError as e:
                print(json.dumps({"error": str(e)}))
                return 1
        else:
            results = kernel.health_monitor.check_all()
            agg = kernel.health_monitor.aggregate_status()
            print(f"Overall: {agg['overall']}")
            for name, h in results.items():
                print(f"  {name}: {h.status}")
        return 0

    if args.command == "events":
        events = kernel.event_bus.history(event_type=args.type, limit=args.limit)
        for e in events:
            print(f"  [{e.event_type}] {e.source_module} — {e.timestamp}")
        print(f"\n{len(events)} events.")
        return 0

    if args.command == "modules":
        if args.legacy:
            mods = kernel.registry.list_legacy()
        elif args.namespace:
            mods = kernel.registry.list_by_namespace(args.namespace)
        else:
            mods = kernel.registry.list_all()
        for m in mods:
            legacy_tag = " [LEGACY]" if m.is_legacy else ""
            print(f"  {m.name} ({m.version}) [{m.status}]{legacy_tag}")
        print(f"\n{len(mods)} modules.")
        return 0

    if args.command == "shutdown":
        result = kernel.shutdown()
        print(json.dumps(result, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

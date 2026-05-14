"""P22 Capability Forge Real CLI — build, status, rollback commands."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.capability_forge_lite.store import ProposalStore
from src.capability_forge_lite import store as store_mod
from src.capability_forge_real.builder import CapabilityBuilder
from src.capability_forge_real.models import BuildResult


def cmd_build(args) -> int:
    """Build code for an approved proposal."""
    store = ProposalStore(store_mod.DEFAULT_PROPOSALS_LOG)
    proposal = store.get(args.proposal_id)
    if proposal is None:
        print(f"Proposal {args.proposal_id} not found", file=sys.stderr)
        return 1

    builder = CapabilityBuilder(dry_run=args.dry_run)
    try:
        result = builder.build(proposal)
        if result.is_success:
            print(f"Build {result.build_id}: DONE — {result.capability_name}")
            print(f"  Files: {result.files_created}")
            print(f"  Tests: {result.test_count}")
            print(f"  Policy: {'PASS' if result.policy_scan['passed'] else 'FAIL'}")
        else:
            print(f"Build {result.build_id}: FAILED ({result.state})", file=sys.stderr)
            if result.policy_scan.get("violations"):
                for v in result.policy_scan["violations"]:
                    print(f"  Policy violation: {v['description']}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Build error: {e}", file=sys.stderr)
        return 1

    return 0


def cmd_status(args) -> int:
    """Check build status (stub — BuildResult is ephemeral)."""
    print(f"Build {args.build_id}: status tracking is ephemeral")
    print("BuildResults are not persisted. Re-run build to see current state.")
    return 0


def cmd_rollback(args) -> int:
    """Remove files from a failed build."""
    builder = CapabilityBuilder(dry_run=False)
    try:
        builder.rollback_files(args.files)
        print(f"Rollback: removed {len(args.files)} file(s)")
    except Exception as e:
        print(f"Rollback error: {e}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="forge-real")
    sub = parser.add_subparsers(dest="command")

    # build
    build_p = sub.add_parser("build", help="Build skill from approved proposal")
    build_p.add_argument("proposal_id")
    build_p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    build_p.add_argument("--no-dry-run", dest="dry_run", action="store_false")

    # status
    status_p = sub.add_parser("status", help="Check build status")
    status_p.add_argument("build_id")

    # rollback
    rollback_p = sub.add_parser("rollback", help="Rollback files")
    rollback_p.add_argument("files", nargs="+")

    args = parser.parse_args()
    if args.command == "build":
        return cmd_build(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "rollback":
        return cmd_rollback(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

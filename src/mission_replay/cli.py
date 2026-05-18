"""CLI for mission replay."""

from __future__ import annotations

import argparse
import sys

from .replay import MissionReplay


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omnis-mission-replay",
        description="Reopen, replay, and compare missions.",
    )

    sub = parser.add_subparsers(dest="command", help="Subcommands")

    # list
    list_cmd = sub.add_parser("list", help="List available missions")
    list_cmd.add_argument("--replays", action="store_true", help="List replays instead of missions")

    # info
    info_cmd = sub.add_parser("info", help="Show mission snapshot")
    info_cmd.add_argument("mission_id", help="Mission ID (e.g. MIS-20260518-002)")

    # replay
    replay_cmd = sub.add_parser("replay", help="Replay a mission with variant")
    replay_cmd.add_argument("mission_id", help="Original mission ID")
    replay_cmd.add_argument("variant", help="Variant name (e.g. Brotas, v2)")
    replay_cmd.add_argument("--change", "-c", nargs=2, action="append",
                            metavar=("KEY", "VALUE"),
                            help="Override parameter (repeatable)")
    replay_cmd.add_argument("--execute", action="store_true",
                            help="Actually copy files (default: dry-run)")

    # diff
    diff_cmd = sub.add_parser("diff", help="Compare original vs replay")
    diff_cmd.add_argument("session_id", help="Replay session ID")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    replay = MissionReplay()

    if args.command == "list":
        if args.replays:
            sessions = replay.list_sessions()
            if not sessions:
                print("No replay sessions found.")
            for s in sessions:
                print(f"  {s.session_id} — {s.status}")
        else:
            missions = replay.list_missions()
            print(f"Missions available: {len(missions)}")
            for m in missions:
                print(f"  {m}")
        return 0

    elif args.command == "info":
        try:
            snap = replay.snapshot(args.mission_id)
            print(f"Mission: {snap['mission_id']}")
            print(f"Contract: {snap['contract']}")
            print(f"Files: {len(snap['files'])}")
            for f in snap["files"][:10]:
                print(f"  {f['path']} ({f['size']} bytes)")
            if len(snap["files"]) > 10:
                print(f"  ... and {len(snap['files']) - 10} more")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1
        return 0

    elif args.command == "replay":
        changes = {}
        if args.change:
            for k, v in args.change:
                changes[k] = v

        try:
            session = replay.create_replay(
                mission_id=args.mission_id,
                variant_name=args.variant,
                variant_changes=changes,
                dry_run=not args.execute,
            )
            print(f"Replay session: {session.session_id}")
            print(f"Status: {session.status}")
            print(f"Variant: {session.variant_name}")
            if changes:
                print(f"Changes: {changes}")
            if session.replay_path:
                print(f"Path: {session.replay_path}")
                print(f"Outputs: {session.output_count} files")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1
        return 0

    elif args.command == "diff":
        try:
            report = replay.diff(args.session_id)
            print(f"Diff: {report.original_mission_id} vs {report.variant_name}")
            print(f"Total: {report.total_files} files")
            print(f"  Added: {report.files_added}")
            print(f"  Removed: {report.files_removed}")
            print(f"  Modified: {report.files_modified}")
            print(f"  Unchanged: {report.files_unchanged}")
            if report.files_modified:
                print("\nModified files:")
                for e in report.entries:
                    if e.change_type == "modified":
                        print(f"  {e.file_path}: {e.summary}")
            if report.files_added:
                print("\nAdded files:")
                for e in report.entries:
                    if e.change_type == "added":
                        print(f"  + {e.file_path}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

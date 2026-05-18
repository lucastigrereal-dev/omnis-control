"""CLI for Backlog Manager."""

import argparse

from .models import ItemStatus, ItemType
from .queue import BacklogManager


def main():
    parser = argparse.ArgumentParser(description="OMNIS Local Backlog")
    sub = parser.add_subparsers(dest="command")

    add = sub.add_parser("add", help="Enqueue item")
    add.add_argument("--type", required=True, choices=[t.value for t in ItemType])
    add.add_argument("--title", required=True)
    add.add_argument("--description", default="")
    add.add_argument("--priority", type=int, default=3)
    add.add_argument("--tags", nargs="*", default=[])

    sub.add_parser("next", help="Dequeue highest-priority pending item")
    sub.add_parser("list", help="List all items")

    ls = sub.add_parser("ls", help="List by status")
    ls.add_argument("--status", choices=[s.value for s in ItemStatus])

    done = sub.add_parser("done", help="Mark item completed")
    done.add_argument("item_id")

    cancel = sub.add_parser("cancel", help="Cancel item")
    cancel.add_argument("item_id")

    block = sub.add_parser("block", help="Block item")
    block.add_argument("item_id")
    block.add_argument("--reason", default="")

    unblock = sub.add_parser("unblock", help="Unblock item")
    unblock.add_argument("item_id")

    pri = sub.add_parser("pri", help="Reprioritize item")
    pri.add_argument("item_id")
    pri.add_argument("priority", type=int)

    sub.add_parser("count", help="Show counts by status")

    args = parser.parse_args()
    mgr = BacklogManager()

    if args.command == "add":
        item = mgr.enqueue(
            ItemType(args.type), args.title, args.description,
            args.priority, args.tags,
        )
        print(f"Enqueued: {item.item_id} — {item.title}")

    elif args.command == "next":
        item = mgr.dequeue()
        if item:
            print(f"Dequeued: {item.item_id} — {item.title} [{item.item_type.value}]")
        else:
            print("No pending items.")

    elif args.command in ("list", "ls"):
        status = ItemStatus(args.status) if getattr(args, 'status', None) else None
        items = mgr.list_by_status(status)
        if not items:
            print("No items.")
        for i in items:
            print(f"[{i.item_id}] {i.status.value:12} p{i.priority} {i.item_type.value:10} {i.title}")

    elif args.command == "done":
        mgr.complete(args.item_id)
        print(f"Completed: {args.item_id}")

    elif args.command == "cancel":
        mgr.cancel(args.item_id)
        print(f"Cancelled: {args.item_id}")

    elif args.command == "block":
        mgr.block(args.item_id, args.reason)
        print(f"Blocked: {args.item_id}")

    elif args.command == "unblock":
        mgr.unblock(args.item_id)
        print(f"Unblocked: {args.item_id}")

    elif args.command == "pri":
        mgr.prioritize(args.item_id, args.priority)
        print(f"Prioritized: {args.item_id} → p{args.priority}")

    elif args.command == "count":
        c = mgr.count()
        for k, v in c.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()

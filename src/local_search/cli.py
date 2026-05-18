"""CLI for local search engine."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .engine import SearchEngine
from .models import SearchQuery, SourceType

SOURCE_ALIASES = {
    "mission": SourceType.MISSION,
    "template": SourceType.TEMPLATE,
    "skill": SourceType.SKILL,
    "log": SourceType.LOG,
    "report": SourceType.REPORT,
    "doc": SourceType.DOC,
    "script": SourceType.SCRIPT,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omnis-local-search",
        description="Search local OMNIS content: missions, templates, skills, logs, and reports.",
    )
    parser.add_argument(
        "query", nargs="+", help="Search query terms"
    )
    parser.add_argument(
        "--source", "-s", choices=list(SOURCE_ALIASES), action="append",
        help="Filter by source type (repeatable)",
    )
    parser.add_argument(
        "--limit", "-n", type=int, default=20, help="Max results (default: 20)"
    )
    parser.add_argument(
        "--reindex", action="store_true", help="Force full reindex before search"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show index statistics"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    engine = SearchEngine()
    engine.index_all()

    if args.stats:
        s = engine.stats()
        print(f"Index: {s['indexed_items']} items, {s['unique_terms']} terms")
        print("By type:", s["by_source_type"])
        if not args.query:
            return 0

    query_str = " ".join(args.query)
    source_types = None
    if args.source:
        source_types = [SOURCE_ALIASES[s] for s in args.source]

    sq = SearchQuery(
        query=query_str,
        source_types=source_types or [],
        max_results=args.limit,
    )
    results = engine.search(sq)

    if not results:
        print(f"No results for: {query_str}")
        return 0

    print(f"\nResults for: '{query_str}' ({len(results)} found)\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r.source_type.value.upper()}] {r.title}")
        print(f"   Score: {r.score:.1f}  Path: {r.source_path}")
        if r.tags:
            print(f"   Tags: {', '.join(r.tags[:5])}")
        snippet = r.snippet[:120].replace("\n", " ")
        print(f"   {snippet}...")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

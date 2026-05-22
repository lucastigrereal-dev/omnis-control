"""CLI script: batch caption generation via CaptionFactory."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.skills.caption_factory import BatchCaptionRequest, CaptionFactory


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OMNIS CaptionFactory — batch Instagram caption generation",
    )
    parser.add_argument(
        "--topic", "-t",
        required=True,
        help="Topic for caption generation (e.g. 'hotéis fazenda interior SP')",
    )
    parser.add_argument(
        "--page", "-p",
        default="@lucastigrereal",
        help="Instagram handle (default: @lucastigrereal)",
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=3,
        help="Number of caption variations (default: 3)",
    )
    parser.add_argument(
        "--tones",
        default="autêntico e caloroso,informativo e educativo,urgente e persuasivo",
        help="Comma-separated tones (default: autêntico,informativo,urgente)",
    )
    parser.add_argument(
        "--formats",
        default="carrossel,reel,feed",
        help="Comma-separated formats (default: carrossel,reel,feed)",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=150,
        help="Max words per caption (default: 150)",
    )
    parser.add_argument(
        "--output", "-o",
        default="exports/captions/batch",
        help="Output directory (default: exports/captions/batch)",
    )
    parser.add_argument(
        "--dry-run/--real",
        default=True,
        help="Dry run (simulation) or real LLM call (default: dry-run)",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=4,
        help="Max parallel workers (default: 4)",
    )

    args = parser.parse_args()

    request = BatchCaptionRequest(
        topic=args.topic,
        page=args.page,
        count=args.count,
        tones=[t.strip() for t in args.tones.split(",")],
        formats=[f.strip() for f in args.formats.split(",")],
        max_words=args.max_words,
    )

    print(f"OMNIS CaptionFactory")
    print(f"  Topic: {args.topic}")
    print(f"  Page: {args.page}")
    print(f"  Count: {args.count} variations")
    print(f"  Tones: {request.tones}")
    print(f"  Formats: {request.formats}")
    print(f"  Mode: {'DRY_RUN' if args.dry_run else 'REAL (Ollama)'}")
    print(f"  Output: {args.output}")
    print()

    factory = CaptionFactory(dry_run=args.dry_run, max_workers=args.workers)

    if args.dry_run:
        print("[DRY RUN] Simulating batch caption generation...")
        result = factory.produce_batch(request)
    else:
        print("[REAL] Calling Ollama via ModelRouter...")
        result = factory.produce_and_save(request, args.output)

    print(f"\nDone! {result.success_count} captions, {result.error_count} errors")
    print(f"Total time: {result.total_time_ms}ms")

    for i, caption in enumerate(result.captions):
        print(f"\n--- Caption {i+1} [{caption.model_used}] ---")
        print(caption.caption[:200])
        if len(caption.caption) > 200:
            print("...")

    if result.errors:
        print(f"\nERRORS:")
        for e in result.errors:
            print(f"  [{e['index']}] {e['error']}")

    if not args.dry_run:
        print(f"\nFiles saved to: {args.output}/")

    return 0 if result.error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

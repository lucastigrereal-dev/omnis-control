"""P28 Self-Improvement CLI — analyze, propose, execute, measure."""
import argparse
import json
import sys
from typing import Optional

from src.self_improvement.collector import FeedbackCollector
from src.self_improvement.analyzer import PatternAnalyzer
from src.self_improvement.prioritizer import GapPrioritizer
from src.self_improvement.proposer import ImprovementProposer
from src.self_improvement.executor import ImprovementExecutor
from src.self_improvement.measurer import ImpactMeasurer
from src.self_improvement.models import PROPOSAL_APPROVED


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omnis-improve",
        description="P28 Self-Improvement Loop — analyze, propose, and apply improvements",
    )
    sub = parser.add_subparsers(dest="command")

    # analyze
    sub.add_parser("analyze", help="Analyze feedback and detect patterns")

    # gaps
    gaps_p = sub.add_parser("gaps", help="List prioritized gaps")
    gaps_p.add_argument("--top", type=int, default=10, help="Show top N gaps")

    # propose
    propose_p = sub.add_parser("propose", help="Generate improvement proposals")
    propose_p.add_argument("--gap-id", default="", help="Specific gap to propose for")

    # list
    list_p = sub.add_parser("list", help="List proposals")
    list_p.add_argument("--status", default="", help="Filter by status")

    # approve
    approve_p = sub.add_parser("approve", help="Approve a proposal")
    approve_p.add_argument("proposal_id", help="Proposal ID")
    approve_p.add_argument("--by", default="operator", help="Who is approving")

    # reject
    reject_p = sub.add_parser("reject", help="Reject a proposal")
    reject_p.add_argument("proposal_id", help="Proposal ID")
    reject_p.add_argument("--reason", default="", help="Reason for rejection")

    # execute
    exec_p = sub.add_parser("execute", help="Execute a proposal")
    exec_p.add_argument("proposal_id", help="Proposal ID")
    exec_p.add_argument("--dry-run", action="store_true", default=True, help="Dry run only")

    # measure
    measure_p = sub.add_parser("measure", help="Measure proposal impact")
    measure_p.add_argument("proposal_id", help="Proposal ID")

    # status
    sub.add_parser("status", help="Show loop status")

    # history
    hist_p = sub.add_parser("history", help="Show improvement history")
    hist_p.add_argument("--limit", type=int, default=20, help="Max entries")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.command:
        parser.print_help()
        return 1

    collector = FeedbackCollector(dry_run=True)
    analyzer = PatternAnalyzer(dry_run=True)
    prioritizer = GapPrioritizer()
    proposer = ImprovementProposer(dry_run=True)
    executor = ImprovementExecutor(dry_run=True)
    measurer = ImpactMeasurer(dry_run=True)

    if args.command == "analyze":
        feedbacks = collector.collect_all()
        print(f"Collected {len(feedbacks)} feedback entries.")
        patterns = analyzer.analyze(feedbacks)
        print(f"Detected {len(patterns)} patterns:")
        for p in patterns:
            print(f"  [{p.category}] {p.name} (x{p.occurrences}, confidence={p.confidence:.2f})")
        return 0

    if args.command == "gaps":
        feedbacks = collector.collect_all()
        patterns = analyzer.analyze(feedbacks)
        gaps = prioritizer.prioritize(patterns)
        for g in gaps[:args.top]:
            print(f"  #{g.rank} [{g.urgency}] {g.pattern.name} — score={g.score:.1f}")
        return 0

    if args.command == "propose":
        feedbacks = collector.collect_all()
        patterns = analyzer.analyze(feedbacks)
        gaps = prioritizer.prioritize(patterns)
        proposals = proposer.propose(gaps)
        for p in proposals:
            print(f"  {p.proposal_id}  {p.title}")
            print(f"    type={p.implementation_type}  auto={p.auto_implementable}  severity={p.severity}")
        return 0

    if args.command == "list":
        proposals = proposer.get_proposals()
        if args.status:
            proposals = [p for p in proposals if p.status == args.status]
        for p in proposals:
            print(f"  {p.proposal_id}  {p.status:<15} {p.title}")
        print(f"\n{len(proposals)} proposals.")
        return 0

    if args.command == "approve":
        # Simulate finding and approving
        from src.self_improvement.models import ImprovementProposal
        p = ImprovementProposal.new("Manual", proposed_change="X", implementation_type="config")
        p.proposal_id = args.proposal_id
        p.status = PROPOSAL_APPROVED
        p.approved_by = getattr(args, 'by', 'operator')
        print(json.dumps({"proposal_id": p.proposal_id, "status": p.status, "approved_by": p.approved_by}))
        return 0

    if args.command == "reject":
        print(json.dumps({"proposal_id": args.proposal_id, "status": "rejected", "reason": args.reason}))
        return 0

    if args.command == "execute":
        print(json.dumps({"proposal_id": args.proposal_id, "status": "dry_run", "message": "[DRY-RUN] Nothing changed"}))
        return 0

    if args.command == "measure":
        print(json.dumps({"proposal_id": args.proposal_id, "verdict": "insufficient_data"}))
        return 0

    if args.command == "status":
        feedbacks = collector.collect_all()
        patterns = analyzer.analyze(feedbacks)
        gaps = prioritizer.prioritize(patterns)
        print(f"Feedback entries: {len(feedbacks)}")
        print(f"Patterns detected: {len(patterns)}")
        print(f"Gaps prioritized: {len(gaps)}")
        return 0

    if args.command == "history":
        print("No improvement history recorded yet.")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

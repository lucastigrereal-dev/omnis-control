"""Proposal Store — append-only JSONL persistence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.capability_forge_real.models import CapabilityProposal

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_PROPOSALS_LOG = BASE / "data" / "capability_proposals.jsonl"


class ProposalStore:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else DEFAULT_PROPOSALS_LOG

    def save(self, proposal: CapabilityProposal) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(proposal.to_dict(), ensure_ascii=False) + "\n")

    def list_all(self, limit: int = 50) -> list[CapabilityProposal]:
        if not self.path.exists():
            return []
        seen: dict[str, CapabilityProposal] = {}
        order: list[str] = []
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    p = CapabilityProposal.from_dict(d)
                    if p.proposal_id not in seen:
                        order.append(p.proposal_id)
                    seen[p.proposal_id] = p
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
        result = [seen[pid] for pid in reversed(order)]
        return result[:limit]

    def get(self, proposal_id: str) -> Optional[CapabilityProposal]:
        for p in self.list_all(limit=10000):
            if p.proposal_id == proposal_id:
                return p
        return None

    def update(self, proposal: CapabilityProposal) -> None:
        """Append updated version — get() returns latest."""
        self.save(proposal)

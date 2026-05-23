"""Approval Store — append-only JSONL persistence with in-place status updates."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.approval_center.models import ApprovalRequest

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_APPROVALS_LOG = BASE / "data" / "approval_requests.jsonl"


class ApprovalStore:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else DEFAULT_APPROVALS_LOG

    def save(self, req: ApprovalRequest) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(req.to_dict(), ensure_ascii=False) + "\n")

    def list_all(self, limit: int = 50, status: str | None = None) -> list[ApprovalRequest]:
        if not self.path.exists():
            return []
        reqs: dict[str, ApprovalRequest] = {}
        order: list[str] = []
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    req = ApprovalRequest.from_dict(d)
                    if req.request_id not in reqs:
                        order.append(req.request_id)
                    reqs[req.request_id] = req
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
        result = [reqs[rid] for rid in reversed(order)]
        if status is not None:
            result = [r for r in result if r.status == status]
        return result[:limit]

    def get(self, request_id: str) -> ApprovalRequest | None:
        for req in self.list_all(limit=10000):
            if req.request_id == request_id:
                return req
        return None

    def update_status(
        self,
        request_id: str,
        new_status: str,
        note: str = "",
    ) -> ApprovalRequest | None:
        req = self.get(request_id)
        if req is None:
            return None
        req.status = new_status
        req.resolution_note = note
        req.resolved_at = datetime.now(timezone.utc).isoformat()
        self.save(req)
        return req

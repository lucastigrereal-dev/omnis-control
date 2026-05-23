import json
from pathlib import Path
from typing import Optional

from src.approval_runtime.models import (
    ApprovalRequest,
    ApprovalDecision,
    ApprovalStatus,
    _now_iso,
)
from src.approval_runtime.errors import AlreadyDecidedError


class ApprovalStore:
    def __init__(self, store_path: Optional[str] = None, dry_run: bool = True):
        self.store_path = Path(store_path) if store_path else None
        self.dry_run = dry_run
        self._pending: dict[str, ApprovalRequest] = {}
        self._decisions: dict[str, ApprovalDecision] = {}

    def save_request(self, request: ApprovalRequest) -> None:
        self._pending[request.request_id] = request
        if self.store_path and not self.dry_run:
            self._flush()

    def pending(self) -> list[ApprovalRequest]:
        return list(self._pending.values())

    def get_pending(self, request_id: str) -> Optional[ApprovalRequest]:
        return self._pending.get(request_id)

    def approve(self, request_id: str, approved_by: str = "human") -> ApprovalDecision:
        if request_id in self._decisions:
            raise AlreadyDecidedError(request_id)
        request = self._pending.pop(request_id, None)
        decision = ApprovalDecision(
            request_id=request_id,
            status=ApprovalStatus.APPROVED,
            decided_at=_now_iso(),
            decided_by=approved_by,
            message=f"Approved by {approved_by}",
        )
        self._decisions[request_id] = decision
        if self.store_path and not self.dry_run:
            self._flush()
        return decision

    def reject(self, request_id: str, reason: str, rejected_by: str = "human") -> ApprovalDecision:
        if request_id in self._decisions:
            raise AlreadyDecidedError(request_id)
        self._pending.pop(request_id, None)
        decision = ApprovalDecision(
            request_id=request_id,
            status=ApprovalStatus.REJECTED,
            decided_at=_now_iso(),
            decided_by=rejected_by,
            message=reason,
        )
        self._decisions[request_id] = decision
        if self.store_path and not self.dry_run:
            self._flush()
        return decision

    def get_decision(self, request_id: str) -> Optional[ApprovalDecision]:
        return self._decisions.get(request_id)

    def _flush(self) -> None:
        if not self.store_path:
            return
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "pending": {k: v.to_dict() for k, v in self._pending.items()},
            "decisions": {k: v.to_dict() for k, v in self._decisions.items()},
        }
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        if not self.store_path or not self.store_path.exists():
            return
        with open(self.store_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.get("pending", {}).items():
            self._pending[k] = ApprovalRequest.from_dict(v)
        for k, v in data.get("decisions", {}).items():
            self._decisions[k] = ApprovalDecision(**{
                dk: dv for dk, dv in v.items()
                if dk in ApprovalDecision.__dataclass_fields__
            })
            if "status" in v:
                self._decisions[k].status = ApprovalStatus(v["status"])

"""Asset Assignment Center models — P1.9.

NUNCA armazena tokens, secrets ou valores reais de credenciais.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AssetAssignmentResult:
    queue_id: str
    asset_id: Optional[str] = None
    account_handle: str = ""
    caption_id: Optional[str] = None

    # Asset info
    asset_path: Optional[str] = None
    asset_type: str = ""  # reel, carousel, static, story, unknown
    asset_exists_on_disk: bool = False

    # Queue state
    previous_status: str = ""
    new_status: str = ""

    # Package readiness
    ready_for_package: bool = False

    # Diagnostics
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "queue_id": self.queue_id,
            "asset_id": self.asset_id,
            "account_handle": self.account_handle,
            "caption_id": self.caption_id,
            "asset_path": self.asset_path,
            "asset_type": self.asset_type,
            "asset_exists_on_disk": self.asset_exists_on_disk,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
            "ready_for_package": self.ready_for_package,
            "warnings": self.warnings,
            "blockers": self.blockers,
            "next_actions": self.next_actions,
        }

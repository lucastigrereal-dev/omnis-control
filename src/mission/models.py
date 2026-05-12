"""Mission Package models — MissionContext + MissionPackage dataclasses."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class MissionContext:
    """Contexto completo de uma missao — o 'prontuario'."""
    mission_id: str
    contract: dict = field(default_factory=dict)
    plan: dict = field(default_factory=dict)
    squad: dict | None = None
    created_at: str = field(default_factory=_now_iso)


@dataclass
class MissionPackage:
    """Pacote completo de missao — contexto + outputs + approvals + logs."""
    mission_id: str
    context: MissionContext = field(default_factory=lambda: MissionContext(mission_id=""))
    work_orders: list[dict] = field(default_factory=list)
    output_packages: list[dict] = field(default_factory=list)
    approval_requests: list[dict] = field(default_factory=list)
    logs: list[dict] = field(default_factory=list)
    manifest_registry_entries: list[dict] = field(default_factory=list)
    closeout: dict | None = None
    status: str = "draft"
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "context": {
                "mission_id": self.context.mission_id,
                "contract": self.context.contract,
                "plan": self.context.plan,
                "squad": self.context.squad,
                "created_at": self.context.created_at,
            },
            "work_orders": self.work_orders,
            "output_packages": self.output_packages,
            "approval_requests": self.approval_requests,
            "logs": self.logs,
            "manifest_registry_entries": self.manifest_registry_entries,
            "closeout": self.closeout,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def from_dict(cls, data: dict) -> "MissionPackage":
        ctx_data = data.get("context", {})
        context = MissionContext(
            mission_id=ctx_data.get("mission_id", data.get("mission_id", "")),
            contract=ctx_data.get("contract", {}),
            plan=ctx_data.get("plan", {}),
            squad=ctx_data.get("squad"),
            created_at=ctx_data.get("created_at", ""),
        )
        return cls(
            mission_id=data["mission_id"],
            context=context,
            work_orders=data.get("work_orders", []),
            output_packages=data.get("output_packages", []),
            approval_requests=data.get("approval_requests", []),
            logs=data.get("logs", []),
            manifest_registry_entries=data.get("manifest_registry_entries", []),
            closeout=data.get("closeout"),
            status=data.get("status", "draft"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    @classmethod
    def from_json(cls, path: Path) -> "MissionPackage":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

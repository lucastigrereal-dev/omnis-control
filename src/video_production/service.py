"""Video Production Plan service — JSONL persistence."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from src.video_production.models import (
    VideoProductionPlan,
    ProductionSlot,
    PlanStatus,
    SlotStatus,
)

PLANS_LOG = Path("data/video_production_plans.jsonl")

VALID_FORMATS = {"reel", "carousel", "static", "story"}


class PlanNotFoundError(ValueError):
    pass


class PlanValidationError(ValueError):
    pass


def _load_all(log_path: Path = PLANS_LOG) -> list[VideoProductionPlan]:
    if not log_path.exists():
        return []
    plans = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                plans.append(VideoProductionPlan.from_dict(json.loads(line)))
            except Exception:
                continue
    return plans


def _save_all(plans: list[VideoProductionPlan], log_path: Path = PLANS_LOG) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        for p in plans:
            f.write(json.dumps(p.to_dict(), ensure_ascii=False) + "\n")


def _build_slots(
    quantity: int,
    days_ahead: int,
    format: str,
) -> list[ProductionSlot]:
    today = datetime.now(timezone.utc).date()
    interval = max(1, days_ahead // quantity) if quantity > 0 else 1
    slots = []
    for i in range(quantity):
        slot_date = today + timedelta(days=i * interval)
        slots.append(ProductionSlot(
            slot_id=f"slot_{uuid.uuid4().hex[:6]}",
            date=slot_date.isoformat(),
            format=format,
        ))
    return slots


def create_plan(
    account_handle: str,
    format: str,
    quantity: int,
    days_ahead: int = 30,
    log_path: Path = None,
) -> VideoProductionPlan:
    if log_path is None:
        log_path = PLANS_LOG
    if format not in VALID_FORMATS:
        raise PlanValidationError(f"format deve ser um de: {', '.join(sorted(VALID_FORMATS))}")
    if quantity < 1 or quantity > 100:
        raise PlanValidationError("quantity deve estar entre 1 e 100")
    if days_ahead < 1 or days_ahead > 365:
        raise PlanValidationError("days_ahead deve estar entre 1 e 365")

    plan = VideoProductionPlan.new(
        account_handle=account_handle,
        format=format,
        quantity=quantity,
        days_ahead=days_ahead,
    )
    plan.slots = _build_slots(quantity, days_ahead, format)
    plan.status = PlanStatus.ACTIVE

    plans = _load_all(log_path)
    plans.append(plan)
    _save_all(plans, log_path)
    return plan


def list_plans(
    account_handle: Optional[str] = None,
    status: Optional[str] = None,
    log_path: Path = None,
) -> list[VideoProductionPlan]:
    if log_path is None:
        log_path = PLANS_LOG
    plans = _load_all(log_path)
    if account_handle:
        handle = account_handle.lstrip("@").lower()
        plans = [p for p in plans if p.account_handle == handle]
    if status:
        plans = [p for p in plans if p.status.value == status]
    return plans


def get_plan(plan_id: str, log_path: Path = None) -> VideoProductionPlan:
    if log_path is None:
        log_path = PLANS_LOG
    plans = _load_all(log_path)
    for p in plans:
        if p.plan_id == plan_id or p.plan_id.startswith(plan_id):
            return p
    raise PlanNotFoundError(f"Plan '{plan_id}' not found")


def mark_slot(
    plan_id: str,
    slot_id: str,
    status: str,
    asset_id: Optional[str] = None,
    log_path: Path = None,
) -> VideoProductionPlan:
    if log_path is None:
        log_path = PLANS_LOG
    if status not in SlotStatus._value2member_map_:
        raise PlanValidationError(f"slot status must be one of: {', '.join(SlotStatus._value2member_map_)}")

    plans = _load_all(log_path)
    target = None
    for p in plans:
        if p.plan_id == plan_id or p.plan_id.startswith(plan_id):
            target = p
            break
    if not target:
        raise PlanNotFoundError(f"Plan '{plan_id}' not found")

    updated = False
    for slot in target.slots:
        if slot.slot_id == slot_id or slot.slot_id.startswith(slot_id):
            slot.status = SlotStatus(status)
            if asset_id:
                slot.asset_id = asset_id
            updated = True
            break
    if not updated:
        raise PlanNotFoundError(f"Slot '{slot_id}' not found in plan '{plan_id}'")

    target.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _save_all(plans, log_path)
    return target

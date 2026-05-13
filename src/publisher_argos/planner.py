"""P8 Publisher ARGOS Planner — deterministic export engine (dry-run only, stdlib-only).

NEVER publishes, NEVER calls Meta/Instagram, NEVER calls real ARGOS.
All operations are pure modeling / dry-run.
Exports only as spec/string/plan.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.publisher_argos.models import (
    ArgosExportItem,
    ArgosExportPackage,
    ExportStatus,
    PublisherHandoff,
    PublishChannel,
    PublishQueuePlan,
    PublishReadinessCheck,
    PublishTarget,
    ReadinessVerdict,
)


# ── known pages (hardcoded for dry-run modeling) ──────────────────
KNOWN_PAGES: dict[str, dict] = {
    "lucastigrereal": {"profile": "@lucastigrereal", "followers": 690_000},
    "oinatalrn": {"profile": "@oinatalrn", "followers": 630_000},
    "agenteviajabrasil": {"profile": "@agenteviajabrasil", "followers": 452_000},
    "afamiliatigrereal": {"profile": "@afamiliatigrereal", "followers": 320_000},
    "oquecomernatalrn": {"profile": "@oquecomernatalrn", "followers": 249_000},
    "natalaivoueu": {"profile": "@natalaivoueu", "followers": 240_000},
}

# ── readiness checks ──────────────────────────────────────────────

REQUIRED_CHECKS = [
    "has_caption",
    "has_target",
    "has_media_url",
    "caption_min_length",
    "handle_is_known",
]


@dataclass
class PublisherArgosPlanner:
    """Deterministic publisher-to-ARGOS planner — dry-run modeling only.

    NEVER publishes. NEVER calls external APIs.
    All exports are spec/string/plan only.
    approval_required is ALWAYS True for any future real publish.
    """

    dry_run: bool = True
    approval_required: bool = True

    # ── build ─────────────────────────────────────────────────

    def build_export_item(
        self,
        caption: str,
        handle: str = "lucastigrereal",
        channel: PublishChannel = PublishChannel.INSTAGRAM_FEED,
        media_url: str = "",
        media_type: str = "IMAGE",
        tags: Optional[list[str]] = None,
        schedule_iso: Optional[str] = None,
        notes: str = "",
    ) -> ArgosExportItem:
        """Build a single ArgosExportItem from a caption and metadata."""
        page = KNOWN_PAGES.get(handle, {"profile": handle, "followers": 0})
        target = PublishTarget(
            handle=handle,
            profile=page["profile"],
            channel=channel,
            followers=page["followers"],
            label=f"{page['profile']} / {channel.value}",
        )
        return ArgosExportItem(
            target=target,
            caption=caption,
            media_url=media_url,
            media_type=media_type,
            tags=tags or [],
            schedule_iso=schedule_iso,
            status=ExportStatus.DRAFT,
            approval_required=self.approval_required,
            notes=notes,
        )

    # ── validate ───────────────────────────────────────────────

    def validate_publish_readiness(self, item: ArgosExportItem) -> PublishReadinessCheck:
        """Run all readiness checks on a single ArgosExportItem. Returns check result."""
        checks: list[dict] = []
        passed = 0
        failed = 0
        blocked = 0

        # 1. has_caption
        if item.caption.strip():
            checks.append({"check": "has_caption", "ok": True})
            passed += 1
        else:
            checks.append({"check": "has_caption", "ok": False, "detail": "empty caption"})
            failed += 1

        # 2. has_target
        if item.target.handle:
            checks.append({"check": "has_target", "ok": True})
            passed += 1
        else:
            checks.append({"check": "has_target", "ok": False, "detail": "no target handle"})
            failed += 1

        # 3. has_media_url
        if item.media_url.strip():
            checks.append({"check": "has_media_url", "ok": True})
            passed += 1
        else:
            checks.append({"check": "has_media_url", "ok": False, "detail": "no media_url (optional for dry-run)"})
            blocked += 1

        # 4. caption_min_length
        if len(item.caption.strip()) >= 10:
            checks.append({"check": "caption_min_length", "ok": True})
            passed += 1
        else:
            checks.append({"check": "caption_min_length", "ok": False, "detail": f"caption too short ({len(item.caption.strip())} chars, min 10)"})
            failed += 1

        # 5. handle_is_known
        if item.target.handle in KNOWN_PAGES:
            checks.append({"check": "handle_is_known", "ok": True})
            passed += 1
        else:
            checks.append({"check": "handle_is_known", "ok": False, "detail": f"unknown handle: {item.target.handle}"})
            blocked += 1

        # verdict
        if failed > 0:
            verdict = ReadinessVerdict.FAIL
            reason = f"{failed} check(s) failed, {blocked} blocked"
        elif blocked > 0:
            verdict = ReadinessVerdict.PENDING_APPROVAL
            reason = f"{blocked} check(s) blocked — needs approval"
        else:
            verdict = ReadinessVerdict.PASS
            reason = "All checks passed"

        return PublishReadinessCheck(
            item_id=item.id,
            verdict=verdict,
            checks=checks,
            passed=passed,
            failed=failed,
            blocked=blocked,
            reason=reason,
        )

    # ── queue ──────────────────────────────────────────────────

    def build_queue_plan(
        self,
        items: Optional[list[ArgosExportItem]] = None,
        label: str = "",
    ) -> PublishQueuePlan:
        """Build a PublishQueuePlan from a list of ArgosExportItems."""
        plan = PublishQueuePlan(
            label=label,
            dry_run=self.dry_run,
        )
        for item in (items or []):
            plan.add(item)
        return plan

    # ── package ────────────────────────────────────────────────

    def build_argos_export_package(
        self,
        queue_plan: PublishQueuePlan,
        label: str = "",
    ) -> ArgosExportPackage:
        """Build an ArgosExportPackage with readiness checks for every item."""
        readiness_checks: list[PublishReadinessCheck] = []
        for item in queue_plan.items:
            chk = self.validate_publish_readiness(item)
            if chk.verdict == ReadinessVerdict.PASS:
                item.mark_ready()
            elif chk.verdict == ReadinessVerdict.FAIL:
                item.mark_blocked(chk.reason)
            # PENDING_APPROVAL keeps DRAFT
            readiness_checks.append(chk)

        return ArgosExportPackage(
            queue_plan=queue_plan,
            readiness_checks=readiness_checks,
            label=label,
            dry_run=self.dry_run,
            approval_required=self.approval_required,
        )

    # ── handoff ────────────────────────────────────────────────

    def build_publisher_handoff(
        self,
        package: ArgosExportPackage,
        notes: str = "",
    ) -> PublisherHandoff:
        """Build a PublisherHandoff record (dry-run only)."""
        return PublisherHandoff(
            package=package,
            approval_required=self.approval_required,
            approved_by=None,  # never auto-approve
            dry_run=self.dry_run,
            notes=notes or "Dry-run handoff — approval required for real publish",
        )

    # ── export ─────────────────────────────────────────────────

    def export_argos_json(self, handoff: PublisherHandoff, indent: int = 2) -> str:
        """Export a PublisherHandoff as a JSON string (never writes to disk).

        To write to a file, use the returned string with an explicit path
        in a test helper — never automatically.
        """
        return json.dumps(handoff.to_dict(), indent=indent, ensure_ascii=False)

    # ── helpers ────────────────────────────────────────────────

    @staticmethod
    def get_known_handles() -> list[str]:
        return sorted(KNOWN_PAGES.keys())

    @staticmethod
    def get_page_info(handle: str) -> Optional[dict]:
        return KNOWN_PAGES.get(handle)

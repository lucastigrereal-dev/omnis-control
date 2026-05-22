"""Audit __init__."""

import uuid
from datetime import datetime, timezone

from .log import AuditAction, AuditEntry, AuditLog, get_audit_log

# Backward-compatible alias — AuditEntryType was renamed to AuditAction
AuditEntryType = AuditAction


class AuditTrail:
    """Backward-compatible wrapper around AuditLog.

    Adapts the old AuditTrail API (action/result/source/details)
    to the current AuditLog API (actor/action/resource/outcome/detail).
    """

    def __init__(self, base_dir: str | None = None):
        self._log = AuditLog(base_dir=base_dir)
        self._seq = 0

    def record(
        self,
        action: str,
        result: str,
        source: str,
        details: dict | None = None,
        actor: str = "audit_trail",
    ) -> AuditEntry:
        try:
            act = AuditAction(action)
        except ValueError:
            act = AuditAction.EXECUTION
        entry = self._log.record(
            actor=actor,
            action=act,
            resource=source,
            outcome=result,
            detail=details or {},
        )
        self._seq += 1
        return entry


__all__ = [
    "AuditLog",
    "AuditEntry",
    "AuditAction",
    "AuditEntryType",
    "AuditTrail",
    "get_audit_log",
]

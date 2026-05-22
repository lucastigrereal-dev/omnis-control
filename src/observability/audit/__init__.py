"""Audit __init__ — unified AuditTrail with full backward compatibility."""
from __future__ import annotations

from .log import AuditAction, AuditEntry, AuditLog, get_audit_log

AuditEntryType = AuditAction


class AuditEntryWrapper:
    """Wraps AuditEntry to expose both AuditAction enum AND original string fields."""

    def __init__(self, entry: AuditEntry, original_action: str, original_result: str, original_source: str):
        self._entry = entry
        self._action_str = original_action
        self._result_str = original_result
        self._source_str = original_source

    @property
    def action(self) -> str:
        return self._action_str

    @property
    def result(self) -> str:
        return self._result_str

    @property
    def source(self) -> str:
        return self._source_str

    @property
    def detail(self) -> dict:
        return self._entry.detail

    @property
    def entry_type(self) -> AuditAction:
        return self._entry.action

    def __getattr__(self, name):
        return getattr(self._entry, name)


class AuditTrail:
    """AuditTrail with full compatibility: query, entry_count, last_entry, record with detail/entry_type."""

    def __init__(self, base_dir: str | None = None):
        self._entries: list[AuditEntryWrapper] = []

    def record(
        self,
        action: str = "",
        result: str = "",
        source: str = "",
        entry_type: AuditEntryType | None = None,
        detail: dict | None = None,
    ) -> AuditEntryWrapper:
        from uuid import uuid4
        from datetime import datetime, timezone

        act = entry_type or AuditAction.EXECUTION
        entry = AuditEntry(
            entry_id=str(uuid4()),
            actor="audit_trail",
            action=act,
            resource=source,
            outcome=result,
            detail=detail or {},
            sequence=len(self._entries),
        )
        wrapper = AuditEntryWrapper(entry, action, result, source)
        self._entries.append(wrapper)
        return wrapper

    def query(
        self,
        source: str = "",
        entry_type: str = "",
    ) -> list[AuditEntryWrapper]:
        results = self._entries
        if source:
            results = [e for e in results if e.source == source]
        if entry_type:
            results = [e for e in results if e.entry_type.value == entry_type.lower()]
        return results

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    @property
    def last_entry(self) -> AuditEntryWrapper | None:
        return self._entries[-1] if self._entries else None


__all__ = [
    "AuditLog",
    "AuditEntry",
    "AuditAction",
    "AuditEntryType",
    "AuditTrail",
    "get_audit_log",
]
